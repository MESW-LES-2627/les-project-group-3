from collections.abc import Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING

from patas_backend.models.animal.enums import (
    AnimalCompatibility,
    AnimalSize,
    FirstTimeOwnerSuitability,
)
from patas_backend.models.matching.scales import (
    EnergyLevel,
    ExperienceLevel,
    LifeStage,
    TimeAway,
)

if TYPE_CHECKING:
    from patas_backend.models.animal.animal import Animal

# The owner's answers on the matching scales (ADR 0011). None means "not settled":
# a family with children is not excluded by it, and it is never read as a "no".
_MAX_TIME_ALONE = {
    EnergyLevel.LOW: TimeAway.FEW_HOURS,
    EnergyLevel.MODERATE: TimeAway.HALF_DAY,
    EnergyLevel.HIGH: TimeAway.MOST_OF_DAY,
}
_EXPERIENCE_NEEDED = {
    FirstTimeOwnerSuitability.YES: ExperienceLevel.NONE,
    FirstTimeOwnerSuitability.WITH_SUPPORT: ExperienceLevel.SOME,
    FirstTimeOwnerSuitability.NO: ExperienceLevel.EXPERIENCED,
    FirstTimeOwnerSuitability.UNKNOWN: None,
}
_SAFE_WITH = {
    AnimalCompatibility.YES: True,
    AnimalCompatibility.NO: False,
    AnimalCompatibility.WITH_SUPERVISION: None,
    AnimalCompatibility.UNKNOWN: None,
}


# Placeholder thresholds, a team rule (the same for dogs and cats): under a year is
# a baby, eight years and over is a senior.
_BABY_BELOW_MONTHS = 12
_SENIOR_FROM_MONTHS = 96


def _translate[K, V](table: Mapping[K, V | None], answer: K | None) -> V | None:
    return None if answer is None else table[answer]


def _life_stage(age_in_months: int | None) -> LifeStage | None:
    if age_in_months is None:
        return None
    if age_in_months < _BABY_BELOW_MONTHS:
        return LifeStage.BABY
    if age_in_months >= _SENIOR_FROM_MONTHS:
        return LifeStage.SENIOR
    return LifeStage.ADULT


@dataclass(frozen=True)
class AnimalMatchProfile:
    """An animal on the scales of a MatchmakerProfile, so the two can be compared.

    None means the owner did not say. It is never read as "no".
    """

    activity: EnergyLevel | None = None
    max_time_alone: TimeAway | None = None
    experience_needed: ExperienceLevel | None = None
    space_needed: AnimalSize | None = None
    safe_with_children: bool | None = None
    safe_with_dogs: bool | None = None
    safe_with_cats: bool | None = None
    # No adopter answer to pair with: a modifier for scoring, never used to guess
    # a blank space_needed.
    size: AnimalSize | None = None
    # Likewise unpaired: scoring reads each only against an adopter answer, as an
    # edge (training needs and age against experience, noise against housing).
    training_needs: EnergyLevel | None = None
    noise_level: EnergyLevel | None = None
    life_stage: LifeStage | None = None

    @classmethod
    def of(cls, animal: "Animal") -> "AnimalMatchProfile":
        return cls(
            activity=animal.activity_level,
            max_time_alone=_translate(_MAX_TIME_ALONE, animal.tolerance_for_time_alone),
            experience_needed=_translate(
                _EXPERIENCE_NEEDED, animal.suitable_for_first_time_owners
            ),
            space_needed=animal.space_requirement,
            safe_with_children=_translate(
                _SAFE_WITH, animal.behaves_well_with_children
            ),
            safe_with_dogs=_translate(_SAFE_WITH, animal.behaves_well_with_dogs),
            safe_with_cats=_translate(_SAFE_WITH, animal.behaves_well_with_cats),
            size=animal.size,
            training_needs=animal.training_needs,
            noise_level=animal.noise_level,
            life_stage=_life_stage(animal.age_in_months),
        )
