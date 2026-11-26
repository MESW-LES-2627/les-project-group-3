from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from patas_backend.models.adoption import AdoptionApplicationRepository
from patas_backend.models.conversation import MessageRepository, MessageView
from patas_backend.models.user import User
from patas_backend.services.events import EventDispatcher
from patas_backend.services.locking import lock_animal_and_application


class ConversationService:
    """Conversation use cases (US-21). Each one owns its transaction."""

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        dispatcher: EventDispatcher,
    ) -> None:
        self._session_factory = session_factory
        self._dispatcher = dispatcher

    async def post(
        self, actor: User, application_id: UUID, body: str
    ) -> MessageView | None:
        """One side writes in the conversation.

        None if there is no such request or the caller is neither side: to anyone
        else it does not exist. Raises InvalidTransition if the request is not
        accepted, or InvalidMessage for a blank or too long message.
        """
        async with self._session_factory.begin() as session:
            # The same lock order as every adoption use case (ADR 0017, decision 8):
            # a decline and a message take turns, so no message lands after a decline.
            application = await lock_animal_and_application(session, application_id)
            if application is None or not application.is_participant(actor.id):
                return None
            message = application.post_message(actor.id, body, datetime.now(UTC))
            messages = MessageRepository(session)
            await messages.add(message)
            # Writing does not change the request, so there is nothing to update.
            events = await self._dispatcher.dispatch(application.pull_events(), session)
            view = await messages.get_view(message.id)
        await self._dispatcher.publish(events)
        return view

    async def read(
        self, actor: User, application_id: UUID, after: UUID | None
    ) -> list[MessageView] | None:
        """The conversation, oldest first; with `after`, only the newer messages.

        None unless the caller is a side of a request that was accepted at some point.
        """
        async with self._session_factory() as session:
            application = await AdoptionApplicationRepository(session).get_by_id(
                application_id
            )
            if (
                application is None
                or not application.is_participant(actor.id)
                or not application.has_conversation
            ):
                return None
            return await MessageRepository(session).list_for(application_id, after)
