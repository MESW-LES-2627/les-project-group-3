"""Seeing and withdrawing my requests (US-17), through the service and the real
database."""

import asyncio
from uuid import UUID

import pytest
from adoption_factory import (
    Factory,
    World,
    adoption_dispatcher,
    load,
    load_animal,
    persist_application,
    transition,
    until_blocked,
)
from sqlalchemy.ext.asyncio import AsyncEngine

from patas_backend.models.adoption import ApplicationStatus, InvalidTransition
from patas_backend.models.animal import AdoptionStatus, AnimalRepository
from patas_backend.models.user import User
from patas_backend.services.adoption import AdoptionService

S = ApplicationStatus
ENDED = [S.DECLINED, S.WITHDRAWN, S.CLOSED, S.ADOPTED]


def _person(user_id: UUID, name: str) -> User:
    return User.provision(id=user_id, name=name, email=f"{name.lower()}@example.com")


def _service(factory: Factory) -> AdoptionService:
    return AdoptionService(factory, adoption_dispatcher())


async def test_the_list_has_only_the_applicants_requests_newest_first(
    session_factory: Factory, world: World
) -> None:
    # Each persist_application is its own transaction, so created_at increases.
    older = await persist_application(session_factory, world, applicant=world.bruno)
    newer = await persist_application(
        session_factory, world, applicant=world.bruno, animal=world.luna
    )
    await persist_application(session_factory, world, applicant=world.carla)

    listed = await _service(session_factory).list_my_requests(
        _person(world.bruno, "Bruno")
    )

    assert [(r.id, r.animal_name) for r in listed] == [
        (newer.id, "Luna"),
        (older.id, "Rex"),
    ]


async def test_the_owner_sees_requests_for_all_her_animals_in_any_status(
    session_factory: Factory, world: World
) -> None:
    # Each persist_application is its own transaction, so created_at increases.
    older = await persist_application(
        session_factory, world, applicant=world.bruno, status=S.DECLINED
    )
    newer = await persist_application(
        session_factory, world, applicant=world.carla, animal=world.luna
    )

    listed = await _service(session_factory).list_received_requests(
        _person(world.ana, "Ana")
    )

    assert [(r.id, r.animal_name, r.applicant_id, r.status) for r in listed] == [
        (newer.id, "Luna", world.carla, S.OPEN),
        (older.id, "Rex", world.bruno, S.DECLINED),
    ]


async def test_a_person_who_owns_no_animal_receives_nothing(
    session_factory: Factory, world: World
) -> None:
    await persist_application(session_factory, world, applicant=world.bruno)

    listed = await _service(session_factory).list_received_requests(
        _person(world.carla, "Carla")
    )

    assert listed == []


async def test_the_list_keeps_requests_that_ended(
    session_factory: Factory, world: World
) -> None:
    for status in ENDED:
        await persist_application(
            session_factory, world, applicant=world.bruno, status=status
        )

    listed = await _service(session_factory).list_my_requests(
        _person(world.bruno, "Bruno")
    )

    assert sorted(r.status for r in listed) == sorted(ENDED)


async def test_withdrawing_an_unknown_request_returns_none(
    session_factory: Factory, world: World
) -> None:
    result = await _service(session_factory).withdraw(
        _person(world.bruno, "Bruno"), UUID(int=0)
    )

    assert result is None


async def test_withdrawing_someone_elses_request_returns_none_and_changes_nothing(
    session_factory: Factory, world: World
) -> None:
    request = await persist_application(session_factory, world, applicant=world.bruno)

    result = await _service(session_factory).withdraw(
        _person(world.carla, "Carla"), request.id
    )

    assert result is None
    assert (await load(session_factory, request.id)).status is S.OPEN


@pytest.mark.parametrize("status", ENDED)
async def test_withdrawing_a_request_that_ended_is_refused(
    status: ApplicationStatus, session_factory: Factory, world: World
) -> None:
    request = await persist_application(
        session_factory, world, applicant=world.bruno, status=status
    )

    with pytest.raises(InvalidTransition):
        await _service(session_factory).withdraw(
            _person(world.bruno, "Bruno"), request.id
        )
    assert (await load(session_factory, request.id)).status is status


async def test_a_withdraw_waiting_behind_an_accept_releases_the_animal(
    engine: AsyncEngine, session_factory: Factory, world: World
) -> None:
    # ADR 0017: the animal is locked first. A withdrawal that read the request before
    # the accept committed would record was_accepted=False and leave Rex reserved
    # for good, with no request holding him.
    request = await persist_application(session_factory, world, applicant=world.bruno)
    dispatcher = adoption_dispatcher()
    service = AdoptionService(session_factory, dispatcher)

    async with session_factory.begin() as holder:
        await AnimalRepository(holder).get_for_update(world.rex)
        accept = asyncio.ensure_future(
            transition(
                session_factory, dispatcher, request.id, lambda a: a.accept(world.ana)
            )
        )
        await until_blocked(engine, 1)
        withdraw = asyncio.ensure_future(
            service.withdraw(_person(world.bruno, "Bruno"), request.id)
        )
        await until_blocked(engine, 2)
    await asyncio.wait_for(asyncio.gather(accept, withdraw), timeout=10)

    assert (await load(session_factory, request.id)).status is S.WITHDRAWN
    animal = await load_animal(session_factory, world.rex)
    assert animal.adoption_status is AdoptionStatus.AVAILABLE
