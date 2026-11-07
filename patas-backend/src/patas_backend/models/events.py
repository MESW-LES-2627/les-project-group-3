from dataclasses import dataclass


@dataclass(frozen=True)
class DomainEvent:
    """Something that happened in the domain, named in the past tense."""
