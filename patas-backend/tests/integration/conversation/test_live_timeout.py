"""US-21: Ably being slow must not hold a write. The announcement is awaited before
the request answers, so it is bounded: past the limit the notice is dropped and the
message stands."""

import asyncio
import time
from uuid import UUID

from adoption_factory import Factory, World, adoption_dispatcher, persist_application
from live import RecordingPublisher
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from patas_backend.models.adoption import ApplicationStatus
from patas_backend.models.user import User
from patas_backend.services.conversation import ConversationService
from patas_backend.services.live import LiveAnnouncer, register_live_handlers


class SlowPublisher(RecordingPublisher):
    """Ably is unreachable: every publish hangs far longer than a person would wait."""

    async def publish(self, user_id: UUID, name: str, data: dict[str, str]) -> None:
        await asyncio.sleep(30)


async def test_a_slow_ably_does_not_hold_the_message(
    engine: AsyncEngine, session_factory: Factory, world: World
) -> None:
    request = await persist_application(
        session_factory, world, applicant=world.bruno, status=ApplicationStatus.ACCEPTED
    )
    dispatcher = adoption_dispatcher()
    register_live_handlers(
        dispatcher,
        LiveAnnouncer(SlowPublisher(), session_factory, timeout_seconds=0.2),
    )
    service = ConversationService(session_factory, dispatcher)
    bruno = User.provision(id=world.bruno, name="Bruno", email="bruno@example.com")

    started = time.monotonic()
    view = await service.post(bruno, request.id, "Still there?")
    elapsed = time.monotonic() - started

    assert view is not None
    assert elapsed < 5
    async with engine.connect() as conn:
        count = await conn.scalar(text("SELECT count(*) FROM patas.messages"))
    assert count == 1
