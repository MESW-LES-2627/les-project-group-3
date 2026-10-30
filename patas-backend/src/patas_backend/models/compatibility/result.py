import math
from collections.abc import Iterable
from dataclasses import dataclass

from patas_backend.models.compatibility.reason import Reason, ReasonKind


class InvalidCompatibilityResult(ValueError):
    """A CompatibilityResult invariant was violated."""


@dataclass(frozen=True)
class CompatibilityResult:
    """How well an animal fits an adopter: a score, why, and whether to show it."""

    score: int
    reasons: tuple[Reason, ...]
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
    def scored(
        cls, raw_score: float, reasons: Iterable[Reason]
    ) -> "CompatibilityResult":
        # Half rounds up: Python's round() would send 62.5 down and 37.5 up.
        score = math.floor(raw_score + 0.5)
        return cls(score=min(100, max(0, score)), reasons=tuple(reasons))

    @classmethod
    def excluded(cls, reason: str) -> "CompatibilityResult":
        concern = Reason(reason, ReasonKind.CONCERN)
        return cls(score=0, reasons=(concern,), is_compatible=False)
