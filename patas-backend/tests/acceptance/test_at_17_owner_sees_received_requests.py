"""AT-17 (#71): The owner accepts one request and the animal is reserved.

Every test goes through the endpoints to the real database. Ana owns Rex, Bruno and
Carla asked to adopt him. The first test is the display half (US-15), the rest
accept a request (US-16).
"""

from uuid import UUID

import httpx
import pytest
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
    _status,
)
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker
from token_issuer import TokenIssuer

from patas_backend.models.animal import AnimalRepository
from patas_backend.models.matching import EnergyLevel

RECEIVED = "/me/received-applications"
MINE = "/me/applications"


def _accept(application_id: UUID) -> str:
    return f"/applications/{application_id}/accept"


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


async def test_at_17_accepting_a_request_shows_it_accepted_and_reserves_the_animal(
    client: httpx.AsyncClient, issuer: TokenIssuer, engine: AsyncEngine
) -> None:
    # Given Bruno and Carla have open requests for Rex
    rex = await _seed_rex(engine)
    bruno = _request(rex, BRUNO)
    carla = _request(rex, CARLA)
    await _save(engine, bruno, carla)
    ana = _bearer(issuer.token(**ANA))

    # When Ana accepts Bruno's with a note
    accepted = await client.post(
        _accept(bruno.id), json={"note": "Come and meet Rex."}, headers=ana
    )

    # Then it shows as accepted in her list, Carla's stays open, and Rex is reserved
    assert accepted.status_code == 200
    listed = await client.get(RECEIVED, headers=ana)
    assert {r["id"]: r["status"] for r in listed.json()} == {
        str(bruno.id): "accepted",
        str(carla.id): "open",
    }
    page = await client.get(f"/animals/{rex.id}")
    assert page.json()["adoption_status"] == "reserved"
    # Bruno sees her note in his own list.
    his = await client.get(MINE, headers=_bearer(issuer.token(**BRUNO)))
    assert [(r["status"], r["owner_note"]) for r in his.json()] == [
        ("accepted", "Come and meet Rex.")
    ]


async def test_at_17_while_the_animal_is_reserved_no_other_request_can_be_accepted(
    client: httpx.AsyncClient, issuer: TokenIssuer, engine: AsyncEngine
) -> None:
    # Bruno's accepted request is what keeps Rex reserved.
    rex = await _seed_rex(engine, "reserve")
    bruno = _request(rex, BRUNO, S.ACCEPTED)
    carla = _request(rex, CARLA)
    await _save(engine, bruno, carla)

    response = await client.post(
        _accept(carla.id), headers=_bearer(issuer.token(**ANA))
    )

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "animal_not_available"
    # Nothing changed: the refusal rolled the whole accept back.
    assert await _status(engine, carla) is S.OPEN
    assert await _status(engine, bruno) is S.ACCEPTED
    page = await client.get(f"/animals/{rex.id}")
    assert page.json()["adoption_status"] == "reserved"


@pytest.mark.parametrize("status", [S.WITHDRAWN, S.DECLINED, S.CLOSED])
async def test_at_17_a_request_that_is_not_open_cannot_be_accepted(
    status: S,
    client: httpx.AsyncClient,
    issuer: TokenIssuer,
    engine: AsyncEngine,
) -> None:
    rex = await _seed_rex(engine)
    request = _request(rex, BRUNO, status)
    await _save(engine, request)

    response = await client.post(
        _accept(request.id), headers=_bearer(issuer.token(**ANA))
    )

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "invalid_transition"
    assert await _status(engine, request) is status
    page = await client.get(f"/animals/{rex.id}")
    assert page.json()["adoption_status"] == "available"


async def test_at_17_only_the_owner_can_accept_and_others_see_nothing(
    client: httpx.AsyncClient, issuer: TokenIssuer, engine: AsyncEngine
) -> None:
    rex = await _seed_rex(engine)
    request = _request(rex, BRUNO)
    await _save(engine, request)

    # The applicant cannot accept his own request, and a stranger cannot either.
    by_applicant = await client.post(
        _accept(request.id), headers=_bearer(issuer.token(**BRUNO))
    )
    by_stranger = await client.post(
        _accept(request.id), headers=_bearer(issuer.token(**CARLA))
    )

    # To them the request does not exist: 404, not 403 (ADR 0020, decision 5).
    for response in (by_applicant, by_stranger):
        assert response.status_code == 404
        assert response.json()["detail"] == "Request not found"
    assert await _status(engine, request) is S.OPEN
    page = await client.get(f"/animals/{rex.id}")
    assert page.json()["adoption_status"] == "available"
    # And the stranger's received list shows none of it.
    hers = await client.get(RECEIVED, headers=_bearer(issuer.token(**CARLA)))
    assert hers.json() == []
