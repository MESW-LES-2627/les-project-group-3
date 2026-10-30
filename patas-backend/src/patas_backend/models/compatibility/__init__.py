from patas_backend.models.compatibility import rules
from patas_backend.models.compatibility.dimension import (
    Assessment,
    Dimension,
    Wording,
)
from patas_backend.models.compatibility.fit_graph import FitGraph
from patas_backend.models.compatibility.fit_graph_strategy import FitGraphStrategy
from patas_backend.models.compatibility.interaction import Interaction, Penalty
from patas_backend.models.compatibility.loose_fit_strategy import LooseFitStrategy
from patas_backend.models.compatibility.result import (
    CompatibilityResult,
    InvalidCompatibilityResult,
)
from patas_backend.models.compatibility.strategy import CompatibilityStrategy

__all__ = [
    "Assessment",
    "CompatibilityResult",
    "CompatibilityStrategy",
    "Dimension",
    "FitGraph",
    "FitGraphStrategy",
    "Interaction",
    "InvalidCompatibilityResult",
    "LooseFitStrategy",
    "Penalty",
    "Wording",
    "rules",
]
