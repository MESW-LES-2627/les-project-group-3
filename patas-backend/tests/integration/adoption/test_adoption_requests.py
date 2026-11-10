"""Requesting to adopt (US-14), through the service and the real database.

The animal's row lock is what keeps a request consistent with an unpublish and with
the same person asking twice. Each race test holds that lock, lets the contenders
run into it, and only then releases it, so the contention is real, not hoped for.
"""

import asyncio
from uuid import UUID

import pytest
from adoption_factory import (
    Factory,
    World,
    adoption_dispatcher,
    until_blocked,
)
from patas_backend.services.adoption import AdoptionService
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from patas_backend.models.adoption import (
    AdoptionApplicationRepository,
    AlreadyRequested,
    ApplicationStatus,
)
from patas_backend.models.animal import (
    AdoptionStatus,
    AnimalNotAvailable,
    AnimalRepository,
)
from patas_backend.models.matching import EnergyLevel, ExperienceLevel, TimeAway
from patas_backend.models.matchmaker_profile import (
    HousingType,
    MatchmakerProfile,
    MatchmakerProfileRepository,
)
from patas_backend.models.user import User

NOTE = "I have a garden and work from home."


def _person(user_id: UUID, name: str) -> User:
    return User.provision(id=user_id, name=name, email=f"{name.lower()}@example.com")


async def _give_a_profile(factory: Factory, user_id: UUID) -> None:
    async with factory.begin() as session:
        await MatchmakerProfileRepository(session).save(
            MatchmakerProfile(
                user_id=user_id,
                housing=HousingType.HOUSE_WITH_YARD,
                activity=EnergyLevel.HIGH,
                time_away=TimeAway.HALF_DAY,
                experience=ExperienceLevel.EXPERIENCED,
                has_children=True,
                has_dogs=True,
                has_cats=False,
            )
        )


async def _requests_for(engine: AsyncEngine, animal_id: UUID) -> int:
    async with engine.connect() as conn:
        return await conn.scalar(
            text(
                "SELECT count(*) FROM patas.adoption_applications"
                " WHERE animal_id = :animal_id"
            ),
            {"animal_id": animal_id},
        )


async def test_a_request_is_stored_open_with_the_owner_copied_from_the_animal(
    session_factory: Factory, world: World
) -> None:
    await _give_a_profile(session_factory, world.bruno)
    service = AdoptionService(session_factory, adoption_dispatcher())

    application = await service.request_to_adopt(
        _person(world.bruno, "Bruno"), world.rex, NOTE
    )

    assert application is not None
    async with session_factory() as session:
        stored = await AdoptionApplicationRepository(session).get_by_id(application.id)
        animal = await AnimalRepository(session).get_by_id(world.rex)
    assert stored is not None
    assert stored.status is ApplicationStatus.OPEN
    assert stored.owner_id == world.ana
    assert stored.applicant_id == world.bruno
    assert stored.applicant_note == NOTE
    # Asking does not reserve the animal: only the owner accepting does.
    assert animal is not None
    assert animal.adoption_status is AdoptionStatus.AVAILABLE


async def test_a_request_for_an_unknown_animal_returns_none(
    session_factory: Factory, world: World
) -> None:
    await _give_a_profile(session_factory, world.bruno)
    service = AdoptionService(session_factory, adoption_dispatcher())

    result = await service.request_to_adopt(
        _person(world.bruno, "Bruno"), UUID(int=0), NOTE
    )

    assert result is None


async def test_a_request_waiting_for_the_animal_lock_sees_an_unpublish_and_is_refused(
    engine: AsyncEngine, session_factory: Factory, world: World
) -> None:
    # ADR 0017: the animal is locked before its availability is checked. Checking
    # first would let this request slip in beside the unpublish and stay open on an
    # animal nobody can see.
    await _give_a_profile(session_factory, world.bruno)
    service = AdoptionService(session_factory, adoption_dispatcher())

    async with session_factory.begin() as holder:
        animals = AnimalRepository(holder)
        rex = await animals.get_for_update(world.rex)
        assert rex is not None
        pending = asyncio.ensure_future(
            service.request_to_adopt(_person(world.bruno, "Bruno"), world.rex, NOTE)
        )
        await until_blocked(engine, 1)
        rex.unpublish(by_user_id=world.ana)
        await animals.update(rex)

    with pytest.raises(AnimalNotAvailable):
        await asyncio.wait_for(pending, timeout=10)
    assert await _requests_for(engine, world.rex) == 0


async def test_the_same_person_asking_twice_at_once_gets_only_one_request(
    engine: AsyncEngine, session_factory: Factory, world: World
) -> None:
    await _give_a_profile(session_factory, world.bruno)
    service = AdoptionService(session_factory, adoption_dispatcher())
    bruno = _person(world.bruno, "Bruno")

    async with session_factory.begin() as holder:
        await AnimalRepository(holder).get_for_update(world.rex)
        both = asyncio.gather(
            service.request_to_adopt(bruno, world.rex, NOTE),
            service.request_to_adopt(bruno, world.rex, NOTE),
            return_exceptions=True,
        )
        await until_blocked(engine, 2)
    results = await asyncio.wait_for(both, timeout=10)

    failures = [r for r in results if isinstance(r, BaseException)]
    assert len(failures) == 1
    assert isinstance(failures[0], AlreadyRequested)
    assert await _requests_for(engine, world.rex) == 1


async def test_two_people_asking_at_once_both_get_a_request(
    engine: AsyncEngine, session_factory: Factory, world: World
) -> None:
    # Several open requests for one animal are allowed: the owner picks one later.
    await _give_a_profile(session_factory, world.bruno)
    await _give_a_profile(session_factory, world.carla)
    service = AdoptionService(session_factory, adoption_dispatcher())

    async with session_factory.begin() as holder:
        await AnimalRepository(holder).get_for_update(world.rex)
        both = asyncio.gather(
            service.request_to_adopt(_person(world.bruno, "Bruno"), world.rex, NOTE),
            service.request_to_adopt(_person(world.carla, "Carla"), world.rex, NOTE),
        )
        await until_blocked(engine, 2)
    await asyncio.wait_for(both, timeout=10)

    assert await _requests_for(engine, world.rex) == 2


async def test_the_active_request_is_found_for_its_applicant_only(
    session_factory: Factory, world: World
) -> None:
    await _give_a_profile(session_factory, world.bruno)
    service = AdoptionService(session_factory, adoption_dispatcher())
    bruno, carla = _person(world.bruno, "Bruno"), _person(world.carla, "Carla")
    asked = await service.request_to_adopt(bruno, world.rex, NOTE)

    found = await service.get_active_request(bruno, world.rex)
    not_hers = await service.get_active_request(carla, world.rex)

    assert asked is not None
    assert found is not None and found.id == asked.id
    assert not_hers is None
