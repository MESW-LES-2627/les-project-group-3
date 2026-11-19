"""AT-14 (#68): Browse the best-fitting animals first."""

from uuid import UUID

import httpx
from compatibility_endpoint import CARLA, _as, _save_home
from matchmaker_swipe_endpoint import _publish
from sqlalchemy.ext.asyncio import AsyncEngine
from token_issuer import TokenIssuer

from patas_backend.models.animal import AnimalCompatibility
from patas_backend.models.matching import EnergyLevel
from patas_backend.models.user import User

CARLA_USER = User.provision(
    id=UUID(CARLA["sub"]), name=CARLA["name"], email=CARLA["email"]
)
PROFILE = "/me/matchmaker-profile"
FEED = "/me/matchmaker/swipes/feed"


async def test_at_14_feed_ranks_fit_first_and_places_unsafe_animals_after(
    client: httpx.AsyncClient, issuer: TokenIssuer, engine: AsyncEngine
) -> None:
    await _save_home(client, issuer, CARLA, has_children=True)
    best = await _publish(
        engine,
        "Best fit",
        activity_level=EnergyLevel.MODERATE,
        tolerance_for_time_alone=EnergyLevel.MODERATE,
        behaves_well_with_children=AnimalCompatibility.YES,
    )
    other_fit = await _publish(
        engine,
        "Another fit",
        activity_level=EnergyLevel.HIGH,
        tolerance_for_time_alone=EnergyLevel.LOW,
        behaves_well_with_children=AnimalCompatibility.YES,
    )
    unsuitable = await _publish(
        engine,
        "Not safe with children",
        behaves_well_with_children=AnimalCompatibility.NO,
    )
    own = await _publish(engine, "Carla's animal", owner=CARLA_USER)
    token = _as(issuer, CARLA)

    scores = {}
    for animal in (best, other_fit, unsuitable):
        response = await client.get(
            f"/animals/{animal.id}/compatibility", headers=token
        )
        assert response.status_code == 200
        scores[animal.id] = response.json()

    response = await client.get(FEED, headers=token)

    assert response.status_code == 200
    items = response.json()
    expected = sorted(
        (best, other_fit, unsuitable),
        key=lambda animal: (
            not scores[animal.id]["is_compatible"],
            -scores[animal.id]["score"],
            str(animal.id),
        ),
    )
    assert [item["id"] for item in items] == [str(animal.id) for animal in expected]
    assert items[-1]["fit"]["is_compatible"] is False
    assert items[-1]["fit"]["reasons"]
    assert str(own.id) not in [item["id"] for item in items]


async def test_at_14_next_batch_continues_through_all_animals_in_the_sample(
    client: httpx.AsyncClient, issuer: TokenIssuer, engine: AsyncEngine
) -> None:
    await _save_home(client, issuer, CARLA)
    animals = [await _publish(engine, f"Animal {index}") for index in range(12)]
    token = _as(issuer, CARLA)

    first = await client.get(FEED, headers=token)
    assert first.status_code == 200
    first_batch = first.json()
    assert len(first_batch) == 10

    for item in first_batch:
        recorded = await client.post(
            "/me/matchmaker/swipes",
            json={"animal_id": item["id"], "disposition": "passed"},
            headers=token,
        )
        assert recorded.status_code == 201

    next_batch = await client.get(FEED, headers=token)

    assert next_batch.status_code == 200
    assert {item["id"] for item in next_batch.json()} == {
        str(animal.id) for animal in animals
    } - {item["id"] for item in first_batch}


async def test_at_14_a_profile_is_required_and_visitors_must_sign_in(
    client: httpx.AsyncClient, issuer: TokenIssuer, engine: AsyncEngine
) -> None:
    animal = await _publish(engine, "Rex")

    no_profile = await client.get(FEED, headers=_as(issuer, CARLA))
    visitor = await client.get(FEED)
    visitor_swipe = await client.post(
        "/me/matchmaker/swipes",
        json={"animal_id": str(animal.id), "disposition": "passed"},
    )

    assert no_profile.status_code == 409
    assert no_profile.json()["detail"]["code"] == "matchmaker_profile_required"
    assert visitor.status_code == 401
    assert visitor_swipe.status_code == 401
