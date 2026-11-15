"""The owner's endpoints for answering requests (US-16): what AT-17 and AT-18 do not
exercise."""

from uuid import UUID

import httpx
from adoption_endpoint import (
    ANA,
    BRUNO,
    S,
    _bearer,
    _request,
    _save,
    _seed_rex,
    _status,
)
from sqlalchemy.ext.asyncio import AsyncEngine
from token_issuer import TokenIssuer

UNKNOWN = UUID(int=1)


async def test_declining_needs_a_session(client: httpx.AsyncClient) -> None:
    response = await client.post(f"/applications/{UNKNOWN}/decline")

    assert response.status_code == 401


async def test_declining_a_request_that_ended_answers_409_with_a_code(
    client: httpx.AsyncClient, issuer: TokenIssuer, engine: AsyncEngine
) -> None:
    rex = await _seed_rex(engine)
    request = _request(rex, BRUNO, S.WITHDRAWN)
    await _save(engine, request)

    response = await client.post(
        f"/applications/{request.id}/decline", headers=_bearer(issuer.token(**ANA))
    )

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "invalid_transition"


async def test_declining_an_unknown_request_answers_404(
    client: httpx.AsyncClient, issuer: TokenIssuer, engine: AsyncEngine
) -> None:
    await _seed_rex(engine)

    response = await client.post(
        f"/applications/{UNKNOWN}/decline", headers=_bearer(issuer.token(**ANA))
    )

    assert response.status_code == 404
    # The detail proves the 404 came from the endpoint, not from a missing route.
    assert response.json()["detail"] == "Request not found"


async def test_a_note_over_1000_characters_answers_422_and_changes_nothing(
    client: httpx.AsyncClient, issuer: TokenIssuer, engine: AsyncEngine
) -> None:
    rex = await _seed_rex(engine)
    request = _request(rex, BRUNO)
    await _save(engine, request)

    response = await client.post(
        f"/applications/{request.id}/decline",
        json={"note": "a" * 1001},
        headers=_bearer(issuer.token(**ANA)),
    )

    assert response.status_code == 422
    assert "1000" in response.json()["detail"]
    assert await _status(engine, request) is S.OPEN


async def test_an_unknown_field_in_the_body_answers_422(
    client: httpx.AsyncClient, issuer: TokenIssuer, engine: AsyncEngine
) -> None:
    rex = await _seed_rex(engine)
    request = _request(rex, BRUNO)
    await _save(engine, request)

    response = await client.post(
        f"/applications/{request.id}/decline",
        json={"note": "No", "status": "accepted"},
        headers=_bearer(issuer.token(**ANA)),
    )

    assert response.status_code == 422
    assert await _status(engine, request) is S.OPEN
