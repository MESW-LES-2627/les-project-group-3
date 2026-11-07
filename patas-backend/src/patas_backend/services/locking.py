from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from patas_backend.models.adoption import (
    AdoptionApplication,
    AdoptionApplicationRepository,
)
from patas_backend.models.animal import Animal, AnimalRepository


async def lock_animal_and_application(
    session: AsyncSession, application_id: UUID
) -> tuple[Animal, AdoptionApplication] | None:
    """Lock an application and its animal, the animal first.

    Every adoption use case must take its locks in this order. Unpublishing locks the
    animal and then its applications, so a use case that locked an application first
    could deadlock against it. Returns None if the application does not exist.
    """
    applications = AdoptionApplicationRepository(session)
    # An application never changes animal, so this unlocked read stays valid.
    animal_id = await applications.get_animal_id(application_id)
    if animal_id is None:
        return None
    animal = await AnimalRepository(session).get_for_update(animal_id)
    application = await applications.get_for_update(application_id)
    if animal is None or application is None:
        return None
    return animal, application
