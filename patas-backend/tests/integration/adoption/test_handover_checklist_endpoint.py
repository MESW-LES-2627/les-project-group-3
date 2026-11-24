"""The handover checklist endpoint (US-25): what it refuses, through HTTP to the real
database. The story itself is AT-26."""

from uuid import UUID

import httpx
import pytest
from adoption_endpoint import ANA, BRUNO, S, _bearer, _request, _save, _seed_rex
from sqlalchemy.ext.asyncio import AsyncEngine
from token_issuer import TokenIssuer


def _tick(application_id: UUID, item: str = "care_notes") -> str:
    return f"/applications/{application_id}/handover/{item}"


@pytest.mark.parametrize("status", [S.OPEN, S.DECLINED, S.WITHDRAWN, S.CLOSED])
async def test_only_an_accepted_request_can_be_ticked(
    client: httpx.AsyncClient, issuer: TokenIssuer, engine: AsyncEngine, status: S
) -> None:
    rex = await _seed_rex(engine)
    request = _request(rex, BRUNO, status)
    await _save(engine, request)

    response = await client.put(
        _tick(request.id),
        json={"checked": True},
        headers=_bearer(issuer.token(**ANA)),
    )

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "invalid_transition"


async def test_an_unknown_item_is_refused(
    client: httpx.AsyncClient, issuer: TokenIssuer, engine: AsyncEngine
) -> None:
    rex = await _seed_rex(engine, "reserve")
    request = _request(rex, BRUNO, S.ACCEPTED)
    await _save(engine, request)

    response = await client.put(
        _tick(request.id, "free_dog_food"),
        json={"checked": True},
        headers=_bearer(issuer.token(**ANA)),
    )

    assert response.status_code == 422


@pytest.mark.parametrize(
    "body", [{}, {"checked": "yes please"}, {"checked": True, "by": "x"}]
)
async def test_the_body_is_only_whether_the_item_is_ticked(
    client: httpx.AsyncClient,
    issuer: TokenIssuer,
    engine: AsyncEngine,
    body: dict[str, object],
) -> None:
    rex = await _seed_rex(engine, "reserve")
    request = _request(rex, BRUNO, S.ACCEPTED)
    await _save(engine, request)

    response = await client.put(
        _tick(request.id), json=body, headers=_bearer(issuer.token(**ANA))
    )

    assert response.status_code == 422


async def test_a_request_that_does_not_exist_is_not_found(
    client: httpx.AsyncClient, issuer: TokenIssuer, engine: AsyncEngine
) -> None:
    await _seed_rex(engine)  # registers the people

    response = await client.put(
        _tick(UUID(int=1)),
        json={"checked": True},
        headers=_bearer(issuer.token(**ANA)),
    )

    assert response.status_code == 404


async def test_ticking_needs_a_signed_in_user(
    client: httpx.AsyncClient, engine: AsyncEngine
) -> None:
    rex = await _seed_rex(engine, "reserve")
    request = _request(rex, BRUNO, S.ACCEPTED)
    await _save(engine, request)

    response = await client.put(_tick(request.id), json={"checked": True})

    assert response.status_code == 401
