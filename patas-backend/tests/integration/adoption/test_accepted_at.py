"""US-21: a request remembers when it was accepted, because that is when its
conversation opens. Through the service and the real database."""

import pytest
from adoption_factory import (
    NOW,
    Factory,
    World,
    adoption_dispatcher,
    load,
    new_application,
    owner_of,
    persist_application,
    save,
)
from sqlalchemy.exc import IntegrityError

from patas_backend.models.adoption import (
    AdoptionApplicationRepository,
    ApplicationStatus,
)
from patas_backend.services.adoption import AdoptionService

S = ApplicationStatus


async def test_accepting_stores_when(session_factory: Factory, world: World) -> None:
    request = await persist_application(session_factory, world, applicant=world.bruno)
    service = AdoptionService(session_factory, adoption_dispatcher())

    await service.accept(owner_of(world), request.id, None)

    stored = await load(session_factory, request.id)
    assert stored.accepted_at is not None
    assert stored.has_conversation


async def test_declining_an_open_request_leaves_no_conversation(
    session_factory: Factory, world: World
) -> None:
    request = await persist_application(session_factory, world, applicant=world.bruno)
    service = AdoptionService(session_factory, adoption_dispatcher())

    await service.decline(owner_of(world), request.id, None)

    assert not (await load(session_factory, request.id)).has_conversation


async def test_both_lists_carry_when_it_was_accepted(
    session_factory: Factory, world: World
) -> None:
    await persist_application(
        session_factory, world, applicant=world.bruno, status=S.ACCEPTED
    )
    await persist_application(
        session_factory, world, applicant=world.carla, animal=world.luna
    )

    async with session_factory() as session:
        repository = AdoptionApplicationRepository(session)
        (sent,) = await repository.list_sent_by(world.bruno)
        received = await repository.list_received_by(world.ana)

    assert sent.accepted_at == NOW
    by_applicant = {r.applicant_id: r.accepted_at for r in received}
    assert by_applicant == {world.bruno: NOW, world.carla: None}


@pytest.mark.parametrize("status", [S.ACCEPTED, S.ADOPTED])
async def test_the_database_refuses_an_accepted_request_without_the_time(
    session_factory: Factory, world: World, status: S
) -> None:
    request = new_application(
        world,
        applicant=world.bruno,
        status=status,
        accepted_at=None,
        owner_confirmed_at=NOW,
        applicant_confirmed_at=NOW,
    )
    with pytest.raises(IntegrityError):
        await save(session_factory, request)


@pytest.mark.parametrize("status", [S.OPEN, S.CLOSED])
async def test_the_database_refuses_the_time_on_a_never_accepted_request(
    session_factory: Factory, world: World, status: S
) -> None:
    request = new_application(
        world, applicant=world.bruno, status=status, accepted_at=NOW
    )
    with pytest.raises(IntegrityError):
        await save(session_factory, request)
