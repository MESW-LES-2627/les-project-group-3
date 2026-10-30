from enum import StrEnum

from patas_backend.models.matching import EnergyLevel

# Placeholder business rules, kept in one place for the team to agree on.
# Each table maps (adopter value, animal value) to a fit from 0 (no fit) to 1.

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
