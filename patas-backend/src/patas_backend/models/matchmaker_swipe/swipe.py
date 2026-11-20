from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID


class SwipeDisposition(StrEnum):
    PASSED = "passed"
    SAVED = "saved"


class SwipeNotSaved(Exception):
    """The swipe is not currently saved."""


@dataclass
class MatchmakerSwipe:
    """One user's permanent decision about one animal."""

    user_id: UUID
    animal_id: UUID
    disposition: SwipeDisposition
    created_at: datetime | None = None

    def remove_from_saved(self) -> None:
        """Remove a saved animal without making it eligible for another swipe."""
        if self.disposition is not SwipeDisposition.SAVED:
            raise SwipeNotSaved("This animal is not in your saved list")
        self.disposition = SwipeDisposition.PASSED
