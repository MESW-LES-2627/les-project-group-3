"""AT-22 (#76): usernames are unique, ignoring case.

Registering is Better Auth's sign-up followed by the register page asking whether
the username is free and setting it on the first backend call (ADR 0024), so
"registers with" is those two calls here.
"""

import httpx
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine
from token_issuer import TokenIssuer

ANA = {
    "sub": "11111111-1111-1111-1111-111111111111",
    "name": "Ana",
    "email": "ana@example.com",
}
DAN = {
    "sub": "44444444-4444-4444-4444-444444444444",
    "name": "Dan",
    "email": "dan@example.com",
}


def _bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def _register(
    client: httpx.AsyncClient,
    issuer: TokenIssuer,
    person: dict[str, str],
    username: str,
) -> httpx.Response:
    """The register page: ask first, then claim the username if it was free."""
    check = await client.get(f"/usernames/{username}")
    assert check.status_code == 200
    if not check.json()["available"]:
        return check
    return await client.patch(
        "/me", json={"username": username}, headers=_bearer(issuer.token(**person))
    )


async def _publish(
    client: httpx.AsyncClient, issuer: TokenIssuer, person: dict[str, str]
) -> str:
    response = await client.post(
        "/animals",
        json={"name": "Rex", "species": "dog"},
        headers=_bearer(issuer.token(**person)),
    )
    assert response.status_code == 201
    return response.json()["id"]


async def test_at_22_a_username_taken_in_another_case_is_refused(
    client: httpx.AsyncClient, issuer: TokenIssuer
) -> None:
    # Given Ana's username is "Ana"
    assert (await _register(client, issuer, ANA, "Ana")).status_code == 200

    # When Dan registers with "ana", then he is refused
    response = await _register(client, issuer, DAN, "ana")

    assert response.json() == {"username": "ana", "available": False}
    # and setting it anyway, as a page racing Ana would, is refused too.
    claim = await client.patch(
        "/me", json={"username": "ana"}, headers=_bearer(issuer.token(**DAN))
    )
    assert claim.status_code == 409
    assert claim.json()["detail"]["code"] == "username_taken"


async def test_at_22_a_free_username_shows_on_the_profile_and_as_publisher(
    client: httpx.AsyncClient, issuer: TokenIssuer
) -> None:
    # When Dan registers with a free username
    response = await _register(client, issuer, DAN, "Dan_Silva")
    assert response.status_code == 200
    rex = await _publish(client, issuer, DAN)

    # Then it shows on his profile and as the publisher of his animals.
    me = await client.get("/me", headers=_bearer(issuer.token(**DAN)))
    assert me.json()["username"] == "Dan_Silva"
    assert (await client.get(f"/animals/{rex}")).json()["owner_username"] == (
        "Dan_Silva"
    )
    mine = await client.get("/me/animals", headers=_bearer(issuer.token(**DAN)))
    assert [a["owner_username"] for a in mine.json()] == ["Dan_Silva"]


async def test_at_22_changing_to_a_free_username_shows_on_his_animals(
    client: httpx.AsyncClient, issuer: TokenIssuer
) -> None:
    await _register(client, issuer, DAN, "dan")
    rex = await _publish(client, issuer, DAN)

    # When he changes it to another free username
    response = await client.patch(
        "/me", json={"username": "dan.s"}, headers=_bearer(issuer.token(**DAN))
    )

    # Then his animals show the new one.
    assert response.status_code == 200
    assert (await client.get(f"/animals/{rex}")).json()["owner_username"] == "dan.s"
    catalog = (await client.get("/animals")).json()
    assert [a["owner_username"] for a in catalog] == ["dan.s"]


async def test_at_22_changing_to_a_taken_username_is_refused_and_keeps_the_old_one(
    client: httpx.AsyncClient, issuer: TokenIssuer
) -> None:
    await _register(client, issuer, ANA, "Ana")
    await _register(client, issuer, DAN, "dan")
    rex = await _publish(client, issuer, DAN)

    # When he changes it to a taken one
    response = await client.patch(
        "/me", json={"username": "ANA"}, headers=_bearer(issuer.token(**DAN))
    )

    # Then he is refused and keeps the current one.
    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "username_taken"
    me = await client.get("/me", headers=_bearer(issuer.token(**DAN)))
    assert me.json()["username"] == "dan"
    assert (await client.get(f"/animals/{rex}")).json()["owner_username"] == "dan"


async def test_at_22_a_user_from_before_usernames_can_sign_in_and_has_one(
    client: httpx.AsyncClient, issuer: TokenIssuer, engine: AsyncEngine
) -> None:
    # Users already in patas.users get one from migration 0008 (see
    # test_users_migration.py). This is the other case: an account created in
    # Better Auth before the change, whose first backend call comes now.
    before = {**DAN, "name": "Dan Old Account"}

    response = await client.get("/me", headers=_bearer(issuer.token(**before)))

    assert response.status_code == 200
    assert response.json()["username"] == "dan_old_account"
    async with engine.connect() as conn:
        stored = await conn.scalar(text("SELECT username FROM patas.users"))
    assert stored == "dan_old_account"
