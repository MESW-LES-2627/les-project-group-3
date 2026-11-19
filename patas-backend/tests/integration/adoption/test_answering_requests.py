"""Answering requests (US-16) when the owner's answers race, through the service and
the real database.

Each test holds the animal's row lock, lets both contenders run into it, and only
then releases it, so the contention is real, not hoped for (see test_adoption_races
for the same method with the use cases stood in for by `transition`).
"""

import asyncio

from adoption_factory import (
    Factory,
    World,
    adoption_dispatcher,
    load,
    load_animal,
    owner_of,
    persist_application,
    until_blocked,
)
from sqlalchemy.ext.asyncio import AsyncEngine

from patas_backend.models.adoption import ApplicationStatus
from patas_backend.models.animal import (
    AdoptionStatus,
    AnimalNotAvailable,
    AnimalRepository,
)
from patas_backend.services.adoption import AdoptionService

S = ApplicationStatus


async def test_two_accepts_for_one_animal_only_one_wins(
    engine: AsyncEngine, session_factory: Factory, world: World
) -> None:
    first = await persist_application(session_factory, world, applicant=world.bruno)
    second = await persist_application(session_factory, world, applicant=world.carla)
    service = AdoptionService(session_factory, adoption_dispatcher())
    owner = owner_of(world)

    async with session_factory.begin() as holder:
        await AnimalRepository(holder).get_for_update(world.rex)
        both = asyncio.gather(
            service.accept(owner, first.id, None),
            service.accept(owner, second.id, None),
            return_exceptions=True,
        )
        await until_blocked(engine, 2)
    results = await asyncio.wait_for(both, timeout=10)

    failures = [r for r in results if isinstance(r, BaseException)]
    assert len(failures) == 1
    # The typed error, not the generic one: the router turns it into a 409 with the
    # code animal_not_available.
    assert isinstance(failures[0], AnimalNotAvailable)
    animal = await load_animal(session_factory, world.rex)
    assert animal.adoption_status is AdoptionStatus.RESERVED
    # The loser was rolled back whole: it is still open.
    statuses = {
        (await load(session_factory, first.id)).status,
        (await load(session_factory, second.id)).status,
    }
    assert statuses == {S.ACCEPTED, S.OPEN}


async def test_a_decline_waiting_behind_an_accept_releases_the_animal(
    engine: AsyncEngine, session_factory: Factory, world: World
) -> None:
    # ADR 0017: the animal is locked first. A decline that read the request before the
    # accept committed would record was_accepted=False and leave Rex reserved for good,
    # with no request holding him.
    request = await persist_application(session_factory, world, applicant=world.bruno)
    service = AdoptionService(session_factory, adoption_dispatcher())
    owner = owner_of(world)

    async with session_factory.begin() as holder:
        await AnimalRepository(holder).get_for_update(world.rex)
        accept = asyncio.ensure_future(service.accept(owner, request.id, None))
        await until_blocked(engine, 1)
        decline = asyncio.ensure_future(service.decline(owner, request.id, None))
        await until_blocked(engine, 2)
    await asyncio.wait_for(asyncio.gather(accept, decline), timeout=10)

    assert (await load(session_factory, request.id)).status is S.DECLINED
    animal = await load_animal(session_factory, world.rex)
    assert animal.adoption_status is AdoptionStatus.AVAILABLE
