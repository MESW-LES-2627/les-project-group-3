"""AT-15 (#69): Keep passed animals hidden and show saved animals."""

import httpx
from compatibility_endpoint import BRUNO, CARLA, _as, _save_home
from matchmaker_swipe_endpoint import _owner_claims, _publish
from sqlalchemy.ext.asyncio import AsyncEngine
from token_issuer import TokenIssuer

from patas_backend.models.animal import Animal

FEED = "/me/matchmaker/swipes/feed"
SAVED = "/me/matchmaker/swipes/saved"
NOTE = "We have room in our home and would love to meet."


async def _record(
    client: httpx.AsyncClient,
    headers: dict[str, str],
    animal: Animal,
    disposition: str,
) -> httpx.Response:
    return await client.post(
        "/me/matchmaker/swipes",
        json={"animal_id": str(animal.id), "disposition": disposition},
        headers=headers,
    )


async def test_at_15_swipes_are_private_and_saved_animals_can_be_requested(
    client: httpx.AsyncClient, issuer: TokenIssuer, engine: AsyncEngine
) -> None:
    await _save_home(client, issuer, CARLA)
    await _save_home(client, issuer, BRUNO)
    passed = await _publish(engine, "Passed")
    saved = await _publish(engine, "Saved")
    carla = _as(issuer, CARLA)
    bruno = _as(issuer, BRUNO)

    pass_response = await _record(client, carla, passed, "passed")
    save_response = await _record(client, carla, saved, "saved")
    duplicate = await _record(client, carla, passed, "saved")
    carla_feed = await client.get(FEED, headers=carla)
    bruno_feed = await client.get(FEED, headers=bruno)
    saved_list = await client.get(SAVED, headers=carla)
    request = await client.post(
        f"/animals/{saved.id}/applications",
        json={"note": NOTE},
        headers=carla,
    )

    assert pass_response.status_code == 201
    assert save_response.status_code == 201
    assert duplicate.status_code == 409
    assert {item["id"] for item in carla_feed.json()} == set()
    assert {item["id"] for item in bruno_feed.json()} == {
        str(passed.id),
        str(saved.id),
    }
    assert [item["id"] for item in saved_list.json()] == [str(saved.id)]
    assert request.status_code == 201

    removed = await client.delete(f"/me/matchmaker/swipes/{saved.id}", headers=carla)
    saved_after_removal = await client.get(SAVED, headers=carla)
    feed_after_removal = await client.get(FEED, headers=carla)

    assert removed.status_code == 204
    assert saved_after_removal.json() == []
    assert {item["id"] for item in feed_after_removal.json()} == set()


async def test_at_15_unpublished_animals_disappear_from_saved_list(
    client: httpx.AsyncClient, issuer: TokenIssuer, engine: AsyncEngine
) -> None:
    await _save_home(client, issuer, CARLA)
    animal = await _publish(engine, "Mia")
    saved = await _record(client, _as(issuer, CARLA), animal, "saved")
    assert saved.status_code == 201

    unpublished = await client.post(
        f"/animals/{animal.id}/unpublish",
        headers=_as(issuer, _owner_claims()),
    )
    assert unpublished.status_code == 200

    saved_list = await client.get(SAVED, headers=_as(issuer, CARLA))

    assert saved_list.status_code == 200
    assert saved_list.json() == []


async def test_at_15_visitors_cannot_read_or_change_swipes(
    client: httpx.AsyncClient, issuer: TokenIssuer, engine: AsyncEngine
) -> None:
    await _save_home(client, issuer, CARLA)
    animal = await _publish(engine, "Mia")

    read = await client.get(SAVED)
    passed = await _record(client, {}, animal, "passed")
    saved = await _record(client, {}, animal, "saved")

    assert read.status_code == 401
    assert passed.status_code == 401
    assert saved.status_code == 401
