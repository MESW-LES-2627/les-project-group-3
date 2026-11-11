"""AT-08 (#32): The Matchmaker profile is private."""

import httpx
from matchmaker_endpoint import (
    BRUNO,
    BRUNOS_ANSWERS,
    CARLA,
    CARLAS_ANSWERS,
    PROFILE,
    _as,
    _stored_profiles,
)
from sqlalchemy.ext.asyncio import AsyncEngine
from token_issuer import TokenIssuer


async def test_at_08_each_user_sees_only_their_own_profile(
    client: httpx.AsyncClient, issuer: TokenIssuer
) -> None:
    await client.put(PROFILE, json=CARLAS_ANSWERS, headers=_as(issuer, CARLA))
    await client.put(PROFILE, json=BRUNOS_ANSWERS, headers=_as(issuer, BRUNO))

    brunos = await client.get(PROFILE, headers=_as(issuer, BRUNO))
    carlas = await client.get(PROFILE, headers=_as(issuer, CARLA))

    assert brunos.json() == BRUNOS_ANSWERS
    assert carlas.json() == CARLAS_ANSWERS


async def test_at_08_a_visitor_cannot_save_and_nothing_is_stored(
    client: httpx.AsyncClient, engine: AsyncEngine
) -> None:
    response = await client.put(PROFILE, json=CARLAS_ANSWERS)

    assert response.status_code == 401
    assert await _stored_profiles(engine) == 0
