"""AT-10 (#40): The animal page shows my fit and why."""

from uuid import UUID

import httpx
from compatibility_endpoint import (
    CARLA,
    MILO,
    _as,
    _publish,
    _save_home,
    _url,
)
from sqlalchemy.ext.asyncio import AsyncEngine
from token_issuer import TokenIssuer

from patas_backend.models.animal import (
    AnimalCompatibility,
)
from patas_backend.models.compatibility import rules
from patas_backend.models.user import User


async def test_at_10_the_animal_page_gets_a_score_and_reasons_by_kind(
    client: httpx.AsyncClient, issuer: TokenIssuer, engine: AsyncEngine
) -> None:
    animal = await _publish(engine, **MILO)
    await _save_home(client, issuer, CARLA)

    response = await client.get(_url(animal), headers=_as(issuer, CARLA))

    # Fits 1.0, 0.5, 1.0, 0.5: a base of 0.75, so 75 in the flexible match.
    assert response.status_code == 200
    assert response.json() == {
        "mode": "loose",
        "score": 75,
        "is_compatible": True,
        "reasons": [
            {"text": rules.ACTIVITY_WORDING.fits, "kind": "strength"},
            {"text": rules.TIME_ALONE_WORDING.partly, "kind": "concern"},
            {"text": rules.EXPERIENCE_WORDING.fits, "kind": "strength"},
            {"text": rules.SPACE_WORDING.partly, "kind": "concern"},
        ],
    }


async def test_at_10_an_animal_not_safe_with_her_children_is_marked_not_suitable(
    client: httpx.AsyncClient, issuer: TokenIssuer, engine: AsyncEngine
) -> None:
    animal = await _publish(
        engine, behaves_well_with_children=AnimalCompatibility.NO, **MILO
    )
    await _save_home(client, issuer, CARLA, has_children=True)

    response = await client.get(_url(animal), headers=_as(issuer, CARLA))

    assert response.status_code == 200
    assert response.json()["is_compatible"] is False
    assert response.json()["score"] == 0
    assert response.json()["reasons"] == [
        {"text": rules.household_wording("children").misfit, "kind": "concern"}
    ]


async def test_at_10_updating_the_profile_changes_the_score(
    client: httpx.AsyncClient, issuer: TokenIssuer, engine: AsyncEngine
) -> None:
    animal = await _publish(engine, **MILO)
    await _save_home(client, issuer, CARLA)
    before = await client.get(_url(animal), headers=_as(issuer, CARLA))

    # Away only a few hours now: time alone fits in full, so 3.5 / 4 = 87.5.
    await _save_home(client, issuer, CARLA, time_away="few_hours")
    after = await client.get(_url(animal), headers=_as(issuer, CARLA))

    assert before.json()["score"] == 75
    assert after.json()["score"] == 88


async def test_at_10_her_own_animal_is_refused(
    client: httpx.AsyncClient, issuer: TokenIssuer, engine: AsyncEngine
) -> None:
    carla = User.provision(
        id=UUID(CARLA["sub"]), name=CARLA["name"], email=CARLA["email"]
    )
    animal = await _publish(engine, owner=carla, **MILO)
    await _save_home(client, issuer, CARLA)

    response = await client.get(_url(animal), headers=_as(issuer, CARLA))

    assert response.status_code == 422
    assert response.json() == {"detail": "This is your own animal"}


async def test_at_10_without_a_profile_the_caller_is_asked_to_create_one(
    client: httpx.AsyncClient, issuer: TokenIssuer, engine: AsyncEngine
) -> None:
    animal = await _publish(engine, **MILO)

    response = await client.get(_url(animal), headers=_as(issuer, CARLA))

    assert response.status_code == 409
    assert response.json() == {"detail": "No Matchmaker profile yet"}


async def test_at_10_a_visitor_without_a_token_gets_401(
    client: httpx.AsyncClient, engine: AsyncEngine
) -> None:
    animal = await _publish(engine, **MILO)

    response = await client.get(_url(animal))

    assert response.status_code == 401
