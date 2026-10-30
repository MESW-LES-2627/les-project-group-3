from abc import abstractmethod
from collections.abc import Sequence
from typing import ClassVar

from patas_backend.models.animal import AnimalMatchProfile
from patas_backend.models.compatibility.dimension import Assessment
from patas_backend.models.compatibility.fit_graph import FitGraph
from patas_backend.models.compatibility.result import CompatibilityResult
from patas_backend.models.compatibility.strategy import CompatibilityStrategy
from patas_backend.models.matchmaker_profile import MatchmakerProfile

# An assessment with the fit it counts for, a blank answer already valued.
type Valued = Sequence[tuple[Assessment, float]]


class FitGraphStrategy(CompatibilityStrategy):
    """The skeleton every strategy over a FitGraph shares.

    The graph measures; a subclass decides what the measures are worth, through
    two values (what a blank answer counts for, how hard the edges bite) and the
    few hooks below.
    """

    # What a dimension the owner left blank counts for, from 0 to 1.
    missing_fit: ClassVar[float]
    # The share of the graph's edge penalty that is taken off the score.
    edge_strength: ClassVar[float]

    def __init__(self, graph: FitGraph | None = None) -> None:
        self._graph = FitGraph.standard() if graph is None else graph

    def evaluate(
        self, adopter: MatchmakerProfile, animal: AnimalMatchProfile
    ) -> CompatibilityResult:
        assessed = self._graph.assess(adopter, animal)
        valued = [(a, self._value(a)) for a in assessed]
        for assessment, fit in valued:
            if self._hides(assessment, fit):
                return CompatibilityResult.excluded(assessment.reason.text)

        penalties = self._graph.penalties(adopter, animal)
        edge_cost = self._graph.total_penalty(penalties) * self.edge_strength
        raw_score = self._score(self._weighted_average(valued), valued) - edge_cost
        reasons = [a.reason for a in assessed] + [p.reason for p in penalties]
        return CompatibilityResult.scored(raw_score, reasons)

    def _value(self, assessment: Assessment) -> float:
        return self.missing_fit if assessment.fit is None else assessment.fit

    def _hides(self, assessment: Assessment, fit: float) -> bool:
        """Whether this dimension alone rules the animal out. In every mode, an
        animal that is not safe with a member of the adopter's household."""
        return assessment.dimension.safety and fit <= 0.0

    @staticmethod
    def _weighted_average(valued: Valued) -> float:
        total_weight = sum(a.dimension.weight for a, _ in valued)
        return sum(a.dimension.weight * fit for a, fit in valued) / total_weight

    @abstractmethod
    def _score(self, base: float, valued: Valued) -> float:
        """The score from 0 to 100, before the edge penalties come off."""
