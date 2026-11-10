import logging
from collections import deque
from collections.abc import Awaitable, Callable, Iterable
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from patas_backend.models.events import DomainEvent

logger = logging.getLogger(__name__)


class EventDispatcher:
    """Tells the handlers of each kind of event what happened.

    There are two kinds of handler, both registered by event class (a handler for
    a base class also receives its subclasses, in registration order):

    - in-transaction handlers keep the data consistent, for example reserving the
      animal when an application is accepted. They run inside the caller's
      transaction, and if one raises, everything rolls back;
    - after-commit handlers announce what already happened (Pusher, email,
      notifications). They get no session, and a failure is logged and never
      raised, so a push that fails cannot undo an adoption.

    A use case dispatches inside its transaction and publishes after it commits:

        async with session_factory.begin() as session:
            ...
            events = await dispatcher.dispatch(aggregate.pull_events(), session)
        await dispatcher.publish(events)

    Publishing is best effort: if the process dies between the commit and the
    publish, the announcement is lost. The database stays the truth.
    """

    def __init__(self) -> None:
        self._in_transaction: list[tuple[type[DomainEvent], Callable[..., Any]]] = []
        self._after_commit: list[tuple[type[DomainEvent], Callable[..., Any]]] = []

    def register[E: DomainEvent](
        self,
        event_type: type[E],
        handler: Callable[[E, AsyncSession], Awaitable[list[DomainEvent]]],
    ) -> None:
        """Run `handler` in the transaction for each event of this class. It returns
        the events of whatever it changed, which are dispatched too."""
        self._in_transaction.append((event_type, handler))

    def register_after_commit[E: DomainEvent](
        self, event_type: type[E], handler: Callable[[E], Awaitable[None]]
    ) -> None:
        """Run `handler` after the commit for each event of this class."""
        self._after_commit.append((event_type, handler))

    async def dispatch(
        self, events: Iterable[DomainEvent], session: AsyncSession
    ) -> list[DomainEvent]:
        """Run the in-transaction handlers. Returns every event handled, in order,
        including the ones the handlers returned."""
        pending = deque(events)
        handled: list[DomainEvent] = []
        while pending:
            event = pending.popleft()
            handled.append(event)
            for event_type, handler in self._in_transaction:
                if isinstance(event, event_type):
                    pending.extend(await handler(event, session))
        return handled

    async def publish(self, events: Iterable[DomainEvent]) -> None:
        """Run the after-commit handlers. Call it only after the commit."""
        for event in events:
            for event_type, handler in self._after_commit:
                if not isinstance(event, event_type):
                    continue
                try:
                    await handler(event)
                except Exception:
                    logger.exception(
                        "after-commit handler %s failed for %s",
                        getattr(handler, "__qualname__", handler),
                        type(event).__name__,
                    )
