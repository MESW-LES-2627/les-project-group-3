"""AT-21 (#75): unpublishing closes the requests, republishing does not reopen them."""

import httpx
import pytest
from adoption_endpoint import (
    ANA,
    BRUNO,
    CARLA,
    NOW,
    S,
    _bearer,
    _request,
    _save,
    _seed_rex,
    _status,
)
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker
from token_issuer import TokenIssuer

from patas_backend.models.adoption import AdoptionApplication
from patas_backend.models.animal import Animal, AnimalRepository

PROFILE = {
    "housing": "house_with_yard",
    "activity": "high",
    "time_away": "half_day",
    "experience": "experienced",
    "has_children": True,
    "has_dogs": True,
    "has_cats": False,
}


async def test_at_21_unpublishing_closes_the_open_requests(
    client: httpx.AsyncClient, issuer: TokenIssuer, engine: AsyncEngine
) -> None:
    # Given Rex has open requests from Bruno and Carla
    rex = await _seed_rex(engine)
    from_bruno, from_carla = _request(rex, BRUNO), _request(rex, CARLA)
    await _save(engine, from_bruno, from_carla)

    # When Ana unpublishes him
    response = await client.post(
        f"/animals/{rex.id}/unpublish", headers=_bearer(issuer.token(**ANA))
    )

    # Then both requests are closed and Rex disappears from public view.
    assert response.status_code == 200
    assert response.json()["adoption_status"] == "unavailable"
    assert await _status(engine, from_bruno) is S.CLOSED
    assert await _status(engine, from_carla) is S.CLOSED
    catalog = (await client.get("/animals")).json()
    assert all(a["id"] != str(rex.id) for a in catalog)
    assert (await client.get(f"/animals/{rex.id}")).status_code == 404


async def test_at_21_an_animal_without_requests_still_unpublishes(
    client: httpx.AsyncClient, issuer: TokenIssuer, engine: AsyncEngine
) -> None:
    rex = await _seed_rex(engine)

    response = await client.post(
        f"/animals/{rex.id}/unpublish", headers=_bearer(issuer.token(**ANA))
    )

    assert response.status_code == 200
    assert response.json()["adoption_status"] == "unavailable"


@pytest.mark.parametrize(
    ("moves", "status", "fields"),
    [
        (("reserve",), S.ACCEPTED, {}),
        (
            ("reserve", "mark_adopted"),
            S.ADOPTED,
            {"owner_confirmed_at": NOW, "applicant_confirmed_at": NOW},
        ),
    ],
    ids=["reserved", "adopted"],
)
async def test_at_21_unpublish_is_refused_while_reserved_or_adopted(
    client: httpx.AsyncClient,
    issuer: TokenIssuer,
    engine: AsyncEngine,
    moves: tuple[str, ...],
    status: S,
    fields: dict[str, object],
) -> None:
    rex = await _seed_rex(engine, *moves)
    application = _request(rex, BRUNO, status, **fields)
    await _save(engine, application)

    response = await client.post(
        f"/animals/{rex.id}/unpublish", headers=_bearer(issuer.token(**ANA))
    )

    assert response.status_code == 409
    async with async_sessionmaker(engine)() as session:
        stored = await AnimalRepository(session).get_by_id(rex.id)
    assert stored is not None
    assert stored.adoption_status is rex.adoption_status
    assert await _status(engine, application) is status


async def _unpublished_rex_with_requests(
    client: httpx.AsyncClient, issuer: TokenIssuer, engine: AsyncEngine
) -> tuple[Animal, AdoptionApplication, AdoptionApplication]:
    """Rex with requests from Bruno and Carla, which Ana's unpublish closed."""
    rex = await _seed_rex(engine)
    from_bruno, from_carla = _request(rex, BRUNO), _request(rex, CARLA)
    await _save(engine, from_bruno, from_carla)
    response = await client.post(
        f"/animals/{rex.id}/unpublish", headers=_bearer(issuer.token(**ANA))
    )
    assert response.status_code == 200
    return rex, from_bruno, from_carla


async def test_at_21_republishing_shows_rex_again_and_the_requests_stay_closed(
    client: httpx.AsyncClient, issuer: TokenIssuer, engine: AsyncEngine
) -> None:
    rex, from_bruno, from_carla = await _unpublished_rex_with_requests(
        client, issuer, engine
    )

    # When Ana republishes Rex
    response = await client.post(
        f"/animals/{rex.id}/republish", headers=_bearer(issuer.token(**ANA))
    )

    # Then he appears again and the closed requests stay closed.
    assert response.status_code == 200
    assert response.json()["adoption_status"] == "available"
    catalog = (await client.get("/animals")).json()
    assert any(a["id"] == str(rex.id) for a in catalog)
    assert (await client.get(f"/animals/{rex.id}")).status_code == 200
    assert await _status(engine, from_bruno) is S.CLOSED
    assert await _status(engine, from_carla) is S.CLOSED


async def test_at_21_after_republishing_bruno_can_request_again(
    client: httpx.AsyncClient, issuer: TokenIssuer, engine: AsyncEngine
) -> None:
    rex, from_bruno, _ = await _unpublished_rex_with_requests(client, issuer, engine)
    republished = await client.post(
        f"/animals/{rex.id}/republish", headers=_bearer(issuer.token(**ANA))
    )
    assert republished.status_code == 200
    bruno = _bearer(issuer.token(**BRUNO))
    profile = await client.put("/me/matchmaker-profile", json=PROFILE, headers=bruno)
    assert profile.status_code == 200

    response = await client.post(
        f"/animals/{rex.id}/applications", json={"note": "Still keen."}, headers=bruno
    )

    assert response.status_code == 201
    assert response.json()["status"] == "open"
    assert response.json()["id"] != str(from_bruno.id)
    assert await _status(engine, from_bruno) is S.CLOSED


async def test_at_21_only_the_owner_can_republish(
    client: httpx.AsyncClient, issuer: TokenIssuer, engine: AsyncEngine
) -> None:
    rex, _, _ = await _unpublished_rex_with_requests(client, issuer, engine)

    response = await client.post(
        f"/animals/{rex.id}/republish", headers=_bearer(issuer.token(**BRUNO))
    )

    assert response.status_code == 403
    assert (await client.get(f"/animals/{rex.id}")).status_code == 404


@pytest.mark.parametrize(
    ("moves", "status", "fields"),
    [
        (("reserve",), S.ACCEPTED, {}),
        (
            ("reserve", "mark_adopted"),
            S.ADOPTED,
            {"owner_confirmed_at": NOW, "applicant_confirmed_at": NOW},
        ),
    ],
    ids=["reserved", "adopted"],
)
async def test_at_21_republish_is_refused_while_reserved_or_adopted(
    client: httpx.AsyncClient,
    issuer: TokenIssuer,
    engine: AsyncEngine,
    moves: tuple[str, ...],
    status: S,
    fields: dict[str, object],
) -> None:
    rex = await _seed_rex(engine, *moves)
    await _save(engine, _request(rex, BRUNO, status, **fields))

    response = await client.post(
        f"/animals/{rex.id}/republish", headers=_bearer(issuer.token(**ANA))
    )

    assert response.status_code == 409
    async with async_sessionmaker(engine)() as session:
        stored = await AnimalRepository(session).get_by_id(rex.id)
    assert stored is not None
    assert stored.adoption_status is rex.adoption_status
