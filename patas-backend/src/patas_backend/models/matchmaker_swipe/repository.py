from typing import Any
from uuid import UUID

from sqlalchemy import Row, text
from sqlalchemy.ext.asyncio import AsyncSession

from patas_backend.models.matchmaker_swipe.swipe import (
    MatchmakerSwipe,
    SwipeDisposition,
)

_INSERT = text(
    """
    INSERT INTO patas.matchmaker_swipes (user_id, animal_id, disposition)
    VALUES (:user_id, :animal_id, CAST(:disposition AS patas.swipe_disposition))
    ON CONFLICT (user_id, animal_id) DO NOTHING
    """
)
_SELECT_BY_USER_AND_ANIMAL = text(
    """
    SELECT user_id, animal_id, disposition, created_at
    FROM patas.matchmaker_swipes
    WHERE user_id = :user_id AND animal_id = :animal_id
    """
)
_SELECT_BY_USER_AND_ANIMAL_FOR_UPDATE = text(
    _SELECT_BY_USER_AND_ANIMAL.text + " FOR UPDATE"
)
_UPDATE = text(
    """
    UPDATE patas.matchmaker_swipes
    SET disposition = CAST(:disposition AS patas.swipe_disposition)
    WHERE user_id = :user_id AND animal_id = :animal_id
    """
)


def _from_row(row: Row[Any]) -> MatchmakerSwipe:
    return MatchmakerSwipe(
        user_id=row.user_id,
        animal_id=row.animal_id,
        disposition=SwipeDisposition(row.disposition),
        created_at=row.created_at,
    )


class MatchmakerSwipeRepository:
    """Persistence for one user's swipe history. The caller owns the transaction."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, swipe: MatchmakerSwipe) -> bool:
        """Insert once; return False if this user already swiped on the animal."""
        result = await self._session.execute(
            _INSERT,
            {
                "user_id": swipe.user_id,
                "animal_id": swipe.animal_id,
                "disposition": swipe.disposition.value,
            },
        )
        return result.rowcount == 1

    async def get_for_update(
        self, user_id: UUID, animal_id: UUID
    ) -> MatchmakerSwipe | None:
        result = await self._session.execute(
            _SELECT_BY_USER_AND_ANIMAL_FOR_UPDATE,
            {"user_id": user_id, "animal_id": animal_id},
        )
        row = result.first()
        return _from_row(row) if row is not None else None

    async def update(self, swipe: MatchmakerSwipe) -> None:
        await self._session.execute(
            _UPDATE,
            {
                "user_id": swipe.user_id,
                "animal_id": swipe.animal_id,
                "disposition": swipe.disposition.value,
            },
        )
