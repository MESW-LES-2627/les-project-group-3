"""AT-26 (#132), the handover checklist part: both sides tick it while the request is
accepted, it never blocks the handover, and after the adoption it stays as it was.

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

BOOKLET = "vaccination_booklet"
NOTES = "care_notes"  # the answers list items alphabetically: NOTES, BOOKLET


def _tick(application_id: UUID, item: str) -> str:
    return f"/applications/{application_id}/handover/{item}"


def _confirm(application_id: UUID) -> str:
    return f"/applications/{application_id}/confirm-handover"


async def _checked_by_bruno(
    client: httpx.AsyncClient, issuer: TokenIssuer
) -> list[str]:
    """What Bruno sees on his own list of requests."""
    response = await client.get(
        "/me/applications", headers=_bearer(issuer.token(**BRUNO))
    )
    assert response.status_code == 200
    (request,) = response.json()
    return request["handover_checked"]


async def _checked_by_ana(client: httpx.AsyncClient, issuer: TokenIssuer) -> list[str]:
    """What Ana sees on the list of requests she received."""
    response = await client.get(
        "/me/received-applications", headers=_bearer(issuer.token(**ANA))
    )
    assert response.status_code == 200
    (request,) = response.json()
    return request["handover_checked"]


async def test_at_26_an_item_ticked_by_one_side_stays_ticked_for_both(
    client: httpx.AsyncClient, issuer: TokenIssuer, engine: AsyncEngine
) -> None:
    # Given Bruno's request is accepted and nothing is ticked yet
    rex = await _seed_rex(engine, "reserve")
    request = _request(rex, BRUNO, S.ACCEPTED)
    await _save(engine, request)
    assert await _checked_by_ana(client, issuer) == []
    assert await _checked_by_bruno(client, issuer) == []

    # When Ana ticks one item and Bruno another
    ana = await client.put(
        _tick(request.id, BOOKLET),
        json={"checked": True},
        headers=_bearer(issuer.token(**ANA)),
    )
    bruno = await client.put(
        _tick(request.id, NOTES),
        json={"checked": True},
        headers=_bearer(issuer.token(**BRUNO)),
    )

    # Then each answer has the ticks so far, and both still see both after reloading
    assert ana.status_code == 200
    assert ana.json() == {"checked": [BOOKLET]}
    assert bruno.json() == {"checked": [NOTES, BOOKLET]}
    assert await _checked_by_ana(client, issuer) == [NOTES, BOOKLET]
    assert await _checked_by_bruno(client, issuer) == [NOTES, BOOKLET]


async def test_at_26_an_item_can_be_unticked(
    client: httpx.AsyncClient, issuer: TokenIssuer, engine: AsyncEngine
) -> None:
    rex = await _seed_rex(engine, "reserve")
    request = _request(rex, BRUNO, S.ACCEPTED)
    await _save(engine, request)
    ana = _bearer(issuer.token(**ANA))
    await client.put(_tick(request.id, NOTES), json={"checked": True}, headers=ana)

    unticked = await client.put(
        _tick(request.id, NOTES), json={"checked": False}, headers=ana
    )

    assert unticked.json() == {"checked": []}
    assert await _checked_by_bruno(client, issuer) == []


async def test_at_26_the_checklist_never_blocks_the_handover(
    client: httpx.AsyncClient, issuer: TokenIssuer, engine: AsyncEngine
) -> None:
    # Given an accepted request with every item unticked
    rex = await _seed_rex(engine, "reserve")
    request = _request(rex, BRUNO, S.ACCEPTED)
    await _save(engine, request)

    # When Ana confirms the handover anyway
    confirmed = await client.post(
        _confirm(request.id), headers=_bearer(issuer.token(**ANA))
    )

    # Then it is confirmed
    assert confirmed.status_code == 200
    assert confirmed.json()["owner_confirmed_at"] is not None


async def test_at_26_after_the_adoption_the_checklist_is_as_it_was_left(
    client: httpx.AsyncClient, issuer: TokenIssuer, engine: AsyncEngine
) -> None:
    # Given Ana ticked one item and both sides confirmed, so Rex is adopted
    rex = await _seed_rex(engine, "reserve")
    request = _request(rex, BRUNO, S.ACCEPTED)
    await _save(engine, request)
    ana = _bearer(issuer.token(**ANA))
    bruno = _bearer(issuer.token(**BRUNO))
    await client.put(_tick(request.id, BOOKLET), json={"checked": True}, headers=ana)
    await client.post(_confirm(request.id), headers=ana)
    adopted = await client.post(_confirm(request.id), headers=bruno)
    assert adopted.json()["status"] == "adopted"

    # When either side tries to change the checklist
    by_ana = await client.put(
        _tick(request.id, BOOKLET), json={"checked": False}, headers=ana
    )
    by_bruno = await client.put(
        _tick(request.id, NOTES), json={"checked": True}, headers=bruno
    )

    # Then both are refused and the checklist shows as it was
    for refused in (by_ana, by_bruno):
        assert refused.status_code == 409
        assert refused.json()["detail"]["code"] == "invalid_transition"
    assert await _checked_by_ana(client, issuer) == [BOOKLET]
    assert await _checked_by_bruno(client, issuer) == [BOOKLET]


async def test_at_26_someone_else_cannot_see_or_change_the_checklist(
    client: httpx.AsyncClient, issuer: TokenIssuer, engine: AsyncEngine
) -> None:
    rex = await _seed_rex(engine, "reserve")
    request = _request(rex, BRUNO, S.ACCEPTED)
    await _save(engine, request)
    carla = _bearer(issuer.token(**CARLA))

    changed = await client.put(
        _tick(request.id, NOTES), json={"checked": True}, headers=carla
    )
    listed = await client.get("/me/applications", headers=carla)

    assert changed.status_code == 404
    assert listed.json() == []
    assert await _checked_by_ana(client, issuer) == []
