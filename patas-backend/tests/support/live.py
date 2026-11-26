"""A stand-in for Ably in tests: it remembers what would have been published."""

from uuid import UUID


class RecordingPublisher:
    def __init__(self) -> None:
        self.sent: list[tuple[UUID, str, dict[str, str]]] = []

    async def publish(self, user_id: UUID, name: str, data: dict[str, str]) -> None:
        self.sent.append((user_id, name, data))

    async def close(self) -> None:
        return None

    def for_user(self, user_id: UUID | str) -> list[tuple[str, dict[str, str]]]:
        """What one person's channel received, in order."""
        wanted = UUID(str(user_id))
        return [(name, data) for who, name, data in self.sent if who == wanted]


class FailingPublisher(RecordingPublisher):
    """Ably is down: every publish raises."""

    async def publish(self, user_id: UUID, name: str, data: dict[str, str]) -> None:
        raise ConnectionError("Ably is unreachable")
