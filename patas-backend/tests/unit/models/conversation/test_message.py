from datetime import UTC, datetime
from uuid import uuid4

import pytest

from patas_backend.models.conversation import (
    MAX_MESSAGE_LENGTH,
    InvalidMessage,
    Message,
)

NOW = datetime(2026, 11, 26, 10, 0, tzinfo=UTC)
APPLICATION, SENDER = uuid4(), uuid4()


def _write(body: str) -> Message:
    return Message.write(
        application_id=APPLICATION, sender_id=SENDER, body=body, at=NOW
    )


def test_a_message_keeps_who_wrote_it_where_and_when() -> None:
    message = _write("Hello")

    assert message.application_id == APPLICATION
    assert message.sender_id == SENDER
    assert message.sent_at == NOW
    assert message.body == "Hello"


def test_each_message_gets_its_own_id() -> None:
    assert _write("a").id != _write("a").id


def test_a_message_is_stored_trimmed() -> None:
    assert _write("  Can I visit Rex?\n").body == "Can I visit Rex?"


@pytest.mark.parametrize("body", ["", "   ", "\n\t "])
def test_a_blank_message_is_refused(body: str) -> None:
    with pytest.raises(InvalidMessage):
        _write(body)


def test_the_limit_is_2000_characters() -> None:
    assert MAX_MESSAGE_LENGTH == 2000
    assert len(_write("a" * 2000).body) == 2000


def test_a_message_of_2001_characters_is_refused() -> None:
    with pytest.raises(InvalidMessage):
        _write("a" * 2001)


def test_the_limit_counts_the_trimmed_message() -> None:
    assert len(_write("  " + "a" * 2000 + "  ").body) == 2000
