"""The lock order (the animal first, then its applications) is what keeps these
races consistent. Each test holds the animal's row lock, lets both contenders run
into it, and only then releases it, so the contention is real, not hoped for.
"""

import asyncio

from adoption_factory import (
    Factory,
    World,
    adoption_dispatcher,
    load,
    load_animal,
    new_application,
    owner_of,
    save,
    transition,
    until_blocked,
)
from sqlalchemy.ext.asyncio import AsyncEngine

from patas_backend.models.adoption import ApplicationStatus, InvalidTransition
from patas_backend.models.animal import (
    AdoptionStatus,
    AnimalRepository,
    InvalidAnimalTransition,
)
from patas_backend.services.animals import AnimalService

S = ApplicationStatus


async def test_two_accepts_for_one_animal_only_one_wins(
    engine: AsyncEngine, session_factory: Factory, world: World
) -> None:
    first = new_application(world, applicant=world.bruno)
    second = new_application(world, applicant=world.carla)
    await save(session_factory, first, second)
    dispatcher = adoption_dispatcher()

    async with session_factory.begin() as holder:
        await AnimalRepository(holder).get_for_update(world.rex)
        both = asyncio.gather(
            transition(
                session_factory, dispatcher, first.id, lambda a: a.accept(world.ana)
            ),
            transition(
                session_factory, dispatcher, second.id, lambda a: a.accept(world.ana)
            ),
            return_exceptions=True,
        )
        await until_blocked(engine, 2)
    results = await asyncio.wait_for(both, timeout=10)

    failures = [r for r in results if isinstance(r, BaseException)]
    assert len(failures) == 1
    assert isinstance(failures[0], InvalidAnimalTransition)
    animal = await load_animal(session_factory, world.rex)
    assert animal.adoption_status is AdoptionStatus.RESERVED
    statuses = {
        (await load(session_factory, first.id)).status,
        (await load(session_factory, second.id)).status,
    }
    assert statuses == {S.ACCEPTED, S.OPEN}


async def test_an_unpublish_racing_an_accept_ends_consistent(
    engine: AsyncEngine, session_factory: Factory, world: World
) -> None:
    application = new_application(world, applicant=world.bruno)
    await save(session_factory, application)
    dispatcher = adoption_dispatcher()
    service = AnimalService(session_factory, dispatcher)

    async with session_factory.begin() as holder:
        await AnimalRepository(holder).get_for_update(world.rex)
        both = asyncio.gather(
            transition(
                session_factory,
                dispatcher,
                application.id,
                lambda a: a.accept(world.ana),
            ),
            service.unpublish(owner_of(world), world.rex),
            return_exceptions=True,
        )
        await until_blocked(engine, 2)
    results = await asyncio.wait_for(both, timeout=10)

    # Whoever got the animal first wins; the other is refused by a domain rule. A
    # deadlock would instead surface here as a database error (or a timeout above).
    failures = [r for r in results if isinstance(r, BaseException)]
    assert len(failures) == 1
    assert isinstance(failures[0], InvalidAnimalTransition | InvalidTransition)
    animal = await load_animal(session_factory, world.rex)
    final = (
        animal.adoption_status,
        (await load(session_factory, application.id)).status,
    )
    assert final in {
        (AdoptionStatus.RESERVED, S.ACCEPTED),
        (AdoptionStatus.UNAVAILABLE, S.CLOSED),
    }
