"""Test support for the adoption use cases: seed people, animals and applications,
and stand in for the use cases the stories will write.

`transition` does what every adoption use case will do: lock the animal and then
the application, apply the change, dispatch the events inside the transaction, save,
and publish after the commit.
"""

import asyncio
from collections.abc import Callable
from datetime import UTC, datetime
from typing import NamedTuple
from uuid import UUID, uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from patas_backend.models.adoption import (
    AdoptionApplication,
    AdoptionApplicationRepository,
    ApplicationStatus,
    ProfileSnapshot,
)
from patas_backend.models.animal import (
    AdoptionStatus,
    Animal,
    AnimalRepository,
    Species,
)
from patas_backend.models.matching import EnergyLevel, ExperienceLevel, TimeAway
from patas_backend.models.matchmaker_profile import HousingType
from patas_backend.models.user import User, UserRepository
from patas_backend.services.adoption_handlers import register_adoption_handlers
from patas_backend.services.events import EventDispatcher
from patas_backend.services.locking import lock_animal_and_application

Factory = async_sessionmaker[AsyncSession]
NOW = datetime(2026, 11, 7, 12, 0, tzinfo=UTC)
LATER = datetime(2026, 11, 8, 9, 30, tzinfo=UTC)
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


async def seed_world(factory: Factory) -> World:
    ana, bruno, carla = uuid4(), uuid4(), uuid4()
    async with factory.begin() as session:
        users = UserRepository(session)
        for user_id, name in ((ana, "Ana"), (bruno, "Bruno"), (carla, "Carla")):
            email = f"{name.lower()}@example.com"
            await users.ensure_exists(
                User.provision(id=user_id, name=name, email=email)
            )
        rex = Animal.publish(owner_id=ana, name="Rex", species=Species.DOG)
        luna = Animal.publish(owner_id=ana, name="Luna", species=Species.DOG)
        await AnimalRepository(session).add(rex)
        await AnimalRepository(session).add(luna)
    return World(ana, bruno, carla, rex.id, luna.id)


def owner_of(world: World) -> User:
    return User.provision(id=world.ana, name="Ana", email="ana@example.com")


def adoption_dispatcher() -> EventDispatcher:
    dispatcher = EventDispatcher()
    register_adoption_handlers(dispatcher)
    return dispatcher


def new_application(
    world: World,
    *,
    applicant: UUID,
    animal: UUID | None = None,
    status: ApplicationStatus = ApplicationStatus.OPEN,
    **fields: object,
) -> AdoptionApplication:
    return AdoptionApplication(
        id=uuid4(),
        animal_id=animal or world.rex,
        owner_id=world.ana,
        applicant_id=applicant,
        applicant_note="Hello",
        applicant_profile=SNAPSHOT,
        status=status,
        **fields,
    )


# The animal's status that goes with an application: an accepted one reserves it, an
# adopted one means the animal went home. Every other status leaves it available.
_ANIMAL_STATUS_FOR = {
    ApplicationStatus.ACCEPTED: AdoptionStatus.RESERVED,
    ApplicationStatus.ADOPTED: AdoptionStatus.ADOPTED,
}


async def persist_application(
    factory: Factory,
    world: World,
    *,
    applicant: UUID,
    animal: UUID | None = None,
    status: ApplicationStatus = ApplicationStatus.OPEN,
    **fields: object,
) -> AdoptionApplication:
    """Save an application in any status, with its animal in the matching status.

    An adopted one gets both handover confirmations unless given, which the
    database requires. This is where a story's tests start from a known state.
    """
    if status is ApplicationStatus.ADOPTED:
        fields.setdefault("owner_confirmed_at", NOW)
        fields.setdefault("applicant_confirmed_at", NOW)
    application = new_application(
        world, applicant=applicant, animal=animal, status=status, **fields
    )
    await save(factory, application)
    if status in _ANIMAL_STATUS_FOR:
        await set_animal_status(
            factory, application.animal_id, _ANIMAL_STATUS_FOR[status]
        )
    return application


async def save(factory: Factory, *applications: AdoptionApplication) -> None:
    async with factory.begin() as session:
        for application in applications:
            await AdoptionApplicationRepository(session).add(application)


async def load(factory: Factory, application_id: UUID) -> AdoptionApplication:
    async with factory() as session:
        found = await AdoptionApplicationRepository(session).get_by_id(application_id)
    assert found is not None
    return found


async def load_animal(factory: Factory, animal_id: UUID) -> Animal:
    async with factory() as session:
        found = await AnimalRepository(session).get_by_id(animal_id)
    assert found is not None
    return found


async def set_animal_status(
    factory: Factory, animal_id: UUID, status: AdoptionStatus
) -> None:
    async with factory.begin() as session:
        await session.execute(
            text(
                "UPDATE patas.animals "
                "SET adoption_status = CAST(:status AS patas.adoption_status) "
                "WHERE id = :id"
            ),
            {"id": animal_id, "status": status.value},
        )


async def transition(
    factory: Factory,
    dispatcher: EventDispatcher,
    application_id: UUID,
    change: Callable[[AdoptionApplication], None],
) -> None:
    async with factory.begin() as session:
        locked = await lock_animal_and_application(session, application_id)
        assert locked is not None
        _, application = locked
        change(application)
        events = await dispatcher.dispatch(application.pull_events(), session)
        await AdoptionApplicationRepository(session).update(application)
    await dispatcher.publish(events)


async def until_blocked(engine: AsyncEngine, count: int) -> None:
    """Wait until `count` connections are waiting for a lock: the contenders met.

    Waiters queue up, so the second is blocked by the first, not by the holder:
    count every waiting connection, not only those the holder blocks directly.
    """
    query = text(
        "SELECT count(*) FROM pg_stat_activity"
        " WHERE datname = current_database()"
        " AND cardinality(pg_blocking_pids(pid)) > 0"
    )
    # Autocommit, so each probe sees connections opened since the last one.
    async with engine.connect() as conn:
        conn = await conn.execution_options(isolation_level="AUTOCOMMIT")
        for _ in range(100):
            if await conn.scalar(query) >= count:
                return
            await asyncio.sleep(0.05)
        activity = await conn.execute(
            text(
                "SELECT pid, state, wait_event_type, pg_blocking_pids(pid) AS "
                "blocked_by, left(query, 70) AS query FROM pg_stat_activity "
                "WHERE datname = current_database() ORDER BY pid"
            )
        )
        snapshot = "\n".join(str(tuple(row)) for row in activity)
    pytest.fail(f"fewer than {count} requests waited for a lock:\n{snapshot}")
