from dataclasses import dataclass
from uuid import UUID

from patas_backend.models.events import DomainEvent


@dataclass(frozen=True)
class ApplicationEvent(DomainEvent):
    application_id: UUID
    animal_id: UUID


@dataclass(frozen=True)
class ApplicationAccepted(ApplicationEvent):
    pass


@dataclass(frozen=True)
class ApplicationDeclined(ApplicationEvent):
    # An accepted application had reserved the animal, so declining it frees it.
    was_accepted: bool


@dataclass(frozen=True)
class ApplicationWithdrawn(ApplicationEvent):
    was_accepted: bool


@dataclass(frozen=True)
class ApplicationAdopted(ApplicationEvent):
    pass


@dataclass(frozen=True)
class ApplicationClosed(ApplicationEvent):
    pass
