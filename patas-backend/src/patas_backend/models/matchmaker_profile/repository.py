from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from patas_backend.models.matching import EnergyLevel, ExperienceLevel
from patas_backend.models.matchmaker_profile.matchmaker_profile import (
    HousingType,
    MatchmakerProfile,
    TimeAway,
)

_UPSERT = text(
    """
    INSERT INTO patas.matchmaker_profiles
        (user_id, housing, activity, time_away, experience,
         has_children, has_dogs, has_cats)
    VALUES (
        :user_id, CAST(:housing AS patas.housing_type),
        CAST(:activity AS patas.energy_level), CAST(:time_away AS patas.time_away),
        CAST(:experience AS patas.experience_level),
        :has_children, :has_dogs, :has_cats
    )
    ON CONFLICT (user_id) DO UPDATE SET
        housing = EXCLUDED.housing,
        activity = EXCLUDED.activity,
        time_away = EXCLUDED.time_away,
        experience = EXCLUDED.experience,
        has_children = EXCLUDED.has_children,
        has_dogs = EXCLUDED.has_dogs,
        has_cats = EXCLUDED.has_cats
    """
)
_SELECT = text(
    """
    SELECT user_id, housing, activity, time_away, experience,
           has_children, has_dogs, has_cats
    FROM patas.matchmaker_profiles
    WHERE user_id = :user_id
    """
)


class MatchmakerProfileRepository:
    """Persistence for MatchmakerProfile. The caller owns the transaction.

    This never commits.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, profile: MatchmakerProfile) -> None:
        """Create the user's profile or replace its answers.

        A single INSERT ... ON CONFLICT is atomic, so two saves at once cannot
        create two rows. The update fires the trigger that refreshes updated_at.
        """
        await self._session.execute(
            _UPSERT,
            {
                "user_id": profile.user_id,
                "housing": profile.housing.value,
                "activity": profile.activity.value,
                "time_away": profile.time_away.value,
                "experience": profile.experience.value,
                "has_children": profile.has_children,
                "has_dogs": profile.has_dogs,
                "has_cats": profile.has_cats,
            },
        )

    async def get(self, user_id: UUID) -> MatchmakerProfile | None:
        """The user's own profile, or None if they have not saved one."""
        row = (await self._session.execute(_SELECT, {"user_id": user_id})).one_or_none()
        if row is None:
            return None
        return MatchmakerProfile(
            user_id=row.user_id,
            housing=HousingType(row.housing),
            activity=EnergyLevel(row.activity),
            time_away=TimeAway(row.time_away),
            experience=ExperienceLevel(row.experience),
            has_children=row.has_children,
            has_dogs=row.has_dogs,
            has_cats=row.has_cats,
        )
