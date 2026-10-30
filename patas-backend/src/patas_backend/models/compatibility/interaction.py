from collections.abc import Callable
from dataclasses import dataclass

from patas_backend.models.animal import AnimalMatchProfile
from patas_backend.models.matchmaker_profile import MatchmakerProfile


@dataclass(frozen=True)
class Penalty:
    """Points an interaction takes off the score, at full strength."""

    interaction: "Interaction"
    points: float
    reason: str


@dataclass(frozen=True)
class Interaction:
    """An edge of the graph: one animal attribute judged against the adopter.

    It reaches across dimensions, so a dimension's own table cannot express it.
    """

    name: str
    max_penalty: int
    # How bad the interaction is, from 0 (none) to 1 (as bad as it gets).
    severity: Callable[[MatchmakerProfile, AnimalMatchProfile], float]
    reason: str

    def assess(
        self, adopter: MatchmakerProfile, animal: AnimalMatchProfile
    ) -> Penalty | None:
        severity = self.severity(adopter, animal)
        if severity <= 0.0:
            return None
        return Penalty(self, self.max_penalty * severity, self.reason)
