"""A message and a decline at the same time (US-21), through the services and the
real database. Same method as test_handover_checklist_races: hold the animal's row
lock, let both contenders queue behind it in a known order, then release it."""

import asyncio

import pytest
from adoption_factory import (
    Factory,
    World,
    adoption_dispatcher,
    load,
    owner_of,
    persist_application,
    until_blocked,
)
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from patas_backend.models.adoption import ApplicationStatus, InvalidTransition
from patas_backend.models.animal import AnimalRepository
from patas_backend.models.user import User
from patas_backend.services.adoption import AdoptionService
from patas_backend.services.conversation import ConversationService

S = ApplicationStatus


def _bruno(world: World) -> User:
    return User.provision(id=world.bruno, name="Bruno", email="bruno@example.com")


async def _stored_count(engine: AsyncEngine) -> int:
    async with engine.connect() as conn:
        return await conn.scalar(text("SELECT count(*) FROM patas.messages")) or 0


async def test_a_message_queued_behind_a_decline_is_refused(
    engine: AsyncEngine, session_factory: Factory, world: World
) -> None:
    request = await persist_application(
        session_factory, world, applicant=world.bruno, status=S.ACCEPTED
    )
    adoption = AdoptionService(session_factory, adoption_dispatcher())
    conversation = ConversationService(session_factory, adoption_dispatcher())

    async with session_factory.begin() as holder:
        await AnimalRepository(holder).get_for_update(world.rex)
        decline = asyncio.ensure_future(
            adoption.decline(owner_of(world), request.id, None)
        )
        await until_blocked(engine, 1)
        post = asyncio.ensure_future(
            conversation.post(_bruno(world), request.id, "Still there?")
        )
        await until_blocked(engine, 2)
    await asyncio.wait_for(decline, timeout=10)

    with pytest.raises(InvalidTransition):
        await asyncio.wait_for(post, timeout=10)
    assert (await load(session_factory, request.id)).status is S.DECLINED
    assert await _stored_count(engine) == 0


async def test_a_message_ahead_of_a_decline_is_kept(
    engine: AsyncEngine, session_factory: Factory, world: World
) -> None:
    request = await persist_application(
        session_factory, world, applicant=world.bruno, status=S.ACCEPTED
    )
    adoption = AdoptionService(session_factory, adoption_dispatcher())
    conversation = ConversationService(session_factory, adoption_dispatcher())

    async with session_factory.begin() as holder:
        await AnimalRepository(holder).get_for_update(world.rex)
        post = asyncio.ensure_future(
            conversation.post(_bruno(world), request.id, "Still there?")
        )
        await until_blocked(engine, 1)
        decline = asyncio.ensure_future(
            adoption.decline(owner_of(world), request.id, None)
        )
        await until_blocked(engine, 2)
    await asyncio.wait_for(asyncio.gather(post, decline), timeout=10)

    assert (await load(session_factory, request.id)).status is S.DECLINED
    assert await _stored_count(engine) == 1
