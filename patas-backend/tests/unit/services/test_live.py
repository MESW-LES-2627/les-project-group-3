from uuid import UUID

from patas_backend.services.live import NullPublisher, channel_for

ANA = UUID("11111111-1111-1111-1111-111111111111")


def test_each_person_has_one_channel_named_after_them() -> None:
    # The frontend's token route grants exactly this name, so both must agree.
    assert channel_for(ANA) == "user:11111111-1111-1111-1111-111111111111"


async def test_without_ably_publishing_does_nothing_and_never_fails() -> None:
    publisher = NullPublisher()

    await publisher.publish(ANA, "message.posted", {"application_id": "x"})
    await publisher.close()
