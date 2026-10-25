from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from patas_backend.models.matching import EnergyLevel, ExperienceLevel
from patas_backend.models.matchmaker_profile import (
    HousingType,
    MatchmakerProfile,
    MatchmakerProfileRepository,
    TimeAway,
)
from patas_backend.models.user import User


class MatchmakerProfileService:
    """Matchmaker profile use cases. Each one owns its transaction."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def get(self, user: User) -> MatchmakerProfile | None:
        """The user's own saved profile, or None. Read-only: a plain session."""
        async with self._session_factory() as session:
            return await MatchmakerProfileRepository(session).get(user.id)

    async def save(
        self,
        user: User,
        *,
        housing: HousingType,
        activity: EnergyLevel,
        time_away: TimeAway,
        experience: ExperienceLevel,
        has_children: bool,
        has_dogs: bool,
        has_cats: bool,
    ) -> MatchmakerProfile:
        """Create the user's profile or replace all of its answers."""
        # Built before the transaction opens: an invalid profile raises
        # InvalidMatchmakerProfile and nothing reaches the database.
        profile = MatchmakerProfile(
            user_id=user.id,
            housing=housing,
            activity=activity,
            time_away=time_away,
            experience=experience,
            has_children=has_children,
            has_dogs=has_dogs,
            has_cats=has_cats,
        )
        async with self._session_factory.begin() as session:
            await MatchmakerProfileRepository(session).save(profile)
        return profile

    async def delete(self, user: User) -> None:
        """Remove the user's own profile. Having none is not an error."""
        async with self._session_factory.begin() as session:
            await MatchmakerProfileRepository(session).delete(user.id)
