"""AT-16 (#70): Send a request to adopt.

Every test goes through the endpoints to the real database. People are Ana (owns
Rex), Bruno and Carla.
"""

from uuid import UUID

import httpx
import pytest
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
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker
from token_issuer import TokenIssuer

from patas_backend.models.adoption import AdoptionApplicationRepository
from patas_backend.models.animal import Animal

PROFILE = "/me/matchmaker-profile"
HOUSE = {
    "housing": "house_with_yard",
    "activity": "high",
    "time_away": "half_day",
    "experience": "experienced",
    "has_children": True,
    "has_dogs": True,
    "has_cats": False,
}
FLAT = {**HOUSE, "housing": "apartment", "activity": "low"}
NOTE = "I have a garden and work from home."


def _applications(rex: Animal) -> str:
    return f"/animals/{rex.id}/applications"


def _mine(rex: Animal) -> str:
    return f"/animals/{rex.id}/my-application"


async def _save_profile(
    client: httpx.AsyncClient, issuer: TokenIssuer, who: dict[str, str]
) -> None:
    response = await client.put(
        PROFILE, json=HOUSE, headers=_bearer(issuer.token(**who))
    )
    assert response.status_code == 200


async def _count(engine: AsyncEngine, rex: Animal) -> int:
    async with engine.connect() as conn:
        return await conn.scalar(
            text(
                "SELECT count(*) FROM patas.adoption_applications"
                " WHERE animal_id = :animal_id"
            ),
            {"animal_id": rex.id},
        )


async def test_at_16_a_request_with_a_note_shows_on_the_animals_page(
    client: httpx.AsyncClient, issuer: TokenIssuer, engine: AsyncEngine
) -> None:
    # Given Bruno is signed in with a profile and Rex is available
    rex = await _seed_rex(engine)
    await _save_profile(client, issuer, BRUNO)
    bruno = _bearer(issuer.token(**BRUNO))

    # When he sends a request with a note
    sent = await client.post(_applications(rex), json={"note": NOTE}, headers=bruno)

    # Then Rex's page shows that he has an open request
    assert sent.status_code == 201
    mine = await client.get(_mine(rex), headers=bruno)
    assert mine.status_code == 200
    assert mine.json()["status"] == "open"
    assert mine.json()["note"] == NOTE
    assert mine.json()["animal_id"] == str(rex.id)


async def test_at_16_a_second_request_while_the_first_is_open_is_refused(
    client: httpx.AsyncClient, issuer: TokenIssuer, engine: AsyncEngine
) -> None:
    rex = await _seed_rex(engine)
    await _save_profile(client, issuer, BRUNO)
    bruno = _bearer(issuer.token(**BRUNO))
    await client.post(_applications(rex), json={"note": NOTE}, headers=bruno)

    again = await client.post(_applications(rex), json={"note": "Again"}, headers=bruno)

    assert again.status_code == 409
    assert again.json()["detail"]["code"] == "already_requested"
    assert await _count(engine, rex) == 1


async def test_at_16_a_withdrawn_request_does_not_block_a_new_one(
    client: httpx.AsyncClient, issuer: TokenIssuer, engine: AsyncEngine
) -> None:
    # Only an open or accepted request counts as "his first request is open".
    rex = await _seed_rex(engine)
    await _save(engine, _request(rex, BRUNO, S.WITHDRAWN))
    await _save_profile(client, issuer, BRUNO)

    response = await client.post(
        _applications(rex), json={"note": NOTE}, headers=_bearer(issuer.token(**BRUNO))
    )

    assert response.status_code == 201
    assert await _count(engine, rex) == 2


async def test_at_16_the_owner_cannot_request_her_own_animal(
    client: httpx.AsyncClient, issuer: TokenIssuer, engine: AsyncEngine
) -> None:
    # Ana has no profile on purpose: being the owner is what refuses her, not the
    # missing profile.
    rex = await _seed_rex(engine)

    response = await client.post(
        _applications(rex), json={"note": NOTE}, headers=_bearer(issuer.token(**ANA))
    )

    assert response.status_code == 403
    assert await _count(engine, rex) == 0


@pytest.mark.parametrize("state", ["reserved", "adopted", "unpublished"])
async def test_at_16_a_request_is_refused_while_the_animal_is_not_available(
    state: str, client: httpx.AsyncClient, issuer: TokenIssuer, engine: AsyncEngine
) -> None:
    moves = {"reserved": ("reserve",), "adopted": ("reserve", "mark_adopted")}
    rex = await _seed_rex(engine, *moves.get(state, ()))
    if state == "unpublished":
        # The real way to get there, through the owner's endpoint.
        done = await client.post(
            f"/animals/{rex.id}/unpublish", headers=_bearer(issuer.token(**ANA))
        )
        assert done.status_code == 200
    await _save_profile(client, issuer, BRUNO)

    response = await client.post(
        _applications(rex), json={"note": NOTE}, headers=_bearer(issuer.token(**BRUNO))
    )

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "animal_not_available"
    assert await _count(engine, rex) == 0


async def test_at_16_without_a_profile_the_applicant_is_asked_to_create_one(
    client: httpx.AsyncClient, issuer: TokenIssuer, engine: AsyncEngine
) -> None:
    rex = await _seed_rex(engine)

    response = await client.post(
        _applications(rex), json={"note": NOTE}, headers=_bearer(issuer.token(**BRUNO))
    )

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "matchmaker_profile_required"
    assert await _count(engine, rex) == 0


async def test_at_16_a_visitor_who_is_not_logged_in_gets_401(
    client: httpx.AsyncClient, engine: AsyncEngine
) -> None:
    rex = await _seed_rex(engine)

    sent = await client.post(_applications(rex), json={"note": NOTE})
    read = await client.get(_mine(rex))

    assert sent.status_code == 401
    assert read.status_code == 401
    assert await _count(engine, rex) == 0


@pytest.mark.parametrize("note", ["", "   ", "a" * 1001])
async def test_at_16_a_note_that_is_blank_or_over_1000_characters_is_rejected(
    note: str, client: httpx.AsyncClient, issuer: TokenIssuer, engine: AsyncEngine
) -> None:
    rex = await _seed_rex(engine)
    await _save_profile(client, issuer, BRUNO)

    response = await client.post(
        _applications(rex), json={"note": note}, headers=_bearer(issuer.token(**BRUNO))
    )

    assert response.status_code == 422
    assert await _count(engine, rex) == 0


async def test_at_16_a_note_of_exactly_1000_characters_is_accepted(
    client: httpx.AsyncClient, issuer: TokenIssuer, engine: AsyncEngine
) -> None:
    rex = await _seed_rex(engine)
    await _save_profile(client, issuer, BRUNO)

    response = await client.post(
        _applications(rex),
        json={"note": "a" * 1000},
        headers=_bearer(issuer.token(**BRUNO)),
    )

    assert response.status_code == 201


async def test_at_16_an_unknown_animal_is_404(
    client: httpx.AsyncClient, issuer: TokenIssuer, engine: AsyncEngine
) -> None:
    await _seed_rex(engine)
    await _save_profile(client, issuer, BRUNO)
    unknown = "00000000-0000-4000-8000-000000000000"

    response = await client.post(
        f"/animals/{unknown}/applications",
        json={"note": NOTE},
        headers=_bearer(issuer.token(**BRUNO)),
    )

    assert response.status_code == 404
    # The detail tells our 404 from the router's "Not Found" for an unknown route.
    assert response.json() == {"detail": "Animal not found"}


async def test_at_16_the_request_keeps_the_profile_as_it_was_when_asking(
    client: httpx.AsyncClient, issuer: TokenIssuer, engine: AsyncEngine
) -> None:
    rex = await _seed_rex(engine)
    await _save_profile(client, issuer, BRUNO)
    bruno = _bearer(issuer.token(**BRUNO))
    sent = await client.post(_applications(rex), json={"note": NOTE}, headers=bruno)

    # Bruno changes his answers afterwards.
    await client.put(PROFILE, json=FLAT, headers=bruno)

    async with async_sessionmaker(engine)() as session:
        stored = await AdoptionApplicationRepository(session).get_by_id(
            UUID(sent.json()["id"])
        )
    assert stored is not None
    assert stored.applicant_profile.housing.value == "house_with_yard"
    assert stored.applicant_profile.activity.value == "high"


async def test_at_16_a_person_only_sees_their_own_request(
    client: httpx.AsyncClient, issuer: TokenIssuer, engine: AsyncEngine
) -> None:
    rex = await _seed_rex(engine)
    await _save_profile(client, issuer, BRUNO)
    await client.post(
        _applications(rex), json={"note": NOTE}, headers=_bearer(issuer.token(**BRUNO))
    )

    carla = await client.get(_mine(rex), headers=_bearer(issuer.token(**CARLA)))
    bruno = await client.get(_mine(rex), headers=_bearer(issuer.token(**BRUNO)))

    assert carla.status_code == 404
    assert bruno.status_code == 200
