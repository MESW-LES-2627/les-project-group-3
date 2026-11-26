"""US-21: what is announced live, and what is not, through the endpoints and the real
database. When Ably fails, the change itself must stand."""

import httpx
import pytest
from adoption_endpoint import ANA, BRUNO, S, _bearer, _request, _save, _seed_rex
from live import FailingPublisher, RecordingPublisher
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine
from token_issuer import TokenIssuer


async def test_declining_an_open_request_announces_nothing(
    client: httpx.AsyncClient,
    issuer: TokenIssuer,
    engine: AsyncEngine,
    live: RecordingPublisher,
) -> None:
    # It never had a conversation, so there is no page to update.
    rex = await _seed_rex(engine)
    request = _request(rex, BRUNO, S.OPEN)
    await _save(engine, request)

    response = await client.post(
        f"/applications/{request.id}/decline", headers=_bearer(issuer.token(**ANA))
    )

    assert response.status_code == 200
    assert live.sent == []


class TestWhenAblyIsDown:
    @pytest.fixture
    def live(self) -> RecordingPublisher:
        return FailingPublisher()

    async def test_the_message_is_still_saved(
        self, client: httpx.AsyncClient, issuer: TokenIssuer, engine: AsyncEngine
    ) -> None:
        rex = await _seed_rex(engine, "reserve")
        request = _request(rex, BRUNO, S.ACCEPTED)
        await _save(engine, request)

        response = await client.post(
            f"/applications/{request.id}/messages",
            json={"body": "Hello"},
            headers=_bearer(issuer.token(**BRUNO)),
        )

        assert response.status_code == 201
        async with engine.connect() as conn:
            count = await conn.scalar(text("SELECT count(*) FROM patas.messages"))
        assert count == 1

    async def test_a_decline_still_happens(
        self, client: httpx.AsyncClient, issuer: TokenIssuer, engine: AsyncEngine
    ) -> None:
        rex = await _seed_rex(engine, "reserve")
        request = _request(rex, BRUNO, S.ACCEPTED)
        await _save(engine, request)

        response = await client.post(
            f"/applications/{request.id}/decline",
            headers=_bearer(issuer.token(**ANA)),
        )

        assert response.status_code == 200
        assert response.json()["status"] == "declined"
