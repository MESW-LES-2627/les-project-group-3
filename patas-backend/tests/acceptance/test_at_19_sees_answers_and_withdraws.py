"""AT-19 (#73): The applicant sees the answers and withdraws.

Every test goes through the endpoints to the real database. Ana owns the animals,
Bruno asked to adopt them, and Carla is someone else.
"""

from uuid import UUID

import httpx
from adoption_endpoint import (
    BRUNO,
    CARLA,
    S,
    _bearer,
    _request,
    _save,
    _seed_animal,
    _seed_rex,
    _status,
)
from sqlalchemy.ext.asyncio import AsyncEngine
from token_issuer import TokenIssuer

MINE = "/me/applications"


def _withdraw(application_id: UUID) -> str:
    return f"/applications/{application_id}/withdraw"


async def test_at_19_each_request_shows_its_status_and_the_owners_note(
    client: httpx.AsyncClient, issuer: TokenIssuer, engine: AsyncEngine
) -> None:
    # Given Bruno has an accepted request with a note and a declined one with a note
    rex = await _seed_rex(engine, "reserve")
    luna = await _seed_animal(engine, "Luna")
    await _save(
        engine,
        _request(rex, BRUNO, S.ACCEPTED, owner_note="Come meet him on Saturday."),
        _request(
            luna, BRUNO, S.DECLINED, owner_note="She needs a home without stairs."
        ),
    )

    # When he opens his requests
    response = await client.get(MINE, headers=_bearer(issuer.token(**BRUNO)))

    # Then each shows its status and the owner's note
    assert response.status_code == 200
    seen = {r["animal_name"]: (r["status"], r["owner_note"]) for r in response.json()}
    assert seen == {
        "Rex": ("accepted", "Come meet him on Saturday."),
        "Luna": ("declined", "She needs a home without stairs."),
    }


async def test_at_19_a_withdrawn_open_request_shows_as_withdrawn(
    client: httpx.AsyncClient, issuer: TokenIssuer, engine: AsyncEngine
) -> None:
    rex = await _seed_rex(engine)
    request = _request(rex, BRUNO)
    await _save(engine, request)
    bruno = _bearer(issuer.token(**BRUNO))

    withdrawn = await client.post(_withdraw(request.id), headers=bruno)

    assert withdrawn.status_code == 200
    assert withdrawn.json()["status"] == "withdrawn"
    listed = await client.get(MINE, headers=bruno)
    assert [(r["id"], r["status"]) for r in listed.json()] == [
        (str(request.id), "withdrawn")
    ]


async def test_at_19_withdrawing_an_accepted_request_makes_the_animal_available(
    client: httpx.AsyncClient, issuer: TokenIssuer, engine: AsyncEngine
) -> None:
    # Bruno's accepted request is what keeps Rex reserved.
    rex = await _seed_rex(engine, "reserve")
    request = _request(rex, BRUNO, S.ACCEPTED)
    await _save(engine, request)

    withdrawn = await client.post(
        _withdraw(request.id), headers=_bearer(issuer.token(**BRUNO))
    )

    assert withdrawn.status_code == 200
    page = await client.get(f"/animals/{rex.id}")
    assert page.json()["adoption_status"] == "available"


async def test_at_19_other_users_cannot_see_or_withdraw_brunos_requests(
    client: httpx.AsyncClient, issuer: TokenIssuer, engine: AsyncEngine
) -> None:
    rex = await _seed_rex(engine)
    request = _request(rex, BRUNO)
    await _save(engine, request)
    carla = _bearer(issuer.token(**CARLA))

    her_list = await client.get(MINE, headers=carla)
    her_withdraw = await client.post(_withdraw(request.id), headers=carla)

    assert her_list.status_code == 200
    assert her_list.json() == []
    # To Carla the request does not exist: 404, not 403 (decision 2).
    assert her_withdraw.status_code == 404
    assert her_withdraw.json()["detail"] == "Request not found"
    assert await _status(engine, request) is S.OPEN
