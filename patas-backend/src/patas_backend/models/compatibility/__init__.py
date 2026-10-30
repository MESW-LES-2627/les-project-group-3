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
from patas_backend.models.compatibility.mode import (
    CompatibilityMode,
    InvalidCompatibilityMode,
    strategy_for,
)
from patas_backend.models.compatibility.reason import Reason, ReasonKind
from patas_backend.models.compatibility.result import (
    CompatibilityResult,
    InvalidCompatibilityResult,
)
from patas_backend.models.compatibility.strategy import CompatibilityStrategy
from patas_backend.models.compatibility.strict_fit_strategy import StrictFitStrategy

__all__ = [
    "Assessment",
    "CompatibilityMode",
    "CompatibilityResult",
    "CompatibilityStrategy",
    "Dimension",
    "FitGraph",
    "FitGraphStrategy",
    "Interaction",
    "InvalidCompatibilityMode",
    "InvalidCompatibilityResult",
    "LooseFitStrategy",
    "Penalty",
    "Reason",
    "ReasonKind",
    "StrictFitStrategy",
    "Wording",
    "rules",
    "strategy_for",
]
