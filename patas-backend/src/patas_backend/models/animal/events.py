from dataclasses import dataclass
from uuid import UUID

from patas_backend.models.events import DomainEvent


@dataclass(frozen=True)
class AnimalUnpublished(DomainEvent):
    animal_id: UUID
