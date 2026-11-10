from collections.abc import Mapping
from dataclasses import dataclass

from patas_backend.models.matching import EnergyLevel, ExperienceLevel, TimeAway
from patas_backend.models.matchmaker_profile import HousingType, MatchmakerProfile


@dataclass(frozen=True)
class ProfileSnapshot:
    """A copy of a Matchmaker profile's answers, kept with one application.

    The owner sees what the applicant declared when asking, even if the applicant
    later edits or deletes their profile.
    """

    housing: HousingType
    activity: EnergyLevel
    time_away: TimeAway
    experience: ExperienceLevel
    has_children: bool
    has_dogs: bool
    has_cats: bool

    @classmethod
    def of(cls, profile: MatchmakerProfile) -> "ProfileSnapshot":
        return cls(
            housing=profile.housing,
            activity=profile.activity,
            time_away=profile.time_away,
            experience=profile.experience,
            has_children=profile.has_children,
            has_dogs=profile.has_dogs,
            has_cats=profile.has_cats,
        )

    def to_json(self) -> dict[str, str | bool]:
        """The plain values stored in the database's jsonb column."""
        return {
            "housing": self.housing.value,
            "activity": self.activity.value,
            "time_away": self.time_away.value,
            "experience": self.experience.value,
            "has_children": self.has_children,
            "has_dogs": self.has_dogs,
            "has_cats": self.has_cats,
        }

    @classmethod
    def from_json(cls, data: Mapping[str, object]) -> "ProfileSnapshot":
        return cls(
            housing=HousingType(data["housing"]),
            activity=EnergyLevel(data["activity"]),
            time_away=TimeAway(data["time_away"]),
            experience=ExperienceLevel(data["experience"]),
            has_children=bool(data["has_children"]),
            has_dogs=bool(data["has_dogs"]),
            has_cats=bool(data["has_cats"]),
        )
