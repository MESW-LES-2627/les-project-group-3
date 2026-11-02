from typing import ClassVar

from patas_backend.models.compatibility import rules
from patas_backend.models.compatibility.dimension import Assessment
from patas_backend.models.compatibility.fit_graph_strategy import (
    FitGraphStrategy,
    Valued,
)


class StrictFitStrategy(FitGraphStrategy):
    """Not for you, unless it fits: the weakest critical fit pulls the whole score down.

    A blank answer is suspect and costs through the average, edges bite in full,
    and a critical dimension two steps short hides the animal.
    """

    missing_fit: ClassVar[float] = 0.25
    edge_strength: ClassVar[float] = 1.0

    def _hides(self, assessment: Assessment, fit: float) -> bool:
        critical_zero = assessment.dimension.critical and fit <= 0.0
        return critical_zero or super()._hides(assessment, fit)

    def _score(self, base: float, valued: Valued) -> float:
        # The weakest link is the weakest known fit. A blank answer is not a known
        # problem: it already costs through the average, and must not veto the score.
        known = [fit for a, fit in valued if a.dimension.critical and a.fit is not None]
        weakest = min(known, default=1.0)
        return 100 * base * (1 - rules.WEAKEST_LINK_STRENGTH * (1 - weakest))
