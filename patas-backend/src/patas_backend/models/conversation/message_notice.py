from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class MessageNotice:
    """What the two sides of a request are told, live, when a message arrives.

    It has no body on purpose: the text of a conversation never leaves Patas. The page
    that receives the notice fetches the message from us.
    """

    application_id: UUID
    message_id: UUID
    sender_id: UUID
    sender_name: str
    sender_username: str
    animal_name: str
    owner_id: UUID
    applicant_id: UUID
