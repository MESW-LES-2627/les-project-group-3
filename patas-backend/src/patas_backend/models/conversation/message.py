from dataclasses import dataclass
from datetime import datetime
from uuid import UUID, uuid4

from patas_backend.models.conversation.errors import InvalidMessage

MAX_MESSAGE_LENGTH = 2000


@dataclass(frozen=True)
class Message:
    """One message in the conversation of an adoption request.

    Its own aggregate: the request never loads its messages. Whether a message may be
    written at all is decided by the request's state (AdoptionApplication.post_message).
    Messages are never edited or deleted, so the history stays as it was said.
    """

    id: UUID
    application_id: UUID
    sender_id: UUID
    body: str
    sent_at: datetime

    @classmethod
    def write(
        cls, *, application_id: UUID, sender_id: UUID, body: str, at: datetime
    ) -> "Message":
        """A new message: trimmed, not blank, at most MAX_MESSAGE_LENGTH long."""
        cleaned = body.strip()
        if not cleaned:
            raise InvalidMessage("a message must not be blank")
        if len(cleaned) > MAX_MESSAGE_LENGTH:
            raise InvalidMessage(
                f"a message must have at most {MAX_MESSAGE_LENGTH} characters"
            )
        return cls(
            id=uuid4(),
            application_id=application_id,
            sender_id=sender_id,
            body=cleaned,
            sent_at=at,
        )
