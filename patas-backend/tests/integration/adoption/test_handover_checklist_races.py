"""Two people ticking the handover checklist at once (US-25), through the service and
the real database. Same method as test_answering_requests: hold the animal's row lock,
let both contenders run into it, then release it."""

import asyncio

from adoption_factory import (
    Factory,
    World,
    adoption_dispatcher,
    load,
    owner_of,
    persist_application,
    until_blocked,
)
from sqlalchemy.ext.asyncio import AsyncEngine

from patas_backend.models.adoption import ApplicationStatus, HandoverItem
from patas_backend.models.animal import AnimalRepository
from patas_backend.models.user import User
from patas_backend.services.adoption import AdoptionService

S = ApplicationStatus


def _bruno(world: World) -> User:
    return User.provision(id=world.bruno, name="Bruno", email="bruno@example.com")


async def test_two_ticks_at_once_both_stay(
    engine: AsyncEngine, session_factory: Factory, world: World
) -> None:
    # Without the lock, each side would save the list it loaded and the second save
    # would erase the first tick.
    request = await persist_application(
        session_factory, world, applicant=world.bruno, status=S.ACCEPTED
    )
    service = AdoptionService(session_factory, adoption_dispatcher())

    async with session_factory.begin() as holder:
        await AnimalRepository(holder).get_for_update(world.rex)
        both = asyncio.gather(
            service.set_handover_item(
                owner_of(world), request.id, HandoverItem.CARE_NOTES, True
            ),
            service.set_handover_item(
                _bruno(world), request.id, HandoverItem.VACCINATION_BOOKLET, True
            ),
        )
        await until_blocked(engine, 2)
    await asyncio.wait_for(both, timeout=10)

    stored = await load(session_factory, request.id)
    assert stored.handover_checked == {
        HandoverItem.CARE_NOTES,
        HandoverItem.VACCINATION_BOOKLET,
    }


async def test_a_tick_waiting_behind_the_confirmation_that_adopts_is_refused(
    engine: AsyncEngine, session_factory: Factory, world: World
) -> None:
    # Bruno already confirmed. Ana's confirmation adopts, and Bruno's tick queued
    # behind it must see the adoption, not slip in before it.
    request = await persist_application(
        session_factory,
        world,
        applicant=world.bruno,
        status=S.ACCEPTED,
        applicant_confirmed_at=None,
    )
    service = AdoptionService(session_factory, adoption_dispatcher())
    await service.confirm_handover(_bruno(world), request.id)

    async with session_factory.begin() as holder:
        await AnimalRepository(holder).get_for_update(world.rex)
        adopt = asyncio.ensure_future(
            service.confirm_handover(owner_of(world), request.id)
        )
        await until_blocked(engine, 1)
        tick = asyncio.ensure_future(
            service.set_handover_item(
                _bruno(world), request.id, HandoverItem.CARE_NOTES, True
            )
        )
        await until_blocked(engine, 2)
    results = await asyncio.wait_for(
        asyncio.gather(adopt, tick, return_exceptions=True), timeout=10
    )

    assert results[0] is not None  # the adopting confirmation went through
    assert isinstance(results[1], Exception)  # InvalidTransition: already adopted
    stored = await load(session_factory, request.id)
    assert stored.status is S.ADOPTED
    assert stored.handover_checked == frozenset()
