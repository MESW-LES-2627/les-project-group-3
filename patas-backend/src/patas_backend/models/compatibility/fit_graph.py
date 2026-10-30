from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from patas_backend.models.animal import AnimalMatchProfile, AnimalSize
from patas_backend.models.compatibility import rules
from patas_backend.models.compatibility.dimension import (
    Assessment,
    Dimension,
    Wording,
)
from patas_backend.models.compatibility.interaction import Interaction, Penalty
from patas_backend.models.matching import ExperienceLevel, TimeAway
from patas_backend.models.matchmaker_profile import MatchmakerProfile

# This file only wires the graph together. Every number and sentence is in rules.py.


def _dimension[A, B](
    name: str,
    adopter_value: Callable[[MatchmakerProfile], A | None],
    animal_value: Callable[[AnimalMatchProfile], B | None],
    table: Mapping[tuple[A, B], float],
    wording: Wording,
) -> Dimension[A, B]:
    return Dimension(
        name=name,
        weight=rules.WEIGHTS[name],
        critical=name in rules.CRITICAL,
        safety=name in rules.SAFETY,
        adopter_value=adopter_value,
        animal_value=animal_value,
        table=table,
        wording=wording,
    )


def _household(
    name: str,
    has: Callable[[MatchmakerProfile], bool],
    safe: Callable[[AnimalMatchProfile], bool | None],
) -> Dimension[bool, bool]:
    return _dimension(
        name,
        lambda adopter: True if has(adopter) else None,
        safe,
        rules.HOUSEHOLD,
        rules.household_wording(name),
    )


def _interaction(
    name: str,
    severity: Callable[[MatchmakerProfile, AnimalMatchProfile], float],
) -> Interaction:
    return Interaction(
        name=name,
        max_penalty=rules.MAX_PENALTY[name],
        severity=severity,
        reason=rules.EDGE_REASON[name],
    )


STANDARD_DIMENSIONS: tuple[Dimension[Any, Any], ...] = (
    _dimension(
        "activity",
        lambda adopter: adopter.activity,
        lambda animal: animal.activity,
        rules.ACTIVITY,
        rules.ACTIVITY_WORDING,
    ),
    _dimension(
        "time_alone",
        lambda adopter: adopter.time_away,
        lambda animal: animal.max_time_alone,
        rules.ceiling_table(TimeAway),
        rules.TIME_ALONE_WORDING,
    ),
    _dimension(
        "experience",
        lambda adopter: adopter.experience,
        lambda animal: animal.experience_needed,
        rules.floor_table(ExperienceLevel),
        rules.EXPERIENCE_WORDING,
    ),
    _dimension(
        "space",
        lambda adopter: adopter.space_offered,
        lambda animal: animal.space_needed,
        rules.floor_table(AnimalSize),
        rules.SPACE_WORDING,
    ),
    _household(
        "children",
        lambda adopter: adopter.has_children,
        lambda animal: animal.safe_with_children,
    ),
    _household(
        "dogs",
        lambda adopter: adopter.has_dogs,
        lambda animal: animal.safe_with_dogs,
    ),
    _household(
        "cats",
        lambda adopter: adopter.has_cats,
        lambda animal: animal.safe_with_cats,
    ),
)

STANDARD_INTERACTIONS: tuple[Interaction, ...] = (
    _interaction("training_experience", rules.training_beyond_experience),
    _interaction("noise_housing", rules.noise_beyond_housing),
    _interaction("baby_care", rules.baby_needs_company_and_training),
)


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
        return cls(STANDARD_DIMENSIONS, STANDARD_INTERACTIONS, rules.MAX_TOTAL_PENALTY)

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
