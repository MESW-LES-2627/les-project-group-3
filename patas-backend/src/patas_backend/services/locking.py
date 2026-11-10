from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from patas_backend.models.adoption import (
    AdoptionApplication,
    AdoptionApplicationRepository,
)
from patas_backend.models.animal import AnimalRepository


async def lock_animal_and_application(
    session: AsyncSession, application_id: UUID
) -> AdoptionApplication | None:
    """Lock an application and its animal, the animal first, and return the application.

    Every adoption use case must take its locks in this order. Unpublishing locks the
    animal and then its applications, so a use case that locked an application first
    could deadlock against it. Returns None if the application does not exist.

    The animal is locked but deliberately not returned. The handlers load and save
    their own copy of it, so an animal kept here and saved after dispatching would
    silently revert what a handler did.
    """
    applications = AdoptionApplicationRepository(session)
    # An application never changes animal, so this unlocked read stays valid.
    animal_id = await applications.get_animal_id(application_id)
    if animal_id is None:
        return None
    await AnimalRepository(session).get_for_update(animal_id)
    return await applications.get_for_update(application_id)
