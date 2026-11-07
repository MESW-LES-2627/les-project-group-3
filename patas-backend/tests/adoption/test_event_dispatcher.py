import logging
from collections.abc import Sequence
from dataclasses import dataclass

import pytest

from patas_backend.models.events import DomainEvent
from patas_backend.services.events import EventDispatcher


@dataclass(frozen=True)
class Base(DomainEvent):
    pass


@dataclass(frozen=True)
class A(Base):
    pass


@dataclass(frozen=True)
class B(Base):
    pass


@dataclass(frozen=True)
class C(DomainEvent):
    pass


SESSION = object()  # the dispatcher only passes it on


def _recorder(seen: list, tag: str = "", then: Sequence[DomainEvent] = ()):
    async def handler(event: DomainEvent, session: object) -> list[DomainEvent]:
        seen.append((tag, event, session))
        return list(then)

    return handler


def _after_commit_recorder(seen: list, tag: str = ""):
    async def handler(event: DomainEvent) -> None:
        seen.append((tag, event))

    return handler


async def test_a_handler_gets_the_event_and_the_session() -> None:
    seen: list = []
    dispatcher = EventDispatcher()
    dispatcher.register(A, _recorder(seen))

    await dispatcher.dispatch([A()], SESSION)

    assert seen == [("", A(), SESSION)]


async def test_a_handler_for_a_base_class_gets_its_subclasses_only() -> None:
    seen: list = []
    dispatcher = EventDispatcher()
    dispatcher.register(Base, _recorder(seen, "base"))
    dispatcher.register(DomainEvent, _recorder(seen, "everything"))

    await dispatcher.dispatch([A(), B(), C()], SESSION)

    assert [(tag, event) for tag, event, _ in seen if tag == "base"] == [
        ("base", A()),
        ("base", B()),
    ]
    assert [event for tag, event, _ in seen if tag == "everything"] == [A(), B(), C()]


async def test_handlers_run_in_registration_order_across_types() -> None:
    seen: list = []
    dispatcher = EventDispatcher()
    dispatcher.register(A, _recorder(seen, "specific"))
    dispatcher.register(Base, _recorder(seen, "general"))
    dispatcher.register(A, _recorder(seen, "last"))

    await dispatcher.dispatch([A()], SESSION)

    assert [tag for tag, _, _ in seen] == ["specific", "general", "last"]


async def test_an_event_with_no_handler_is_ignored() -> None:
    dispatcher = EventDispatcher()

    assert await dispatcher.dispatch([C()], SESSION) == [C()]


async def test_dispatch_returns_every_event_handled_nested_ones_included() -> None:
    dispatcher = EventDispatcher()
    dispatcher.register(A, _recorder([], then=[B()]))
    dispatcher.register(B, _recorder([], then=[C()]))

    handled = await dispatcher.dispatch([A()], SESSION)

    assert handled == [A(), B(), C()]


async def test_nested_events_reach_the_subscribers_too() -> None:
    seen: list = []
    dispatcher = EventDispatcher()
    dispatcher.register(A, _recorder([], then=[B()]))
    dispatcher.register(B, _recorder(seen, "subscriber"))

    await dispatcher.dispatch([A()], SESSION)

    assert [event for _, event, _ in seen] == [B()]


async def test_after_commit_handlers_run_in_publish_not_in_dispatch() -> None:
    seen: list = []
    dispatcher = EventDispatcher()
    dispatcher.register_after_commit(A, _after_commit_recorder(seen))

    handled = await dispatcher.dispatch([A()], SESSION)
    assert seen == []

    await dispatcher.publish(handled)
    assert seen == [("", A())]


async def test_publish_includes_the_events_handlers_raised() -> None:
    seen: list = []
    dispatcher = EventDispatcher()
    dispatcher.register(A, _recorder([], then=[B()]))
    dispatcher.register_after_commit(B, _after_commit_recorder(seen))

    await dispatcher.publish(await dispatcher.dispatch([A()], SESSION))

    assert seen == [("", B())]


async def test_a_failing_after_commit_handler_is_logged_and_the_others_still_run(
    caplog: pytest.LogCaptureFixture,
) -> None:
    seen: list = []

    async def broken(event: DomainEvent) -> None:
        raise RuntimeError("the push service is down")

    dispatcher = EventDispatcher()
    dispatcher.register_after_commit(A, broken)
    dispatcher.register_after_commit(A, _after_commit_recorder(seen))

    with caplog.at_level(logging.ERROR):
        await dispatcher.publish([A()])

    assert seen == [("", A())]
    assert any("the push service is down" in r.exc_text for r in caplog.records)


async def test_an_in_transaction_handler_that_raises_stops_the_dispatch() -> None:
    seen: list = []

    async def broken(event: DomainEvent, session: object) -> list[DomainEvent]:
        raise RuntimeError("cannot reserve")

    dispatcher = EventDispatcher()
    dispatcher.register(A, broken)
    dispatcher.register(A, _recorder(seen))

    with pytest.raises(RuntimeError, match="cannot reserve"):
        await dispatcher.dispatch([A()], SESSION)

    assert seen == []
