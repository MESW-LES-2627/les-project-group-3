"""AT-07 (#31): Save and update my Matchmaker profile."""

import httpx
from matchmaker_endpoint import (
    CARLA,
    CARLAS_ANSWERS,
    PROFILE,
    _as,
    _stored_profiles,
)
from sqlalchemy.ext.asyncio import AsyncEngine
from token_issuer import TokenIssuer


async def test_at_07_saved_answers_show_up_on_the_next_visit(
    client: httpx.AsyncClient, issuer: TokenIssuer
) -> None:
    saved = await client.put(PROFILE, json=CARLAS_ANSWERS, headers=_as(issuer, CARLA))

    assert saved.status_code == 200
    assert saved.json() == CARLAS_ANSWERS
    visit = await client.get(PROFILE, headers=_as(issuer, CARLA))
    assert visit.status_code == 200
    assert visit.json() == CARLAS_ANSWERS


async def test_at_07_changing_an_answer_updates_the_profile_and_keeps_only_one(
    client: httpx.AsyncClient, issuer: TokenIssuer, engine: AsyncEngine
) -> None:
    await client.put(PROFILE, json=CARLAS_ANSWERS, headers=_as(issuer, CARLA))
    changed = {**CARLAS_ANSWERS, "has_dogs": True}

    response = await client.put(PROFILE, json=changed, headers=_as(issuer, CARLA))

    assert response.status_code == 200
    visit = await client.get(PROFILE, headers=_as(issuer, CARLA))
    assert visit.json() == changed
    assert await _stored_profiles(engine) == 1


async def test_at_07_an_invalid_answer_is_rejected_and_the_profile_is_unchanged(
    client: httpx.AsyncClient, issuer: TokenIssuer
) -> None:
    await client.put(PROFILE, json=CARLAS_ANSWERS, headers=_as(issuer, CARLA))

    response = await client.put(
        PROFILE,
        json={**CARLAS_ANSWERS, "housing": "castle"},
        headers=_as(issuer, CARLA),
    )

    assert response.status_code == 422
    visit = await client.get(PROFILE, headers=_as(issuer, CARLA))
    assert visit.json() == CARLAS_ANSWERS
