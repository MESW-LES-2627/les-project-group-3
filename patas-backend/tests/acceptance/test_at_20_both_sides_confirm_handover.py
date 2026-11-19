"""AT-20 (#74): Both sides confirm the handover and the animal is adopted.

Every test goes through the endpoints to the real database. Ana owns Rex, Bruno's
accepted request reserved him, and Carla is someone else.
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
)
from sqlalchemy.ext.asyncio import AsyncEngine
from token_issuer import TokenIssuer


def _confirm(application_id: UUID) -> str:
    return f"/applications/{application_id}/confirm-handover"


async def _animal_status(client: httpx.AsyncClient, animal_id: UUID) -> str:
    response = await client.get(f"/animals/{animal_id}")
    assert response.status_code == 200
    return response.json()["adoption_status"]


async def test_at_20_the_first_confirmation_keeps_the_request_accepted(
    client: httpx.AsyncClient, issuer: TokenIssuer, engine: AsyncEngine
) -> None:
    # Given Bruno's accepted request is what keeps Rex reserved
    rex = await _seed_rex(engine, "reserve")
    request = _request(rex, BRUNO, S.ACCEPTED)
    await _save(engine, request)

    # When the owner confirms first
    confirmed = await client.post(
        _confirm(request.id), headers=_bearer(issuer.token(**ANA))
    )

    # Then the request stays accepted, with only the owner's confirmation
    assert confirmed.status_code == 200
    body = confirmed.json()
    assert body["status"] == "accepted"
    assert body["owner_confirmed_at"] is not None
    assert body["applicant_confirmed_at"] is None
    assert await _animal_status(client, rex.id) == "reserved"


async def test_at_20_the_same_side_cannot_confirm_twice(
    client: httpx.AsyncClient, issuer: TokenIssuer, engine: AsyncEngine
) -> None:
    rex = await _seed_rex(engine, "reserve")
    request = _request(rex, BRUNO, S.ACCEPTED)
    await _save(engine, request)
    ana = _bearer(issuer.token(**ANA))
    await client.post(_confirm(request.id), headers=ana)

    again = await client.post(_confirm(request.id), headers=ana)

    assert again.status_code == 409
    assert again.json()["detail"]["code"] == "invalid_transition"


async def test_at_20_someone_else_cannot_confirm_the_handover(
    client: httpx.AsyncClient, issuer: TokenIssuer, engine: AsyncEngine
) -> None:
    rex = await _seed_rex(engine, "reserve")
    request = _request(rex, BRUNO, S.ACCEPTED)
    await _save(engine, request)

    response = await client.post(
        _confirm(request.id), headers=_bearer(issuer.token(**CARLA))
    )

    assert response.status_code == 403


async def test_at_20_the_second_confirmation_adopts_the_animal(
    client: httpx.AsyncClient, issuer: TokenIssuer, engine: AsyncEngine
) -> None:
    # Given the owner has already confirmed
    rex = await _seed_rex(engine, "reserve")
    request = _request(rex, BRUNO, S.ACCEPTED)
    await _save(engine, request)
    await client.post(_confirm(request.id), headers=_bearer(issuer.token(**ANA)))

    # When the applicant confirms second
    confirmed = await client.post(
        _confirm(request.id), headers=_bearer(issuer.token(**BRUNO))
    )

    # Then the request is adopted, both sides confirmed, and so did the animal
    assert confirmed.status_code == 200
    body = confirmed.json()
    assert body["status"] == "adopted"
    assert body["owner_confirmed_at"] is not None
    assert body["applicant_confirmed_at"] is not None
    assert await _animal_status(client, rex.id) == "adopted"


async def test_at_20_the_handover_can_be_confirmed_in_the_reverse_order(
    client: httpx.AsyncClient, issuer: TokenIssuer, engine: AsyncEngine
) -> None:
    # Given the applicant confirms first
    rex = await _seed_rex(engine, "reserve")
    request = _request(rex, BRUNO, S.ACCEPTED)
    await _save(engine, request)
    first = await client.post(
        _confirm(request.id), headers=_bearer(issuer.token(**BRUNO))
    )

    # Then the request is still accepted until the owner confirms
    assert first.json()["status"] == "accepted"
    assert await _animal_status(client, rex.id) == "reserved"

    # When the owner confirms second, the adoption completes
    second = await client.post(
        _confirm(request.id), headers=_bearer(issuer.token(**ANA))
    )

    assert second.status_code == 200
    assert second.json()["status"] == "adopted"
    assert await _animal_status(client, rex.id) == "adopted"
