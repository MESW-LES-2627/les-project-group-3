import time
from collections.abc import Callable
from uuid import UUID

import httpx
import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine
from token_issuer import USER_ID, TokenIssuer

from patas_backend.auth.keys import JwksKeyProvider, RemoteJwksKeyProvider

OTHER_ID = "5c6d7e8f-9a0b-4c1d-8e2f-3a4b5c6d7e8f"


def _bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def _rows(engine: AsyncEngine) -> list[tuple[UUID, str, str, bool]]:
    async with engine.connect() as conn:
        result = await conn.execute(
            text("SELECT id, name, email, is_platform_admin FROM patas.users")
        )
        return [tuple(row) for row in result]


async def test_first_authenticated_call_creates_the_user(
    client: httpx.AsyncClient, issuer: TokenIssuer, engine: AsyncEngine
) -> None:
    response = await client.get("/me", headers=_bearer(issuer.token()))

    assert response.status_code == 200
    assert response.json() == {
        "id": USER_ID,
        "name": "Ana",
        "email": "ana@example.com",
        "is_platform_admin": False,
    }
    assert await _rows(engine) == [(UUID(USER_ID), "Ana", "ana@example.com", False)]


async def test_second_call_does_not_duplicate_the_user(
    client: httpx.AsyncClient, issuer: TokenIssuer, engine: AsyncEngine
) -> None:
    await client.get("/me", headers=_bearer(issuer.token()))
    response = await client.get("/me", headers=_bearer(issuer.token()))

    assert response.status_code == 200
    assert len(await _rows(engine)) == 1


async def test_request_without_a_token_is_rejected(
    client: httpx.AsyncClient, engine: AsyncEngine
) -> None:
    response = await client.get("/me")

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"
    assert await _rows(engine) == []


@pytest.mark.parametrize(
    "authorization", ["Bearer", "Bearer ", "Basic abc123", "Token xyz"]
)
async def test_malformed_authorization_header_is_rejected(
    client: httpx.AsyncClient, engine: AsyncEngine, authorization: str
) -> None:
    response = await client.get("/me", headers={"Authorization": authorization})

    assert response.status_code == 401
    assert await _rows(engine) == []


@pytest.mark.parametrize(
    "make_token",
    [
        pytest.param(lambda i, o: i.token(exp=int(time.time()) - 10), id="expired"),
        pytest.param(lambda i, o: o.token(), id="wrong-signature"),
        pytest.param(lambda i, o: TokenIssuer(kid="gone").token(), id="unknown-kid"),
        pytest.param(lambda i, o: "not.a.jwt", id="garbage"),
    ],
)
async def test_invalid_token_is_rejected_and_nothing_is_stored(
    client: httpx.AsyncClient,
    issuer: TokenIssuer,
    other_issuer: TokenIssuer,
    engine: AsyncEngine,
    make_token: Callable[[TokenIssuer, TokenIssuer], str],
) -> None:
    response = await client.get(
        "/me", headers=_bearer(make_token(issuer, other_issuer))
    )

    assert response.status_code == 401
    assert await _rows(engine) == []


async def test_email_owned_by_another_user_is_rejected(
    client: httpx.AsyncClient, issuer: TokenIssuer, engine: AsyncEngine
) -> None:
    await client.get("/me", headers=_bearer(issuer.token()))

    response = await client.get(
        "/me", headers=_bearer(issuer.token(sub=OTHER_ID, email="ANA@Example.com"))
    )

    assert response.status_code == 401
    assert await _rows(engine) == [(UUID(USER_ID), "Ana", "ana@example.com", False)]


async def test_unreachable_jwks_is_a_503_and_nothing_is_stored(
    make_client: Callable[[JwksKeyProvider], httpx.AsyncClient],
    issuer: TokenIssuer,
    engine: AsyncEngine,
) -> None:
    client = make_client(RemoteJwksKeyProvider("http://127.0.0.1:1/jwks"))

    response = await client.get("/me", headers=_bearer(issuer.token()))

    assert response.status_code == 503
    assert await _rows(engine) == []


async def test_token_claims_cannot_grant_admin(
    client: httpx.AsyncClient, issuer: TokenIssuer
) -> None:
    token = issuer.token(is_platform_admin=True, role="admin")

    response = await client.get("/me", headers=_bearer(token))

    assert response.json()["is_platform_admin"] is False


async def test_admin_flag_comes_from_the_database(
    client: httpx.AsyncClient, issuer: TokenIssuer, engine: AsyncEngine
) -> None:
    async with engine.begin() as conn:
        await conn.execute(
            text(
                "INSERT INTO patas.users (id, name, email, is_platform_admin) "
                "VALUES (:id, 'Ana', 'ana@example.com', true)"
            ),
            {"id": UUID(USER_ID)},
        )

    response = await client.get("/me", headers=_bearer(issuer.token()))

    assert response.json()["is_platform_admin"] is True


async def test_patch_me_updates_name(
    client: httpx.AsyncClient, issuer: TokenIssuer, engine: AsyncEngine
) -> None:
    # First ensure the user exists via GET /me
    await client.get("/me", headers=_bearer(issuer.token()))

    response = await client.patch(
        "/me",
        json={"name": "  Ana Silva  "},
        headers=_bearer(issuer.token()),
    )

    assert response.status_code == 200
    assert response.json() == {
        "id": USER_ID,
        "name": "Ana Silva",
        "email": "ana@example.com",
        "is_platform_admin": False,
    }
    assert await _rows(engine) == [
        (UUID(USER_ID), "Ana Silva", "ana@example.com", False)
    ]


@pytest.mark.parametrize("name", ["", "   "])
async def test_patch_me_rejects_blank_name_and_leaves_name_unchanged(
    client: httpx.AsyncClient, issuer: TokenIssuer, engine: AsyncEngine, name: str
) -> None:
    await client.get("/me", headers=_bearer(issuer.token()))

    response = await client.patch(
        "/me",
        json={"name": name},
        headers=_bearer(issuer.token()),
    )

    assert response.status_code == 422
    assert await _rows(engine) == [(UUID(USER_ID), "Ana", "ana@example.com", False)]
