from collections.abc import Callable, Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from patas_backend.models.animal import AnimalMatchProfile, AnimalSize
from patas_backend.models.compatibility import tables
from patas_backend.models.compatibility.dimension import (
    Assessment,
    Dimension,
    Wording,
)
from patas_backend.models.compatibility.interaction import Interaction, Penalty
from patas_backend.models.matching import ExperienceLevel, LifeStage, TimeAway
from patas_backend.models.matchmaker_profile import MatchmakerProfile


def _household(
    name: str,
    noun: str,
    has: Callable[[MatchmakerProfile], bool],
    safe: Callable[[AnimalMatchProfile], bool | None],
) -> Dimension[bool, bool]:
    safe_with = f"Safe with {noun}"
    return Dimension(
        name=name,
        weight=2,
        critical=True,
        safety=True,
        adopter_value=lambda adopter: True if has(adopter) else None,
        animal_value=safe,
        table=tables.HOUSEHOLD,
        # The table only gives 1 or 0, so a partial fit cannot happen here.
        wording=Wording(
            fits=safe_with,
            partly=safe_with,
            misfit=f"Not safe with {noun}",
            unknown=f"The owner did not say if it is safe with {noun}",
        ),
    )


STANDARD_DIMENSIONS: tuple[Dimension[Any, Any], ...] = (
    Dimension(
        name="activity",
        weight=1,
        critical=False,
        safety=False,
        adopter_value=lambda adopter: adopter.activity,
        animal_value=lambda animal: animal.activity,
        table=tables.ACTIVITY,
        wording=Wording(
            fits="Matches your activity level",
            partly="Its energy is a bit different from yours",
            misfit="Its energy is very different from yours",
            unknown="The owner did not say how active it is",
        ),
    ),
    Dimension(
        name="time_alone",
        weight=1,
        critical=True,
        safety=False,
        adopter_value=lambda adopter: adopter.time_away,
        animal_value=lambda animal: animal.max_time_alone,
        table=tables.ceiling_table(TimeAway),
        wording=Wording(
            fits="Fine with the time you are away",
            partly="Would be alone longer than it is used to",
            misfit="Cannot be left alone for as long as you are away",
            unknown="The owner did not say how long it can be left alone",
        ),
    ),
    Dimension(
        name="experience",
        weight=1,
        critical=True,
        safety=False,
        adopter_value=lambda adopter: adopter.experience,
        animal_value=lambda animal: animal.experience_needed,
        table=tables.floor_table(ExperienceLevel),
        wording=Wording(
            fits="Suits your experience",
            partly="Needs a bit more experience than you have",
            misfit="Needs much more experience than you have",
            unknown="The owner did not say if it suits first-time owners",
        ),
    ),
    Dimension(
        name="space",
        weight=1,
        critical=True,
        safety=False,
        adopter_value=lambda adopter: adopter.space_offered,
        animal_value=lambda animal: animal.space_needed,
        table=tables.floor_table(AnimalSize),
        wording=Wording(
            fits="Your home gives it enough space",
            partly="Needs more space than your home offers",
            misfit="Needs far more space than your home offers",
            unknown="The owner did not say how much space it needs",
        ),
    ),
    _household(
        "children",
        "children",
        lambda adopter: adopter.has_children,
        lambda animal: animal.safe_with_children,
    ),
    _household(
        "dogs",
        "dogs",
        lambda adopter: adopter.has_dogs,
        lambda animal: animal.safe_with_dogs,
    ),
    _household(
        "cats",
        "cats",
        lambda adopter: adopter.has_cats,
        lambda animal: animal.safe_with_cats,
    ),
)


def _unit(value: StrEnum) -> float:
    """Where a value sits on its scale: 0 for the first, 1 for the last."""
    scale = list(type(value))
    return scale.index(value) / (len(scale) - 1)


# An edge never fires on a blank animal answer: it punishes a known problem only.
def _training_beyond_experience(
    adopter: MatchmakerProfile, animal: AnimalMatchProfile
) -> float:
    if animal.training_needs is None:
        return 0.0
    return max(0.0, _unit(animal.training_needs) - _unit(adopter.experience))


def _noise_beyond_housing(
    adopter: MatchmakerProfile, animal: AnimalMatchProfile
) -> float:
    if animal.noise_level is None:
        return 0.0
    return max(0.0, _unit(animal.noise_level) - _unit(adopter.housing))


def _baby_needs_company_and_training(
    adopter: MatchmakerProfile, animal: AnimalMatchProfile
) -> float:
    if animal.life_stage is not LifeStage.BABY:
        return 0.0
    absence = _unit(adopter.time_away)
    inexperience = 1.0 - _unit(adopter.experience)
    return (absence + inexperience) / 2


STANDARD_INTERACTIONS: tuple[Interaction, ...] = (
    Interaction(
        name="training_experience",
        max_penalty=15,
        severity=_training_beyond_experience,
        reason="Its training needs are high for your experience",
    ),
    Interaction(
        name="noise_housing",
        max_penalty=10,
        severity=_noise_beyond_housing,
        reason="It can be noisy, which may not suit your home",
    ),
    Interaction(
        name="baby_care",
        max_penalty=15,
        severity=_baby_needs_company_and_training,
        reason="A young animal needs company and training you may find hard to give",
    ),
)

# Stacked edges are held here so a hard match still scores apart from a hopeless one.
MAX_TOTAL_PENALTY = 25.0


@dataclass(frozen=True)
class FitGraph:
    """The attributes of an adopter and an animal, and how they bear on each other.

    A graph in the modelling sense: attributes are the nodes and the interactions
    between them the weighted edges. It is stored flat on purpose, as plain tuples,
    because scoring is a single pass and nothing is traversed or propagated.
    """

    dimensions: tuple[Dimension[Any, Any], ...]
    interactions: tuple[Interaction, ...] = ()
    max_total_penalty: float = float("inf")

    @classmethod
    def standard(cls) -> "FitGraph":
        return cls(STANDARD_DIMENSIONS, STANDARD_INTERACTIONS, MAX_TOTAL_PENALTY)

    def assess(
        self, adopter: MatchmakerProfile, animal: AnimalMatchProfile
    ) -> list[Assessment]:
        """The dimensions that apply to this adopter, measured, in a fixed order."""
        assessed = (d.assess(adopter, animal) for d in self.dimensions)
        return [a for a in assessed if a is not None]

    def penalties(
        self, adopter: MatchmakerProfile, animal: AnimalMatchProfile
    ) -> list[Penalty]:
        """The interactions that fire for this pair, at full strength, in order."""
        fired = (i.assess(adopter, animal) for i in self.interactions)
        return [p for p in fired if p is not None]

    def total_penalty(self, penalties: Sequence[Penalty]) -> float:
        """The points to take off, held at the cap. Every reason still shows."""
        return min(sum(p.points for p in penalties), self.max_total_penalty)
