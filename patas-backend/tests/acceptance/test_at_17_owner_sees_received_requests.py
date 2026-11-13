"""AT-17 display slice: an owner sees received requests and applicant profiles.

The accept/decline flow is deliberately not exercised here; it belongs to US-16.
"""

import httpx
from adoption_endpoint import (
    ANA,
    BRUNO,
    CARLA,
    SNAPSHOT,
    S,
    _bearer,
    _request,
    _save,
    _seed_rex,
)
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker
from token_issuer import TokenIssuer

from patas_backend.models.animal import AnimalRepository
from patas_backend.models.matching import EnergyLevel

RECEIVED = "/me/received-applications"


async def test_at_17_owner_sees_received_requests_with_profiles_and_concerns(
    client: httpx.AsyncClient, issuer: TokenIssuer, engine: AsyncEngine
) -> None:
    rex = await _seed_rex(engine)
    rex.activity_level = EnergyLevel.LOW
    async with async_sessionmaker(engine).begin() as session:
        await AnimalRepository(session).update(rex)

    bruno = _request(rex, BRUNO, S.OPEN)
    bruno.applicant_note = "I have a calm home."
    carla = _request(rex, CARLA, S.DECLINED)
    carla.applicant_note = "I have cared for dogs before."
    await _save(engine, bruno, carla)

    response = await client.get(RECEIVED, headers=_bearer(issuer.token(**ANA)))

    assert response.status_code == 200
    requests = {request["id"]: request for request in response.json()}
    assert set(requests) == {str(bruno.id), str(carla.id)}
    assert requests[str(bruno.id)]["status"] == "open"
    assert requests[str(bruno.id)]["note"] == "I have a calm home."
    assert requests[str(bruno.id)]["animal_name"] == "Rex"
    assert requests[str(bruno.id)]["applicant_profile"] == SNAPSHOT.to_json()
    assert (
        "Its energy is a bit different from yours"
        in requests[str(bruno.id)]["compatibility_concerns"]
    )
    assert requests[str(carla.id)]["status"] == "declined"
    assert requests[str(carla.id)]["applicant_profile"] == SNAPSHOT.to_json()

    someone_elses_list = await client.get(
        RECEIVED, headers=_bearer(issuer.token(**CARLA))
    )
    assert someone_elses_list.status_code == 200
    assert someone_elses_list.json() == []


async def test_received_requests_endpoint_requires_a_session(
    client: httpx.AsyncClient,
) -> None:
    response = await client.get(RECEIVED)

    assert response.status_code == 401
