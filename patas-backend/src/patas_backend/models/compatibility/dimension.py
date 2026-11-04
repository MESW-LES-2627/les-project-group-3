from collections.abc import Callable, Mapping
from dataclasses import dataclass

from patas_backend.models.animal import AnimalMatchProfile
from patas_backend.models.compatibility.reason import Reason, ReasonKind
from patas_backend.models.matchmaker_profile import MatchmakerProfile


@dataclass(frozen=True)
class Wording:
    """What to tell the adopter, by how well the animal fits on one dimension."""

    fits: str
    misfit: str
    unknown: str
    # None: the dimension's table never gives a partial fit.
    partly: str | None = None


@dataclass(frozen=True)
class Assessment:
    """One dimension measured for one adopter and animal."""

    dimension: "Dimension"
    fit: float | None  # None: the owner did not say, which is never a "no"
    reason: Reason


@dataclass(frozen=True)
class Dimension[A, B]:
    """One adopter answer set against its animal counterpart, as data.

    A dimension only measures; what a fit is worth, and what a missing one costs,
    is up to the strategy that reads it.
    """

    name: str
    weight: int
    # Counts in a strict strategy's weakest link.
    critical: bool
    # A fit of 0 hides the animal in every mode.
    safety: bool
    # None: the dimension does not apply to this adopter.
    adopter_value: Callable[[MatchmakerProfile], A | None]
    animal_value: Callable[[AnimalMatchProfile], B | None]
    table: Mapping[tuple[A, B], float]
    wording: Wording

    def assess(
        self, adopter: MatchmakerProfile, animal: AnimalMatchProfile
    ) -> Assessment | None:
        asked = self.adopter_value(adopter)
        if asked is None:
            return None
        answered = self.animal_value(animal)
        if answered is None:
            unknown = Reason(self.wording.unknown, ReasonKind.UNKNOWN)
            return Assessment(self, None, unknown)
        fit = self.table[(asked, answered)]
        return Assessment(self, fit, self._reason(fit))

    def _reason(self, fit: float) -> Reason:
        if fit >= 1.0:
            return Reason(self.wording.fits, ReasonKind.STRENGTH)
        if fit > 0.0:
            if self.wording.partly is None:
                raise ValueError(
                    f"{self.name} has no wording for a partial fit ({fit})"
                )
            return Reason(self.wording.partly, ReasonKind.CONCERN)
        return Reason(self.wording.misfit, ReasonKind.CONCERN)
