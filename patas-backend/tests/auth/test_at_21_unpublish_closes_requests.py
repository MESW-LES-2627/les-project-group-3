"""AT-21 (the base's half): unpublishing closes the open requests.

Republishing and the new request that follows belong to US-19.
"""

from datetime import UTC, datetime
from uuid import UUID, uuid4

import httpx
import pytest
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker
from token_issuer import TokenIssuer

from patas_backend.models.adoption import (
    AdoptionApplication,
    AdoptionApplicationRepository,
    ApplicationStatus,
    ProfileSnapshot,
)
from patas_backend.models.animal import Animal, AnimalRepository, Species
from patas_backend.models.matching import EnergyLevel, ExperienceLevel, TimeAway
from patas_backend.models.matchmaker_profile import HousingType
from patas_backend.models.user import User, UserRepository

S = ApplicationStatus
NOW = datetime(2026, 11, 7, 12, 0, tzinfo=UTC)
ANA = {
    "sub": "11111111-1111-1111-1111-111111111111",
    "name": "Ana",
    "email": "ana@example.com",
}
BRUNO = {
    "sub": "22222222-2222-2222-2222-222222222222",
    "name": "Bruno",
    "email": "bruno@example.com",
}
CARLA = {
    "sub": "33333333-3333-3333-3333-333333333333",
    "name": "Carla",
    "email": "carla@example.com",
}
SNAPSHOT = ProfileSnapshot(
    housing=HousingType.APARTMENT,
    activity=EnergyLevel.MODERATE,
    time_away=TimeAway.HALF_DAY,
    experience=ExperienceLevel.SOME,
    has_children=False,
    has_dogs=True,
    has_cats=False,
)


def _bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def _seed_rex(engine: AsyncEngine, *moves: str) -> Animal:
    """Rex, Ana's, with Ana, Bruno and Carla registered. `moves` are Animal methods
    applied in order to put him in the status the test needs."""
    async with async_sessionmaker(engine).begin() as session:
        users = UserRepository(session)
        for who in (ANA, BRUNO, CARLA):
            await users.ensure_exists(
                User.provision(
                    id=UUID(who["sub"]), name=who["name"], email=who["email"]
                )
            )
        rex = Animal.publish(owner_id=UUID(ANA["sub"]), name="Rex", species=Species.DOG)
        for move in moves:
            getattr(rex, move)()
        await AnimalRepository(session).add(rex)
    return rex


def _request(
    rex: Animal, who: dict[str, str], status: S = S.OPEN, **fields: object
) -> AdoptionApplication:
    return AdoptionApplication(
        id=uuid4(),
        animal_id=rex.id,
        owner_id=rex.owner_id,
        applicant_id=UUID(who["sub"]),
        applicant_note="Hello",
        applicant_profile=SNAPSHOT,
        status=status,
        **fields,
    )


async def _save(engine: AsyncEngine, *applications: AdoptionApplication) -> None:
    async with async_sessionmaker(engine).begin() as session:
        for application in applications:
            await AdoptionApplicationRepository(session).add(application)


async def _status(engine: AsyncEngine, application: AdoptionApplication) -> S:
    async with async_sessionmaker(engine)() as session:
        stored = await AdoptionApplicationRepository(session).get_by_id(application.id)
    assert stored is not None
    return stored.status


async def test_at_21_unpublishing_closes_the_open_requests(
    client: httpx.AsyncClient, issuer: TokenIssuer, engine: AsyncEngine
) -> None:
    # Given Rex has open requests from Bruno and Carla
    rex = await _seed_rex(engine)
    from_bruno, from_carla = _request(rex, BRUNO), _request(rex, CARLA)
    await _save(engine, from_bruno, from_carla)

    # When Ana unpublishes him
    response = await client.post(
        f"/animals/{rex.id}/unpublish", headers=_bearer(issuer.token(**ANA))
    )

    # Then both requests are closed and Rex disappears from public view.
    assert response.status_code == 200
    assert response.json()["adoption_status"] == "unavailable"
    assert await _status(engine, from_bruno) is S.CLOSED
    assert await _status(engine, from_carla) is S.CLOSED
    catalog = (await client.get("/animals")).json()
    assert all(a["id"] != str(rex.id) for a in catalog)
    assert (await client.get(f"/animals/{rex.id}")).status_code == 404


async def test_at_21_an_animal_without_requests_still_unpublishes(
    client: httpx.AsyncClient, issuer: TokenIssuer, engine: AsyncEngine
) -> None:
    rex = await _seed_rex(engine)

    response = await client.post(
        f"/animals/{rex.id}/unpublish", headers=_bearer(issuer.token(**ANA))
    )

    assert response.status_code == 200
    assert response.json()["adoption_status"] == "unavailable"


@pytest.mark.parametrize(
    ("moves", "status", "fields"),
    [
        (("reserve",), S.ACCEPTED, {}),
        (
            ("reserve", "mark_adopted"),
            S.ADOPTED,
            {"owner_confirmed_at": NOW, "applicant_confirmed_at": NOW},
        ),
    ],
    ids=["reserved", "adopted"],
)
async def test_at_21_unpublish_is_refused_while_reserved_or_adopted(
    client: httpx.AsyncClient,
    issuer: TokenIssuer,
    engine: AsyncEngine,
    moves: tuple[str, ...],
    status: S,
    fields: dict[str, object],
) -> None:
    rex = await _seed_rex(engine, *moves)
    application = _request(rex, BRUNO, status, **fields)
    await _save(engine, application)

    response = await client.post(
        f"/animals/{rex.id}/unpublish", headers=_bearer(issuer.token(**ANA))
    )

    assert response.status_code == 409
    async with async_sessionmaker(engine)() as session:
        stored = await AnimalRepository(session).get_by_id(rex.id)
    assert stored is not None
    assert stored.adoption_status is rex.adoption_status
    assert await _status(engine, application) is status
