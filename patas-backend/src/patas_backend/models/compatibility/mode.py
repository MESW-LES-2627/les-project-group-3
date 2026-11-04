from collections.abc import Callable, Mapping
from enum import StrEnum

from patas_backend.models.compatibility.loose_fit_strategy import LooseFitStrategy
from patas_backend.models.compatibility.strategy import CompatibilityStrategy
from patas_backend.models.compatibility.strict_fit_strategy import StrictFitStrategy


class InvalidCompatibilityMode(ValueError):
    """A compatibility mode was not one of the known ones."""


class CompatibilityMode(StrEnum):
    LOOSE = "loose"
    STRICT = "strict"


_STRATEGIES: Mapping[CompatibilityMode, Callable[[], CompatibilityStrategy]] = {
    CompatibilityMode.LOOSE: LooseFitStrategy,
    CompatibilityMode.STRICT: StrictFitStrategy,
}


def strategy_for(mode: str) -> CompatibilityStrategy:
    """The strategy a mode asks for, so callers never name a strategy class."""
    try:
        chosen = CompatibilityMode(mode)
    except ValueError:
        allowed = ", ".join(m.value for m in CompatibilityMode)
        raise InvalidCompatibilityMode(f"mode must be one of: {allowed}") from None
    return _STRATEGIES[chosen]()
