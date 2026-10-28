from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID

from patas_backend.models.matching import EnergyLevel, ExperienceLevel, TimeAway


class InvalidMatchmakerProfile(ValueError):
    """A MatchmakerProfile invariant was violated."""


class HousingType(StrEnum):
    APARTMENT = "apartment"
    HOUSE_NO_YARD = "house_no_yard"
    HOUSE_WITH_YARD = "house_with_yard"


def _choice[E: StrEnum](scale: type[E], field: str, value: object) -> E:
    try:
        return scale(value)
    except ValueError:
        allowed = ", ".join(member.value for member in scale)
        raise InvalidMatchmakerProfile(f"{field} must be one of: {allowed}") from None


def _yes_or_no(field: str, value: object) -> bool:
    # Only a real bool: a truthy string such as "no" must not become True.
    if not isinstance(value, bool):
        raise InvalidMatchmakerProfile(f"{field} must be yes or no")
    return value


@dataclass
class MatchmakerProfile:
    """A user's saved answers. One per user, so the user is its identity."""

    user_id: UUID
    housing: HousingType
    activity: EnergyLevel
    time_away: TimeAway
    experience: ExperienceLevel
    has_children: bool
    has_dogs: bool
    has_cats: bool

    def __post_init__(self) -> None:
        # Invariants hold however a profile is built (saved by the user or loaded
        # from the DB). Every answer is required: there is no partial profile.
        self.housing = _choice(HousingType, "housing", self.housing)
        self.activity = _choice(EnergyLevel, "activity", self.activity)
        self.time_away = _choice(TimeAway, "time_away", self.time_away)
        self.experience = _choice(ExperienceLevel, "experience", self.experience)
        self.has_children = _yes_or_no("has_children", self.has_children)
        self.has_dogs = _yes_or_no("has_dogs", self.has_dogs)
        self.has_cats = _yes_or_no("has_cats", self.has_cats)
