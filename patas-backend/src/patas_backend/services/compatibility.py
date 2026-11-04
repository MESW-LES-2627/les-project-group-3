from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from patas_backend.models.animal import AnimalRepository
from patas_backend.models.compatibility import (
    CompatibilityMode,
    CompatibilityResult,
    strategy_for,
)
from patas_backend.models.matchmaker_profile import MatchmakerProfileRepository
from patas_backend.models.user import User


class AnimalNotFound(Exception):
    """No published animal has this id."""


class OwnAnimal(Exception):
    """An owner cannot ask how well their own animal fits their home."""


class NoMatchmakerProfile(Exception):
    """The caller has not saved a Matchmaker profile yet."""


class CompatibilityService:
    """How well an animal fits the caller's home. Read-only: nothing is stored."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def assess(
        self, user: User, animal_id: UUID, mode: CompatibilityMode
    ) -> CompatibilityResult:
        # Read-only: a plain session, closed before any scoring happens.
        async with self._session_factory() as session:
            animal = await AnimalRepository(session).get_by_id(animal_id)
            if animal is None or not animal.is_published:
                raise AnimalNotFound(f"No animal {animal_id}")
            if animal.owner_id == user.id:
                raise OwnAnimal("This is your own animal")
            profile = await MatchmakerProfileRepository(session).get(user.id)

        if profile is None:
            raise NoMatchmakerProfile("No Matchmaker profile yet")
        return strategy_for(mode).evaluate(profile, animal.match_profile())
