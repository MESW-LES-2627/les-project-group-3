"""Live updates (US-21): tell both sides of a request, at once, what happened to it.

Each person listens to one Ably channel of their own. Only small notices go there;
the text of a conversation never leaves Patas, and the page fetches it from us.
"""

import asyncio
from typing import Protocol
from uuid import UUID

from ably.pubsub.server import create_http_client
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from patas_backend.models.adoption import (
    AdoptionApplicationRepository,
    ApplicationAdopted,
    ApplicationDeclined,
    ApplicationWithdrawn,
)
from patas_backend.models.conversation import MessagePosted, MessageRepository
from patas_backend.services.events import EventDispatcher

# The announcement is awaited before the request answers: Ably being slow must not
# hold every write. Past this, the notice is dropped (the dispatcher logs it) and the
# page still shows the change on its next fetch or reload.
PUBLISH_TIMEOUT_SECONDS = 3.0


def channel_for(user_id: UUID) -> str:
    """The one channel a person listens to. Their token lets them listen to nothing
    else (the frontend's token route)."""
    return f"user:{user_id}"


class LivePublisher(Protocol):
    async def publish(self, user_id: UUID, name: str, data: dict[str, str]) -> None:
        """Send one notice to one person's channel."""

    async def close(self) -> None:
        """Release what the publisher holds, when the app stops."""


class NullPublisher:
    """No Ably key (local development, CI): nothing is live, and nothing breaks."""

    async def publish(self, user_id: UUID, name: str, data: dict[str, str]) -> None:
        return None

    async def close(self) -> None:
        return None


class AblyPublisher:
    """Publishes through Ably's HTTP API, declared as a server: accounts billed by
    monthly active users refuse the plain `ably` package, and a server is not counted
    as a user."""

    def __init__(self, api_key: str) -> None:
        self._client = create_http_client(key=api_key)

    async def publish(self, user_id: UUID, name: str, data: dict[str, str]) -> None:
        channel = self._client.channels.get(channel_for(user_id))
        await channel.publish(name=name, data=data)

    async def close(self) -> None:
        await self._client.close()


class LiveAnnouncer:
    """Tells both sides of a request, live, what just happened to it.

    Its methods are after-commit handlers (Observer): they read what they need in a
    session of their own, and a failure is logged by the dispatcher, never undoing
    the change that was announced.
    """

    def __init__(
        self,
        publisher: LivePublisher,
        session_factory: async_sessionmaker[AsyncSession],
        timeout_seconds: float = PUBLISH_TIMEOUT_SECONDS,
    ) -> None:
        self._publisher = publisher
        self._session_factory = session_factory
        self._timeout_seconds = timeout_seconds

    async def message_posted(self, event: MessagePosted) -> None:
        async with self._session_factory() as session:
            notice = await MessageRepository(session).get_notice(event.message_id)
        if notice is None:
            return
        data = {
            "application_id": str(notice.application_id),
            "message_id": str(notice.message_id),
            "sender_id": str(notice.sender_id),
            "sender_name": notice.sender_name,
            "sender_username": notice.sender_username,
            "animal_name": notice.animal_name,
        }
        # Both sides: the sender's other tabs need the message too.
        await self._tell_both(
            notice.owner_id, notice.applicant_id, "message.posted", data
        )

    async def request_ended(
        self, event: ApplicationDeclined | ApplicationWithdrawn | ApplicationAdopted
    ) -> None:
        # Only a request that had a conversation: one declined while open had none.
        if (
            isinstance(event, ApplicationDeclined | ApplicationWithdrawn)
            and not event.was_accepted
        ):
            return
        async with self._session_factory() as session:
            application = await AdoptionApplicationRepository(session).get_by_id(
                event.application_id
            )
        if application is None:
            return
        data = {
            "application_id": str(application.id),
            "status": application.status.value,
        }
        await self._tell_both(
            application.owner_id, application.applicant_id, "request.changed", data
        )

    async def _tell_both(
        self, owner_id: UUID, applicant_id: UUID, name: str, data: dict[str, str]
    ) -> None:
        # Together, so a failure on one channel does not stop the other, and bounded,
        # so a slow Ably does not hold the request (PUBLISH_TIMEOUT_SECONDS).
        await asyncio.wait_for(
            asyncio.gather(
                self._publisher.publish(owner_id, name, data),
                self._publisher.publish(applicant_id, name, data),
            ),
            timeout=self._timeout_seconds,
        )


def register_live_handlers(
    dispatcher: EventDispatcher, announcer: LiveAnnouncer
) -> None:
    dispatcher.register_after_commit(MessagePosted, announcer.message_posted)
    for ended in (ApplicationDeclined, ApplicationWithdrawn, ApplicationAdopted):
        dispatcher.register_after_commit(ended, announcer.request_ended)
