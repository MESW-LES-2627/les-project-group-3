import asyncio
import time
from collections.abc import Callable
from uuid import UUID

import httpx
import pytest
from adoption_factory import until_blocked
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker
from token_issuer import USER_ID, TokenIssuer

from patas_backend.auth.keys import JwksKeyProvider, RemoteJwksKeyProvider
from patas_backend.models.user import UserRepository

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
        "username": "ana",
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
                "INSERT INTO patas.users"
                " (id, name, email, username, is_platform_admin)"
                " VALUES (:id, 'Ana', 'ana@example.com', 'ana', true)"
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
        "username": "ana",
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


OTHER = {"sub": OTHER_ID, "name": "Bob", "email": "bob@example.com"}


async def _stored(engine: AsyncEngine, user_id: str) -> tuple[str, str]:
    """The stored (name, username) of one user."""
    async with engine.connect() as conn:
        row = (
            await conn.execute(
                text("SELECT name, username FROM patas.users WHERE id = :id"),
                {"id": UUID(user_id)},
            )
        ).one()
    return row.name, row.username


async def test_patch_me_changes_the_username_as_typed(
    client: httpx.AsyncClient, issuer: TokenIssuer, engine: AsyncEngine
) -> None:
    response = await client.patch(
        "/me", json={"username": " Ana.Demo "}, headers=_bearer(issuer.token())
    )

    assert response.status_code == 200
    assert response.json()["username"] == "Ana.Demo"
    assert await _stored(engine, USER_ID) == ("Ana", "Ana.Demo")


async def test_patch_me_changes_name_and_username_together(
    client: httpx.AsyncClient, issuer: TokenIssuer
) -> None:
    response = await client.patch(
        "/me",
        json={"name": "Ana Silva", "username": "ana_silva"},
        headers=_bearer(issuer.token()),
    )

    assert response.status_code == 200
    assert (response.json()["name"], response.json()["username"]) == (
        "Ana Silva",
        "ana_silva",
    )


@pytest.mark.parametrize("username", ["an", "ana demo", ".ana", "a" * 31])
async def test_patch_me_refuses_a_malformed_username_and_keeps_the_old(
    client: httpx.AsyncClient, issuer: TokenIssuer, engine: AsyncEngine, username: str
) -> None:
    response = await client.patch(
        "/me",
        json={"name": "Ana Silva", "username": username},
        headers=_bearer(issuer.token()),
    )

    assert response.status_code == 422
    assert await _stored(engine, USER_ID) == ("Ana", "ana")


async def test_patch_me_needs_something_to_change(
    client: httpx.AsyncClient, issuer: TokenIssuer
) -> None:
    response = await client.patch("/me", json={}, headers=_bearer(issuer.token()))

    assert response.status_code == 422


async def test_patch_me_refuses_a_taken_username_and_changes_nothing(
    client: httpx.AsyncClient, issuer: TokenIssuer, engine: AsyncEngine
) -> None:
    await client.get("/me", headers=_bearer(issuer.token(**OTHER)))

    response = await client.patch(
        "/me",
        json={"name": "Ana Silva", "username": "BOB"},
        headers=_bearer(issuer.token()),
    )

    assert response.status_code == 409
    assert response.json()["detail"] == {
        "code": "username_taken",
        "message": "That username is already taken",
    }
    assert await _stored(engine, USER_ID) == ("Ana", "ana")


async def test_a_name_change_that_meets_a_username_change_keeps_both(
    client: httpx.AsyncClient, issuer: TokenIssuer, engine: AsyncEngine
) -> None:
    # The name change waits for the row instead of writing the old username back.
    await client.get("/me", headers=_bearer(issuer.token()))

    async with async_sessionmaker(engine).begin() as session:
        repo = UserRepository(session)
        being_changed = await repo.get_for_update(UUID(USER_ID))
        name_change = asyncio.create_task(
            client.patch(
                "/me", json={"name": "Ana Silva"}, headers=_bearer(issuer.token())
            )
        )
        await until_blocked(engine, 1)
        being_changed.change_username("ana.new")
        await repo.update(being_changed)

    assert (await name_change).status_code == 200
    assert await _stored(engine, USER_ID) == ("Ana Silva", "ana.new")


async def test_username_availability_is_public_and_ignores_case(
    client: httpx.AsyncClient, issuer: TokenIssuer
) -> None:
    await client.get("/me", headers=_bearer(issuer.token()))

    taken = await client.get("/usernames/ANA")
    free = await client.get("/usernames/%20bob%20")

    assert taken.status_code == 200
    assert taken.json() == {"username": "ANA", "available": False}
    assert free.json() == {"username": "bob", "available": True}


async def test_username_availability_refuses_a_malformed_username(
    client: httpx.AsyncClient,
) -> None:
    response = await client.get("/usernames/a b")

    assert response.status_code == 422
