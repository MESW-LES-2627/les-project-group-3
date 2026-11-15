"""The owner's endpoints for answering requests (US-16): what AT-17 and AT-18 do not
exercise. Accepting and declining share the same contract, so each test runs for both.
"""

from uuid import UUID

import httpx
import pytest
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
ACTIONS = pytest.mark.parametrize("action", ["accept", "decline"])


@ACTIONS
async def test_answering_needs_a_session(
    action: str, client: httpx.AsyncClient
) -> None:
    response = await client.post(f"/applications/{UNKNOWN}/{action}")

    assert response.status_code == 401


@ACTIONS
async def test_answering_a_request_that_ended_answers_409_with_a_code(
    action: str,
    client: httpx.AsyncClient,
    issuer: TokenIssuer,
    engine: AsyncEngine,
) -> None:
    rex = await _seed_rex(engine)
    request = _request(rex, BRUNO, S.WITHDRAWN)
    await _save(engine, request)

    response = await client.post(
        f"/applications/{request.id}/{action}", headers=_bearer(issuer.token(**ANA))
    )

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "invalid_transition"


@ACTIONS
async def test_answering_an_unknown_request_answers_404(
    action: str,
    client: httpx.AsyncClient,
    issuer: TokenIssuer,
    engine: AsyncEngine,
) -> None:
    await _seed_rex(engine)

    response = await client.post(
        f"/applications/{UNKNOWN}/{action}", headers=_bearer(issuer.token(**ANA))
    )

    assert response.status_code == 404
    # The detail proves the 404 came from the endpoint, not from a missing route.
    assert response.json()["detail"] == "Request not found"


@ACTIONS
async def test_a_note_over_1000_characters_answers_422_and_changes_nothing(
    action: str,
    client: httpx.AsyncClient,
    issuer: TokenIssuer,
    engine: AsyncEngine,
) -> None:
    rex = await _seed_rex(engine)
    request = _request(rex, BRUNO)
    await _save(engine, request)

    response = await client.post(
        f"/applications/{request.id}/{action}",
        json={"note": "a" * 1001},
        headers=_bearer(issuer.token(**ANA)),
    )

    assert response.status_code == 422
    assert "1000" in response.json()["detail"]
    assert await _status(engine, request) is S.OPEN


@ACTIONS
async def test_an_unknown_field_in_the_body_answers_422(
    action: str,
    client: httpx.AsyncClient,
    issuer: TokenIssuer,
    engine: AsyncEngine,
) -> None:
    rex = await _seed_rex(engine)
    request = _request(rex, BRUNO)
    await _save(engine, request)

    response = await client.post(
        f"/applications/{request.id}/{action}",
        json={"note": "No", "status": "declined"},
        headers=_bearer(issuer.token(**ANA)),
    )

    assert response.status_code == 422
    assert await _status(engine, request) is S.OPEN


async def test_accepting_without_a_note_stores_none(
    client: httpx.AsyncClient, issuer: TokenIssuer, engine: AsyncEngine
) -> None:
    rex = await _seed_rex(engine)
    request = _request(rex, BRUNO)
    await _save(engine, request)

    # No body at all: the note is optional.
    response = await client.post(
        f"/applications/{request.id}/accept", headers=_bearer(issuer.token(**ANA))
    )

    assert response.status_code == 200
    assert response.json()["status"] == "accepted"
    assert response.json()["owner_note"] is None
