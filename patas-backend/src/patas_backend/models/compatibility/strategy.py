from abc import ABC, abstractmethod

from patas_backend.models.animal import AnimalMatchProfile
from patas_backend.models.compatibility.result import CompatibilityResult
from patas_backend.models.matchmaker_profile import MatchmakerProfile


class CompatibilityStrategy(ABC):
    """One way to judge how well an animal fits an adopter.

    It reads only the two profiles, which are on the same scales, so it cannot
    depend on anything an owner or adopter did not answer.
    """

    @abstractmethod
    def evaluate(
        self, adopter: MatchmakerProfile, animal: AnimalMatchProfile
    ) -> CompatibilityResult: ...
