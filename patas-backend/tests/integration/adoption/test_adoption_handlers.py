import pytest
from adoption_factory import (
    LATER,
    NOW,
    Factory,
    World,
    adoption_dispatcher,
    load,
    load_animal,
    new_application,
    owner_of,
    save,
    set_animal_status,
    transition,
)

from patas_backend.models.adoption import ApplicationClosed, ApplicationStatus
from patas_backend.models.animal import (
    AdoptionStatus,
    AnimalUnpublished,
    InvalidAnimalTransition,
)
from patas_backend.models.events import DomainEvent
from patas_backend.services.animals import AnimalService

S = ApplicationStatus


async def test_accepting_reserves_the_animal(
    session_factory: Factory, world: World
) -> None:
    application = new_application(world, applicant=world.bruno)
    await save(session_factory, application)

    await transition(
        session_factory,
        adoption_dispatcher(),
        application.id,
        lambda a: a.accept(world.ana),
    )

    animal = await load_animal(session_factory, world.rex)
    assert animal.adoption_status is AdoptionStatus.RESERVED
    assert (await load(session_factory, application.id)).status is S.ACCEPTED


@pytest.mark.parametrize(("action", "who"), [("decline", "ana"), ("withdraw", "bruno")])
async def test_ending_an_accepted_application_releases_the_animal(
    session_factory: Factory, world: World, action: str, who: str
) -> None:
    application = new_application(world, applicant=world.bruno, status=S.ACCEPTED)
    await save(session_factory, application)
    await set_animal_status(session_factory, world.rex, AdoptionStatus.RESERVED)

    await transition(
        session_factory,
        adoption_dispatcher(),
        application.id,
        lambda a: getattr(a, action)(getattr(world, who)),
    )

    animal = await load_animal(session_factory, world.rex)
    assert animal.adoption_status is AdoptionStatus.AVAILABLE


@pytest.mark.parametrize(("action", "who"), [("decline", "ana"), ("withdraw", "bruno")])
async def test_ending_an_open_application_leaves_the_animal_alone(
    session_factory: Factory, world: World, action: str, who: str
) -> None:
    application = new_application(world, applicant=world.bruno)
    await save(session_factory, application)

    await transition(
        session_factory,
        adoption_dispatcher(),
        application.id,
        lambda a: getattr(a, action)(getattr(world, who)),
    )

    animal = await load_animal(session_factory, world.rex)
    assert animal.adoption_status is AdoptionStatus.AVAILABLE


async def test_the_second_confirmation_adopts_the_animal_and_closes_the_rest(
    session_factory: Factory, world: World
) -> None:
    accepted = new_application(
        world, applicant=world.bruno, status=S.ACCEPTED, owner_confirmed_at=NOW
    )
    waiting = new_application(world, applicant=world.carla)
    await save(session_factory, accepted, waiting)
    await set_animal_status(session_factory, world.rex, AdoptionStatus.RESERVED)

    await transition(
        session_factory,
        adoption_dispatcher(),
        accepted.id,
        lambda a: a.confirm_handover(world.bruno, LATER),
    )

    animal = await load_animal(session_factory, world.rex)
    assert animal.adoption_status is AdoptionStatus.ADOPTED
    assert (await load(session_factory, accepted.id)).status is S.ADOPTED
    assert (await load(session_factory, waiting.id)).status is S.CLOSED


async def test_accepting_while_the_animal_is_reserved_changes_nothing(
    session_factory: Factory, world: World
) -> None:
    accepted = new_application(world, applicant=world.bruno, status=S.ACCEPTED)
    waiting = new_application(world, applicant=world.carla)
    await save(session_factory, accepted, waiting)
    await set_animal_status(session_factory, world.rex, AdoptionStatus.RESERVED)
    dispatcher = adoption_dispatcher()
    published: list[DomainEvent] = []

    async def spy(event: DomainEvent) -> None:
        published.append(event)

    dispatcher.register_after_commit(DomainEvent, spy)

    with pytest.raises(InvalidAnimalTransition):
        await transition(
            session_factory,
            dispatcher,
            waiting.id,
            lambda a: a.accept(world.ana),
        )

    assert (await load(session_factory, waiting.id)).status is S.OPEN
    assert (await load(session_factory, accepted.id)).status is S.ACCEPTED
    assert published == []  # a rolled-back change is never announced


async def test_unpublishing_closes_only_the_open_requests_of_that_animal(
    session_factory: Factory, world: World
) -> None:
    from_bruno = new_application(world, applicant=world.bruno)
    from_carla = new_application(world, applicant=world.carla)
    declined = new_application(world, applicant=world.bruno, status=S.DECLINED)
    for_luna = new_application(world, applicant=world.bruno, animal=world.luna)
    await save(session_factory, from_bruno, from_carla, declined, for_luna)
    service = AnimalService(session_factory, adoption_dispatcher())

    await service.unpublish(owner_of(world), world.rex)

    statuses = {
        name: (await load(session_factory, application.id)).status
        for name, application in {
            "bruno": from_bruno,
            "carla": from_carla,
            "declined": declined,
            "luna": for_luna,
        }.items()
    }
    assert statuses == {
        "bruno": S.CLOSED,
        "carla": S.CLOSED,
        "declined": S.DECLINED,
        "luna": S.OPEN,
    }


async def test_closes_made_by_a_handler_reach_the_subscribers(
    session_factory: Factory, world: World
) -> None:
    first = new_application(world, applicant=world.bruno)
    second = new_application(world, applicant=world.carla)
    await save(session_factory, first, second)
    dispatcher = adoption_dispatcher()
    subscribed: list[DomainEvent] = []

    async def subscriber(event: DomainEvent, session: object) -> list[DomainEvent]:
        subscribed.append(event)
        return []

    dispatcher.register(ApplicationClosed, subscriber)

    async with session_factory.begin() as session:
        handled = await dispatcher.dispatch(
            [AnimalUnpublished(animal_id=world.rex)], session
        )

    closed = {e.application_id for e in handled if isinstance(e, ApplicationClosed)}
    assert closed == {first.id, second.id}
    assert {e.application_id for e in subscribed} == closed


async def test_after_commit_handlers_see_the_committed_state(
    session_factory: Factory, world: World
) -> None:
    application = new_application(world, applicant=world.bruno)
    await save(session_factory, application)
    dispatcher = adoption_dispatcher()
    seen: list[ApplicationStatus] = []

    async def read_in_a_fresh_session(event: ApplicationClosed) -> None:
        seen.append((await load(session_factory, event.application_id)).status)

    dispatcher.register_after_commit(ApplicationClosed, read_in_a_fresh_session)

    await AnimalService(session_factory, dispatcher).unpublish(
        owner_of(world), world.rex
    )

    assert seen == [S.CLOSED]
