"""AT-24 (#130): only the owner and the accepted applicant can chat.

Every test goes through the endpoints to the real database. Ably is stood in for by
the recording publisher (`live`): what it records is what each person's browser
would receive without reloading. Ana owns Rex, Bruno's request is the one Ana
accepts, and Carla is someone else.
"""

from uuid import UUID

import httpx
import pytest
from adoption_endpoint import ANA, BRUNO, CARLA, S, _bearer, _request, _save, _seed_rex
from live import RecordingPublisher
from sqlalchemy.ext.asyncio import AsyncEngine
from token_issuer import TokenIssuer


def _messages(application_id: UUID) -> str:
    return f"/applications/{application_id}/messages"


async def _say(
    client: httpx.AsyncClient,
    issuer: TokenIssuer,
    who: dict[str, str],
    application_id: UUID,
    body: str,
) -> httpx.Response:
    return await client.post(
        _messages(application_id),
        json={"body": body},
        headers=_bearer(issuer.token(**who)),
    )


async def _read(
    client: httpx.AsyncClient,
    issuer: TokenIssuer,
    who: dict[str, str],
    application_id: UUID,
) -> httpx.Response:
    return await client.get(
        _messages(application_id), headers=_bearer(issuer.token(**who))
    )


async def _act(
    client: httpx.AsyncClient,
    issuer: TokenIssuer,
    who: dict[str, str],
    application_id: UUID,
    action: str,
) -> None:
    response = await client.post(
        f"/applications/{application_id}/{action}",
        headers=_bearer(issuer.token(**who)),
    )
    assert response.status_code == 200, response.text


async def _ana_accepts_bruno(
    client: httpx.AsyncClient, issuer: TokenIssuer, engine: AsyncEngine
) -> UUID:
    rex = await _seed_rex(engine)
    request = _request(rex, BRUNO)
    await _save(engine, request)
    await _act(client, issuer, ANA, request.id, "accept")
    return request.id


async def test_at_24_bruno_writes_and_ana_gets_it_without_reloading(
    client: httpx.AsyncClient,
    issuer: TokenIssuer,
    engine: AsyncEngine,
    live: RecordingPublisher,
) -> None:
    # Given Ana accepted Bruno's request for Rex
    request = await _ana_accepts_bruno(client, issuer, engine)

    # When Bruno sends a message
    sent = await _say(client, issuer, BRUNO, request, "Can I visit Rex on Saturday?")

    # Then Ana's browser is told at once, and loading the new message shows it
    assert sent.status_code == 201
    message = sent.json()
    ((name, data),) = live.for_user(ANA["sub"])
    assert name == "message.posted"
    assert data["application_id"] == str(request)
    assert data["message_id"] == message["id"]
    assert data["sender_id"] == BRUNO["sub"]
    assert data["animal_name"] == "Rex"
    # The text never goes to Ably: the page fetches it from Patas.
    assert "Can I visit Rex on Saturday?" not in str(data)
    conversation = await _read(client, issuer, ANA, request)
    assert [m["body"] for m in conversation.json()] == ["Can I visit Rex on Saturday?"]
    # Bruno's other tabs are told too, and nobody else is
    assert [name for name, _ in live.for_user(BRUNO["sub"])] == ["message.posted"]
    assert live.for_user(CARLA["sub"]) == []


async def test_at_24_carla_whose_request_is_still_open_has_no_conversation(
    client: httpx.AsyncClient,
    issuer: TokenIssuer,
    engine: AsyncEngine,
    live: RecordingPublisher,
) -> None:
    rex = await _seed_rex(engine)
    carla = _request(rex, CARLA, S.OPEN)
    await _save(engine, carla)

    assert (await _read(client, issuer, CARLA, carla.id)).status_code == 404
    assert (await _read(client, issuer, ANA, carla.id)).status_code == 404
    assert (await _say(client, issuer, CARLA, carla.id, "Hello?")).status_code == 409
    assert (await _say(client, issuer, ANA, carla.id, "Hello?")).status_code == 409
    assert live.sent == []


async def test_at_24_nobody_else_can_read_or_write_in_their_conversation(
    client: httpx.AsyncClient,
    issuer: TokenIssuer,
    engine: AsyncEngine,
    live: RecordingPublisher,
) -> None:
    request = await _ana_accepts_bruno(client, issuer, engine)
    await _say(client, issuer, BRUNO, request, "Only for Ana")

    assert (await _read(client, issuer, CARLA, request)).status_code == 404
    assert (await _say(client, issuer, CARLA, request, "Hi!")).status_code == 404
    assert live.for_user(CARLA["sub"]) == []
    bodies = [m["body"] for m in (await _read(client, issuer, ANA, request)).json()]
    assert bodies == ["Only for Ana"]


@pytest.mark.parametrize(
    ("ending", "status"),
    [
        ([(ANA, "decline")], "declined"),
        ([(BRUNO, "withdraw")], "withdrawn"),
        ([(ANA, "confirm-handover"), (BRUNO, "confirm-handover")], "adopted"),
    ],
)
async def test_at_24_an_ended_request_can_still_be_read_but_not_written(
    client: httpx.AsyncClient,
    issuer: TokenIssuer,
    engine: AsyncEngine,
    live: RecordingPublisher,
    ending: list[tuple[dict[str, str], str]],
    status: str,
) -> None:
    request = await _ana_accepts_bruno(client, issuer, engine)
    await _say(client, issuer, BRUNO, request, "See you soon")

    # When the request ends
    for who, action in ending:
        await _act(client, issuer, who, request, action)

    # Then both pages are told, so the box to write disappears without reloading
    for who in (ANA, BRUNO):
        changes = [d for n, d in live.for_user(who["sub"]) if n == "request.changed"]
        assert changes == [{"application_id": str(request), "status": status}]
    # And both can still read, but no new message can be sent
    for who in (ANA, BRUNO):
        bodies = [m["body"] for m in (await _read(client, issuer, who, request)).json()]
        assert bodies == ["See you soon"]
        refused = await _say(client, issuer, who, request, "One more thing")
        assert refused.status_code == 409
