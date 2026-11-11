"""AT-21 (the base's half): unpublishing closes the open requests.

Republishing and the new request that follows belong to US-19.
"""

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

from patas_backend.models.animal import AnimalRepository


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
