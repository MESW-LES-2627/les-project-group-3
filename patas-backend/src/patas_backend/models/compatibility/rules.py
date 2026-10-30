from enum import StrEnum

from patas_backend.models.animal import AnimalMatchProfile
from patas_backend.models.compatibility.dimension import Wording
from patas_backend.models.matching import EnergyLevel, LifeStage
from patas_backend.models.matchmaker_profile import MatchmakerProfile

# The placeholder business rules of the Matchmaker's compatibility score, all in one
# file for the team to review and agree on (and for the ADR to point at). Nothing
# else in this package holds a number or a sentence shown to the adopter, except the
# strategies' own policy: what a blank answer is worth, how hard edges bite.

# --- Fit: each table maps (adopter value, animal value) to 0 (no fit) .. 1 (full) ---

# By how many steps short the adopter or the animal falls on an ordered scale.
_FIT_BY_STEPS_SHORT = (1.0, 0.5, 0.0)


def _fit_for(steps_short: int) -> float:
    return _FIT_BY_STEPS_SHORT[min(max(steps_short, 0), 2)]


def floor_table[S: StrEnum](scale: type[S]) -> dict[tuple[S, S], float]:
    """What the animal needs is a floor under what the adopter has."""
    order = list(scale)
    return {
        (has, needed): _fit_for(order.index(needed) - order.index(has))
        for has in order
        for needed in order
    }


def ceiling_table[S: StrEnum](scale: type[S]) -> dict[tuple[S, S], float]:
    """What the animal can bear is a ceiling over what the adopter brings."""
    order = list(scale)
    return {
        (brings, bears): _fit_for(order.index(brings) - order.index(bears))
        for brings in order
        for bears in order
    }


# Asymmetric: an animal more energetic than its adopter fits worse than a calmer one.
ACTIVITY: dict[tuple[EnergyLevel, EnergyLevel], float] = {
    (EnergyLevel.LOW, EnergyLevel.LOW): 1.0,
    (EnergyLevel.LOW, EnergyLevel.MODERATE): 0.5,
    (EnergyLevel.LOW, EnergyLevel.HIGH): 0.2,
    (EnergyLevel.MODERATE, EnergyLevel.LOW): 0.8,
    (EnergyLevel.MODERATE, EnergyLevel.MODERATE): 1.0,
    (EnergyLevel.MODERATE, EnergyLevel.HIGH): 0.5,
    (EnergyLevel.HIGH, EnergyLevel.LOW): 0.6,
    (EnergyLevel.HIGH, EnergyLevel.MODERATE): 0.8,
    (EnergyLevel.HIGH, EnergyLevel.HIGH): 1.0,
}

# The adopter has a household member; the animal is safe with it or not.
# A blank animal answer has no row: it is a missing answer, valued by the strategy.
HOUSEHOLD: dict[tuple[bool, bool], float] = {
    (True, True): 1.0,
    (True, False): 0.0,
}

# --- Dimensions: weight in the average, and which flags they carry ---

WEIGHTS = {
    "activity": 1,
    "time_alone": 1,
    "experience": 1,
    "space": 1,
    "children": 2,
    "dogs": 2,
    "cats": 2,
}
# Counts in a strict strategy's weakest link.
CRITICAL = frozenset({"time_alone", "experience", "space", "children", "dogs", "cats"})
# A fit of 0 hides the animal in every mode.
SAFETY = frozenset({"children", "dogs", "cats"})

# --- Dimensions: what the adopter is told ---

ACTIVITY_WORDING = Wording(
    fits="Matches your activity level",
    partly="Its energy is a bit different from yours",
    misfit="Its energy is very different from yours",
    unknown="The owner did not say how active it is",
)
TIME_ALONE_WORDING = Wording(
    fits="Fine with the time you are away",
    partly="Would be alone longer than it is used to",
    misfit="Cannot be left alone for as long as you are away",
    unknown="The owner did not say how long it can be left alone",
)
EXPERIENCE_WORDING = Wording(
    fits="Suits your experience",
    partly="Needs a bit more experience than you have",
    misfit="Needs much more experience than you have",
    unknown="The owner did not say if it suits first-time owners",
)
SPACE_WORDING = Wording(
    fits="Your home gives it enough space",
    partly="Needs more space than your home offers",
    misfit="Needs far more space than your home offers",
    unknown="The owner did not say how much space it needs",
)


def household_wording(noun: str) -> Wording:
    # The table only gives 1 or 0, so there is no partial wording.
    return Wording(
        fits=f"Safe with {noun}",
        misfit=f"Not safe with {noun}",
        unknown=f"The owner did not say if it is safe with {noun}",
    )


# --- Edges: an animal attribute judged against the adopter, across dimensions ---

# The most points each edge can take off, and what the adopter is told.
MAX_PENALTY = {"training_experience": 15, "noise_housing": 10, "baby_care": 15}
EDGE_REASON = {
    "training_experience": "Its training needs are high for your experience",
    "noise_housing": "It can be noisy, which may not suit your home",
    "baby_care": "A young animal needs company and training you may find hard to give",
}
# Stacked edges are held here so a hard match still scores apart from a hopeless one.
MAX_TOTAL_PENALTY = 25.0


def _unit(value: StrEnum) -> float:
    """Where a value sits on its scale: 0 for the first, 1 for the last."""
    scale = list(type(value))
    return scale.index(value) / (len(scale) - 1)


# Severity runs from 0 (the edge does not fire) to 1 (as bad as it gets). An edge
# never fires on a blank animal answer: it punishes a known problem only.


def training_beyond_experience(
    adopter: MatchmakerProfile, animal: AnimalMatchProfile
) -> float:
    if animal.training_needs is None:
        return 0.0
    return max(0.0, _unit(animal.training_needs) - _unit(adopter.experience))


def noise_beyond_housing(
    adopter: MatchmakerProfile, animal: AnimalMatchProfile
) -> float:
    if animal.noise_level is None:
        return 0.0
    return max(0.0, _unit(animal.noise_level) - _unit(adopter.housing))


def baby_needs_company_and_training(
    adopter: MatchmakerProfile, animal: AnimalMatchProfile
) -> float:
    if animal.life_stage is not LifeStage.BABY:
        return 0.0
    absence = _unit(adopter.time_away)
    inexperience = 1.0 - _unit(adopter.experience)
    return (absence + inexperience) / 2
