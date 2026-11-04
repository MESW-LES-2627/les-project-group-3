from dataclasses import dataclass
from enum import StrEnum


class ReasonKind(StrEnum):
    STRENGTH = "strength"  # the animal fits on this
    CONCERN = "concern"  # a partial or full mismatch, or an interaction that fired
    UNKNOWN = "unknown"  # the owner did not say, which is neither of the others


@dataclass(frozen=True)
class Reason:
    """One line of why an animal scored as it did, and what kind of line it is."""

    text: str
    kind: ReasonKind
