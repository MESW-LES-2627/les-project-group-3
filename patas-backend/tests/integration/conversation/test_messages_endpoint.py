"""US-21: the messages of a conversation, through the endpoints and the real database.
Ana owns Rex, Bruno's request was accepted, and Carla is someone else."""

from uuid import UUID, uuid4

import httpx
from adoption_endpoint import ANA, BRUNO, CARLA, S, _bearer, _request, _save, _seed_rex
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine
from token_issuer import TokenIssuer


def _messages(application_id: UUID) -> str:
    return f"/applications/{application_id}/messages"


async def _post(
    client: httpx.AsyncClient,
    issuer: TokenIssuer,
    who: dict[str, str],
    application_id: UUID,
    body: object,
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
    after: UUID | None = None,
) -> httpx.Response:
    params = {"after": str(after)} if after else {}
    return await client.get(
        _messages(application_id),
        params=params,
        headers=_bearer(issuer.token(**who)),
    )


async def _stored_count(engine: AsyncEngine) -> int:
    async with engine.connect() as conn:
        return await conn.scalar(text("SELECT count(*) FROM patas.messages")) or 0


async def _accepted(engine: AsyncEngine) -> UUID:
    rex = await _seed_rex(engine, "reserve")
    request = _request(rex, BRUNO, S.ACCEPTED)
    await _save(engine, request)
    return request.id


async def test_both_sides_see_the_messages_in_order(
    client: httpx.AsyncClient, issuer: TokenIssuer, engine: AsyncEngine
) -> None:
    request = await _accepted(engine)

    bruno = await _post(client, issuer, BRUNO, request, "  Can I visit Rex?  ")
    ana = await _post(client, issuer, ANA, request, "Saturday morning?")

    assert bruno.status_code == 201
    assert ana.status_code == 201
    sent = bruno.json()
    assert sent["body"] == "Can I visit Rex?"
    assert sent["sender_id"] == BRUNO["sub"]
    assert sent["sender_name"] == "Bruno"
    assert sent["sender_username"]
    assert sent["application_id"] == str(request)
    for who in (ANA, BRUNO):
        response = await _read(client, issuer, who, request)
        assert response.status_code == 200
        assert [m["body"] for m in response.json()] == [
            "Can I visit Rex?",
            "Saturday morning?",
        ]


async def test_after_gives_only_the_newer_messages(
    client: httpx.AsyncClient, issuer: TokenIssuer, engine: AsyncEngine
) -> None:
    request = await _accepted(engine)
    first = (await _post(client, issuer, BRUNO, request, "one")).json()
    await _post(client, issuer, ANA, request, "two")
    await _post(client, issuer, BRUNO, request, "three")

    newer = await _read(client, issuer, ANA, request, after=UUID(first["id"]))

    assert [m["body"] for m in newer.json()] == ["two", "three"]


async def test_an_unknown_after_gives_the_whole_conversation(
    client: httpx.AsyncClient, issuer: TokenIssuer, engine: AsyncEngine
) -> None:
    request = await _accepted(engine)
    await _post(client, issuer, BRUNO, request, "one")

    response = await _read(client, issuer, ANA, request, after=uuid4())

    assert [m["body"] for m in response.json()] == ["one"]


async def test_someone_else_can_neither_read_nor_write(
    client: httpx.AsyncClient, issuer: TokenIssuer, engine: AsyncEngine
) -> None:
    request = await _accepted(engine)
    await _post(client, issuer, BRUNO, request, "private")

    assert (await _read(client, issuer, CARLA, request)).status_code == 404
    assert (await _post(client, issuer, CARLA, request, "hi")).status_code == 404
    assert await _stored_count(engine) == 1


async def test_an_unknown_request_is_404(
    client: httpx.AsyncClient, issuer: TokenIssuer, engine: AsyncEngine
) -> None:
    await _seed_rex(engine)

    assert (await _read(client, issuer, ANA, uuid4())).status_code == 404
    assert (await _post(client, issuer, ANA, uuid4(), "hi")).status_code == 404


async def test_an_open_request_has_no_conversation(
    client: httpx.AsyncClient, issuer: TokenIssuer, engine: AsyncEngine
) -> None:
    rex = await _seed_rex(engine)
    request = _request(rex, BRUNO, S.OPEN)
    await _save(engine, request)

    assert (await _read(client, issuer, BRUNO, request.id)).status_code == 404
    posted = await _post(client, issuer, BRUNO, request.id, "hi")
    assert posted.status_code == 409
    assert posted.json()["detail"]["code"] == "conversation_closed"
    assert await _stored_count(engine) == 0


async def test_a_request_declined_while_open_never_had_a_conversation(
    client: httpx.AsyncClient, issuer: TokenIssuer, engine: AsyncEngine
) -> None:
    rex = await _seed_rex(engine)
    request = _request(rex, BRUNO, S.DECLINED)
    await _save(engine, request)

    assert (await _read(client, issuer, BRUNO, request.id)).status_code == 404
    assert (await _read(client, issuer, ANA, request.id)).status_code == 404


async def test_an_ended_conversation_can_be_read_but_not_written(
    client: httpx.AsyncClient, issuer: TokenIssuer, engine: AsyncEngine
) -> None:
    request = await _accepted(engine)
    await _post(client, issuer, BRUNO, request, "before")
    declined = await client.post(
        f"/applications/{request}/decline", headers=_bearer(issuer.token(**ANA))
    )
    assert declined.status_code == 200

    for who in (ANA, BRUNO):
        response = await _read(client, issuer, who, request)
        assert [m["body"] for m in response.json()] == ["before"]
        posted = await _post(client, issuer, who, request, "after")
        assert posted.status_code == 409
        assert posted.json()["detail"]["code"] == "conversation_closed"
    assert await _stored_count(engine) == 1


async def test_blank_or_too_long_messages_are_422_and_not_saved(
    client: httpx.AsyncClient, issuer: TokenIssuer, engine: AsyncEngine
) -> None:
    request = await _accepted(engine)

    for body in ("   ", "a" * 2001):
        response = await _post(client, issuer, BRUNO, request, body)
        assert response.status_code == 422
    assert await _stored_count(engine) == 0


async def test_unknown_fields_are_422(
    client: httpx.AsyncClient, issuer: TokenIssuer, engine: AsyncEngine
) -> None:
    request = await _accepted(engine)

    response = await client.post(
        _messages(request),
        json={"body": "hi", "sender_id": CARLA["sub"]},
        headers=_bearer(issuer.token(**BRUNO)),
    )

    assert response.status_code == 422
