"""What changes together when an adoption event happens.

Every handler persists what it changes, and returns the events of the aggregates it
changed. The application that raised the event is left to the use case, which saves
it after dispatching.
"""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from patas_backend.models.adoption import (
    AdoptionApplicationRepository,
    ApplicationAccepted,
    ApplicationAdopted,
    ApplicationDeclined,
    ApplicationWithdrawn,
)
from patas_backend.models.animal import Animal, AnimalRepository, AnimalUnpublished
from patas_backend.models.events import DomainEvent
from patas_backend.services.events import EventDispatcher


async def _locked_animal(session: AsyncSession, animal_id: UUID) -> Animal:
    animal = await AnimalRepository(session).get_for_update(animal_id)
    if animal is None:
        # Unreachable: applications reference the animal and the foreign key
        # restricts deleting it.
        raise LookupError(f"animal {animal_id} no longer exists")
    return animal


async def _close_open_applications(
    session: AsyncSession, animal_id: UUID
) -> list[DomainEvent]:
    repository = AdoptionApplicationRepository(session)
    events: list[DomainEvent] = []
    for application in await repository.list_open_for_animal_for_update(animal_id):
        application.close()
        await repository.update(application)
        events.extend(application.pull_events())
    return events


async def reserve_animal(
    event: ApplicationAccepted, session: AsyncSession
) -> list[DomainEvent]:
    animal = await _locked_animal(session, event.animal_id)
    animal.reserve()
    await AnimalRepository(session).update(animal)
    return []


async def release_animal(
    event: ApplicationDeclined | ApplicationWithdrawn, session: AsyncSession
) -> list[DomainEvent]:
    # Only an accepted application had reserved the animal.
    if event.was_accepted:
        animal = await _locked_animal(session, event.animal_id)
        animal.release()
        await AnimalRepository(session).update(animal)
    return []


async def adopt_animal(
    event: ApplicationAdopted, session: AsyncSession
) -> list[DomainEvent]:
    animal = await _locked_animal(session, event.animal_id)
    animal.mark_adopted()
    await AnimalRepository(session).update(animal)
    return await _close_open_applications(session, event.animal_id)


async def close_open_applications(
    event: AnimalUnpublished, session: AsyncSession
) -> list[DomainEvent]:
    return await _close_open_applications(session, event.animal_id)


def register_adoption_handlers(dispatcher: EventDispatcher) -> None:
    dispatcher.register(ApplicationAccepted, reserve_animal)
    dispatcher.register(ApplicationDeclined, release_animal)
    dispatcher.register(ApplicationWithdrawn, release_animal)
    dispatcher.register(ApplicationAdopted, adopt_animal)
    dispatcher.register(AnimalUnpublished, close_open_applications)
