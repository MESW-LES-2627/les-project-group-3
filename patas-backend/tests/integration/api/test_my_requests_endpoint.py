"""The endpoints for my requests (US-17): the answers AT-19 does not exercise."""

from uuid import UUID

import httpx
import pytest
from adoption_endpoint import BRUNO, S, _bearer, _request, _save, _seed_rex
from sqlalchemy.ext.asyncio import AsyncEngine
from token_issuer import TokenIssuer

UNKNOWN = UUID(int=1)


@pytest.mark.parametrize(
    ("method", "path"),
    [("GET", "/me/applications"), ("POST", f"/applications/{UNKNOWN}/withdraw")],
)
async def test_both_endpoints_need_a_session(
    method: str, path: str, client: httpx.AsyncClient
) -> None:
    response = await client.request(method, path)

    assert response.status_code == 401


async def test_withdrawing_a_request_that_ended_answers_409_with_a_code(
    client: httpx.AsyncClient, issuer: TokenIssuer, engine: AsyncEngine
) -> None:
    rex = await _seed_rex(engine)
    request = _request(rex, BRUNO, S.DECLINED)
    await _save(engine, request)

    response = await client.post(
        f"/applications/{request.id}/withdraw", headers=_bearer(issuer.token(**BRUNO))
    )

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "invalid_transition"


async def test_withdrawing_an_unknown_request_answers_404(
    client: httpx.AsyncClient, issuer: TokenIssuer, engine: AsyncEngine
) -> None:
    await _seed_rex(engine)

    response = await client.post(
        f"/applications/{UNKNOWN}/withdraw", headers=_bearer(issuer.token(**BRUNO))
    )

    assert response.status_code == 404
