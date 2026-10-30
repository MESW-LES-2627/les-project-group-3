from typing import ClassVar

from patas_backend.models.compatibility.fit_graph_strategy import (
    FitGraphStrategy,
    Valued,
)


class LooseFitStrategy(FitGraphStrategy):
    """Possible, but check this: good answers can make up for a bad one.

    A blank answer is neutral, edges bite at half strength, and only a household
    member the animal is not safe with hides it.
    """

    missing_fit: ClassVar[float] = 0.5
    edge_strength: ClassVar[float] = 0.5

    def _score(self, base: float, valued: Valued) -> float:
        return 100 * base
