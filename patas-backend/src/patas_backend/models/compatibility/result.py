import math
from collections.abc import Iterable
from dataclasses import dataclass


class InvalidCompatibilityResult(ValueError):
    """A CompatibilityResult invariant was violated."""


@dataclass(frozen=True)
class CompatibilityResult:
    """How well an animal fits an adopter: a score, why, and whether to show it."""

    score: int
    reasons: tuple[str, ...]
    is_compatible: bool = True

    def __post_init__(self) -> None:
        # Invariants hold however a result is built, not only through the factories.
        if not 0 <= self.score <= 100:
            raise InvalidCompatibilityResult("score must be between 0 and 100")
        if not self.is_compatible and (self.score != 0 or not self.reasons):
            raise InvalidCompatibilityResult(
                "an incompatible result must score 0 and say why"
            )

    @classmethod
    def scored(cls, raw_score: float, reasons: Iterable[str]) -> "CompatibilityResult":
        # Half rounds up: Python's round() would send 62.5 down and 37.5 up.
        score = math.floor(raw_score + 0.5)
        return cls(score=min(100, max(0, score)), reasons=tuple(reasons))

    @classmethod
    def excluded(cls, reason: str) -> "CompatibilityResult":
        return cls(score=0, reasons=(reason,), is_compatible=False)
