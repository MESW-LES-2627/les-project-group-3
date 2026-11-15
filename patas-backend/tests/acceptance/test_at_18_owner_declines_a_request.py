"""AT-18 (#72): The owner declines a request.

Every test goes through the endpoints to the real database. Ana owns Rex, Bruno and
Carla asked to adopt him.

Two bullets of the AT need the owner to accept a request, which US-16 adds in the
same story: a declined request cannot be accepted afterwards, and a declined accepted
request lets Carla's open one be accepted. They live with the accept endpoint.
"""

from uuid import UUID

import httpx
from adoption_endpoint import (
    ANA,
    BRUNO,
    CARLA,
    S,
    _bearer,
    _request,
    _save,
    _seed_rex,
    _status,
)
from sqlalchemy.ext.asyncio import AsyncEngine
from token_issuer import TokenIssuer

MINE = "/me/applications"


def _decline(application_id: UUID) -> str:
    return f"/applications/{application_id}/decline"


async def test_at_18_a_declined_request_shows_as_declined_with_the_owners_note(
    client: httpx.AsyncClient, issuer: TokenIssuer, engine: AsyncEngine
) -> None:
    # Given Carla has an open request
    rex = await _seed_rex(engine)
    request = _request(rex, CARLA)
    await _save(engine, request)

    # When Ana declines it with a note
    declined = await client.post(
        _decline(request.id),
        json={"note": "Rex needs a home with a garden."},
        headers=_bearer(issuer.token(**ANA)),
    )

    # Then it shows as declined, with her note, in Carla's list
    assert declined.status_code == 200
    listed = await client.get(MINE, headers=_bearer(issuer.token(**CARLA)))
    assert [(r["id"], r["status"], r["owner_note"]) for r in listed.json()] == [
        (str(request.id), "declined", "Rex needs a home with a garden.")
    ]


async def test_at_18_the_owner_can_decline_without_a_note(
    client: httpx.AsyncClient, issuer: TokenIssuer, engine: AsyncEngine
) -> None:
    rex = await _seed_rex(engine)
    request = _request(rex, CARLA)
    await _save(engine, request)

    # No body at all: the note is optional.
    declined = await client.post(
        _decline(request.id), headers=_bearer(issuer.token(**ANA))
    )

    assert declined.status_code == 200
    assert declined.json()["status"] == "declined"
    assert declined.json()["owner_note"] is None
    assert await _status(engine, request) is S.DECLINED


async def test_at_18_declining_an_accepted_request_makes_the_animal_available(
    client: httpx.AsyncClient, issuer: TokenIssuer, engine: AsyncEngine
) -> None:
    # Bruno's accepted request is what keeps Rex reserved.
    rex = await _seed_rex(engine, "reserve")
    request = _request(rex, BRUNO, S.ACCEPTED)
    await _save(engine, request)

    declined = await client.post(
        _decline(request.id), headers=_bearer(issuer.token(**ANA))
    )

    assert declined.status_code == 200
    assert await _status(engine, request) is S.DECLINED
    page = await client.get(f"/animals/{rex.id}")
    assert page.json()["adoption_status"] == "available"


async def test_at_18_only_the_owner_can_decline(
    client: httpx.AsyncClient, issuer: TokenIssuer, engine: AsyncEngine
) -> None:
    rex = await _seed_rex(engine)
    request = _request(rex, BRUNO)
    await _save(engine, request)

    # The applicant cannot answer his own request, and a stranger cannot either.
    by_applicant = await client.post(
        _decline(request.id), headers=_bearer(issuer.token(**BRUNO))
    )
    by_stranger = await client.post(
        _decline(request.id), headers=_bearer(issuer.token(**CARLA))
    )

    # To them the request does not exist: 404, not 403 (ADR 0020, decision 5).
    for response in (by_applicant, by_stranger):
        assert response.status_code == 404
        assert response.json()["detail"] == "Request not found"
    assert await _status(engine, request) is S.OPEN
