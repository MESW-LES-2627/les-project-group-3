from dataclasses import dataclass
from uuid import UUID

from patas_backend.models.events import DomainEvent


@dataclass(frozen=True)
class MessagePosted(DomainEvent):
    application_id: UUID
    message_id: UUID
    sender_id: UUID
