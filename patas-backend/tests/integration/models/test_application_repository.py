import asyncio
from dataclasses import replace
from datetime import UTC, datetime
from typing import NamedTuple
from uuid import UUID, uuid4

import pytest
import pytest_asyncio
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

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
Factory = async_sessionmaker[AsyncSession]
NOW = datetime(2026, 11, 7, 12, 0, tzinfo=UTC)
SNAPSHOT = ProfileSnapshot(
    housing=HousingType.APARTMENT,
    activity=EnergyLevel.MODERATE,
    time_away=TimeAway.HALF_DAY,
    experience=ExperienceLevel.SOME,
    has_children=False,
    has_dogs=True,
    has_cats=False,
)


class World(NamedTuple):
    ana: UUID  # owns both animals
    bruno: UUID
    carla: UUID
    rex: UUID
    luna: UUID


@pytest_asyncio.fixture
async def world(session_factory: Factory) -> World:
    ana, bruno, carla = uuid4(), uuid4(), uuid4()
    async with session_factory.begin() as session:
        users = UserRepository(session)
        for user_id, name in ((ana, "Ana"), (bruno, "Bruno"), (carla, "Carla")):
            await users.ensure_exists(
                User.provision(
                    id=user_id, name=name, email=f"{name.lower()}@example.com"
                )
            )
        rex = Animal.publish(owner_id=ana, name="Rex", species=Species.DOG)
        luna = Animal.publish(owner_id=ana, name="Luna", species=Species.DOG)
        await AnimalRepository(session).add(rex)
        await AnimalRepository(session).add(luna)
    return World(ana, bruno, carla, rex.id, luna.id)


def _application(
    world: World, *, applicant: UUID, animal: UUID, status: S = S.OPEN
) -> AdoptionApplication:
    return AdoptionApplication(
        id=uuid4(),
        animal_id=animal,
        owner_id=world.ana,
        applicant_id=applicant,
        applicant_note="Hello",
        applicant_profile=SNAPSHOT,
        status=status,
    )


async def _save(factory: Factory, application: AdoptionApplication) -> None:
    async with factory.begin() as session:
        await AdoptionApplicationRepository(session).add(application)


async def _load(factory: Factory, application_id: UUID) -> AdoptionApplication | None:
    async with factory() as session:
        return await AdoptionApplicationRepository(session).get_by_id(application_id)


async def test_a_saved_application_loads_back_with_every_field(
    session_factory: Factory, world: World
) -> None:
    application = _application(world, applicant=world.bruno, animal=world.rex)
    await _save(session_factory, application)

    loaded = await _load(session_factory, application.id)

    assert loaded is not None
    # Filled in by the database.
    assert loaded.created_at is not None
    assert loaded.created_at.tzinfo is not None
    # Everything else, including the snapshot that went through jsonb.
    assert replace(loaded, created_at=None) == application


async def test_a_missing_application_is_none(session_factory: Factory) -> None:
    missing = uuid4()

    async with session_factory() as session:
        repo = AdoptionApplicationRepository(session)
        assert await repo.get_by_id(missing) is None
        assert await repo.get_for_update(missing) is None
        assert await repo.get_animal_id(missing) is None


async def test_an_update_persists_the_transition(
    session_factory: Factory, world: World
) -> None:
    application = _application(world, applicant=world.bruno, animal=world.rex)
    await _save(session_factory, application)

    async with session_factory.begin() as session:
        repo = AdoptionApplicationRepository(session)
        loaded = await repo.get_for_update(application.id)
        assert loaded is not None
        loaded.accept(world.ana, "Welcome")
        loaded.confirm_handover(world.ana, NOW)
        await repo.update(loaded)

    reloaded = await _load(session_factory, application.id)
    assert reloaded is not None
    assert reloaded.status is S.ACCEPTED
    assert reloaded.owner_note == "Welcome"
    assert reloaded.owner_confirmed_at == NOW
    assert reloaded.applicant_confirmed_at is None


async def test_an_update_leaves_the_request_itself_untouched(
    session_factory: Factory, world: World
) -> None:
    application = _application(world, applicant=world.bruno, animal=world.rex)
    await _save(session_factory, application)
    other_answers = replace(SNAPSHOT, has_cats=True)

    async with session_factory.begin() as session:
        repo = AdoptionApplicationRepository(session)
        loaded = await repo.get_for_update(application.id)
        assert loaded is not None
        loaded.applicant_note = "Changed"
        loaded.applicant_profile = other_answers
        await repo.update(loaded)

    reloaded = await _load(session_factory, application.id)
    assert reloaded is not None
    assert reloaded.applicant_note == "Hello"
    assert reloaded.applicant_profile == SNAPSHOT


async def test_get_animal_id_returns_the_animal_of_the_application(
    session_factory: Factory, world: World
) -> None:
    application = _application(world, applicant=world.bruno, animal=world.luna)
    await _save(session_factory, application)

    async with session_factory() as session:
        found = await AdoptionApplicationRepository(session).get_animal_id(
            application.id
        )

    assert found == world.luna


async def test_the_open_list_has_only_open_applications_of_that_animal(
    session_factory: Factory, world: World
) -> None:
    open_bruno = _application(world, applicant=world.bruno, animal=world.rex)
    open_carla = _application(world, applicant=world.carla, animal=world.rex)
    declined = _application(
        world, applicant=world.bruno, animal=world.rex, status=S.DECLINED
    )
    other_animal = _application(world, applicant=world.bruno, animal=world.luna)
    for application in (open_bruno, open_carla, declined, other_animal):
        await _save(session_factory, application)

    async with session_factory() as session:
        found = await AdoptionApplicationRepository(
            session
        ).list_open_for_animal_for_update(world.rex)

    assert {a.id for a in found} == {open_bruno.id, open_carla.id}


async def test_a_second_accepted_application_for_one_animal_is_refused(
    session_factory: Factory, world: World
) -> None:
    first = _application(
        world, applicant=world.bruno, animal=world.rex, status=S.ACCEPTED
    )
    second = _application(
        world, applicant=world.carla, animal=world.rex, status=S.ACCEPTED
    )
    await _save(session_factory, first)

    with pytest.raises(IntegrityError, match="one_accepted_per_animal"):
        await _save(session_factory, second)


LOCKING_READS = {
    "get_for_update": lambda repo, a: repo.get_for_update(a.id),
    "list_open_for_animal_for_update": lambda repo, a: (
        repo.list_open_for_animal_for_update(a.animal_id)
    ),
}


@pytest.mark.parametrize("read", LOCKING_READS.values(), ids=LOCKING_READS.keys())
async def test_a_locking_read_waits_until_the_other_transaction_ends(
    session_factory: Factory, world: World, read: object
) -> None:
    application = _application(world, applicant=world.bruno, animal=world.rex)
    await _save(session_factory, application)

    async with session_factory() as holder, session_factory() as contender:
        await read(AdoptionApplicationRepository(holder), application)  # type: ignore[operator]
        waiting = asyncio.create_task(
            read(AdoptionApplicationRepository(contender), application)  # type: ignore[operator]
        )
        done, _ = await asyncio.wait({waiting}, timeout=0.5)
        assert not done  # still waiting for the lock

        await holder.commit()  # releases it
        await asyncio.wait_for(waiting, timeout=5)


async def test_a_plain_read_does_not_wait_for_a_lock(
    session_factory: Factory, world: World
) -> None:
    application = _application(world, applicant=world.bruno, animal=world.rex)
    await _save(session_factory, application)

    async with session_factory() as holder, session_factory() as reader:
        await AdoptionApplicationRepository(holder).get_for_update(application.id)

        loaded = await asyncio.wait_for(
            AdoptionApplicationRepository(reader).get_by_id(application.id),
            timeout=5,
        )

    assert loaded is not None
