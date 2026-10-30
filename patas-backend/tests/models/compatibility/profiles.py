from uuid import UUID

from patas_backend.models.animal import AnimalMatchProfile, AnimalSize
from patas_backend.models.compatibility import CompatibilityResult
from patas_backend.models.matching import EnergyLevel, ExperienceLevel, TimeAway
from patas_backend.models.matchmaker_profile import HousingType, MatchmakerProfile

USER_ID = UUID("0b1f2a3c-4d5e-4f60-8a7b-9c0d1e2f3a4b")


def make_adopter(**overrides: object) -> MatchmakerProfile:
    """An adopter every lifestyle dimension of make_animal() fits in full, with no
    household. Each test overrides only the answers it is about."""
    answers: dict[str, object] = {
        "user_id": USER_ID,
        "housing": HousingType.HOUSE_WITH_YARD,
        "activity": EnergyLevel.MODERATE,
        "time_away": TimeAway.FEW_HOURS,
        "experience": ExperienceLevel.NONE,
        "has_children": False,
        "has_dogs": False,
        "has_cats": False,
        **overrides,
    }
    return MatchmakerProfile(**answers)  # type: ignore[arg-type]


def make_animal(**overrides: object) -> AnimalMatchProfile:
    """An animal that fits make_adopter() in full on every lifestyle dimension."""
    answers: dict[str, object] = {
        "activity": EnergyLevel.MODERATE,
        "max_time_alone": TimeAway.FEW_HOURS,
        "experience_needed": ExperienceLevel.NONE,
        "space_needed": AnimalSize.SMALL,
        **overrides,
    }
    return AnimalMatchProfile(**answers)  # type: ignore[arg-type]


def texts(result: CompatibilityResult) -> tuple[str, ...]:
    return tuple(reason.text for reason in result.reasons)
