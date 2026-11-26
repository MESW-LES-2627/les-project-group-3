from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class MessageView:
    """A message as the conversation shows it, with who wrote it.

    A read model: it answers what the page shows and holds no rules. Messages are
    written through AdoptionApplication.post_message, never through this.
    """

    id: UUID
    application_id: UUID
    sender_id: UUID
    sender_name: str
    sender_username: str
    body: str
    sent_at: datetime
