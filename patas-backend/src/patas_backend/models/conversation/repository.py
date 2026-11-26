from typing import Any
from uuid import UUID

from sqlalchemy import Row, text
from sqlalchemy.ext.asyncio import AsyncSession

from patas_backend.models.conversation.message import Message
from patas_backend.models.conversation.message_notice import MessageNotice
from patas_backend.models.conversation.message_view import MessageView

_INSERT = text(
    """
    INSERT INTO patas.messages (id, application_id, sender_id, body, sent_at)
    VALUES (:id, :application_id, :sender_id, :body, :sent_at)
    """
)
# The users table never loses a row, so the inner join never drops a message.
_VIEW = """
    SELECT m.id, m.application_id, m.sender_id, u.name AS sender_name,
           u.username AS sender_username, m.body, m.sent_at
    FROM patas.messages m
    JOIN patas.users u ON u.id = m.sender_id
"""
_SELECT_ONE = text(_VIEW + " WHERE m.id = :id")
# sent_at can tie, so id keeps the order the same on every read and for "after".
_SELECT_ALL = text(
    _VIEW + " WHERE m.application_id = :application_id ORDER BY m.sent_at, m.id"
)
_SELECT_AFTER = text(
    _VIEW
    + """
    WHERE m.application_id = :application_id
      AND (m.sent_at, m.id) > (:sent_at, :id)
    ORDER BY m.sent_at, m.id
    """
)
# Everything the live notice needs, and nothing of the text.
_SELECT_NOTICE = text(
    """
    SELECT m.application_id, m.id AS message_id, m.sender_id,
           u.name AS sender_name, u.username AS sender_username,
           an.name AS animal_name, a.owner_id, a.applicant_id
    FROM patas.messages m
    JOIN patas.users u ON u.id = m.sender_id
    JOIN patas.adoption_applications a ON a.id = m.application_id
    JOIN patas.animals an ON an.id = a.animal_id
    WHERE m.id = :id
    """
)
_CURSOR = text(
    """
    SELECT sent_at, id FROM patas.messages
    WHERE id = :id AND application_id = :application_id
    """
)


def _view(row: Row[Any]) -> MessageView:
    return MessageView(
        id=row.id,
        application_id=row.application_id,
        sender_id=row.sender_id,
        sender_name=row.sender_name,
        sender_username=row.sender_username,
        body=row.body,
        sent_at=row.sent_at,
    )


class MessageRepository:
    """Persistence for Message. The caller owns the transaction; this never commits."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, message: Message) -> None:
        await self._session.execute(
            _INSERT,
            {
                "id": message.id,
                "application_id": message.application_id,
                "sender_id": message.sender_id,
                "body": message.body,
                "sent_at": message.sent_at,
            },
        )

    async def get_view(self, message_id: UUID) -> MessageView | None:
        result = await self._session.execute(_SELECT_ONE, {"id": message_id})
        row = result.first()
        return _view(row) if row is not None else None

    async def get_notice(self, message_id: UUID) -> MessageNotice | None:
        """What to tell both sides about this message, without its text."""
        result = await self._session.execute(_SELECT_NOTICE, {"id": message_id})
        row = result.first()
        if row is None:
            return None
        return MessageNotice(
            application_id=row.application_id,
            message_id=row.message_id,
            sender_id=row.sender_id,
            sender_name=row.sender_name,
            sender_username=row.sender_username,
            animal_name=row.animal_name,
            owner_id=row.owner_id,
            applicant_id=row.applicant_id,
        )

    async def list_for(
        self, application_id: UUID, after: UUID | None
    ) -> list[MessageView]:
        """The conversation in order. With `after`, only the messages after that one.

        An `after` that is not a message of this conversation gives them all: the
        page then merges what it already has.
        """
        cursor = None
        if after is not None:
            found = await self._session.execute(
                _CURSOR, {"id": after, "application_id": application_id}
            )
            cursor = found.first()
        if cursor is None:
            result = await self._session.execute(
                _SELECT_ALL, {"application_id": application_id}
            )
        else:
            result = await self._session.execute(
                _SELECT_AFTER,
                {
                    "application_id": application_id,
                    "sent_at": cursor.sent_at,
                    "id": cursor.id,
                },
            )
        return [_view(row) for row in result]
