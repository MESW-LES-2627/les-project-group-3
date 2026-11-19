from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from patas_backend.models.user import User, UserRepository, validate_username


class UserService:
    """Profile use cases for the logged-in user. Each one owns its transaction."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def update_profile(
        self, user: User, *, name: str | None = None, username: str | None = None
    ) -> User:
        """Change the name, the username or both.

        Raises InvalidUser for a blank name or a malformed username, and
        UsernameTaken when another user has the username; nothing changes then.
        """
        async with self._session_factory.begin() as session:
            repo = UserRepository(session)
            # Locked and reloaded: a concurrent change to the other field is kept.
            current = await repo.get_for_update(user.id)
            if name is not None:
                current.change_name(name)
            if username is not None:
                current.change_username(username)
            return await repo.update(current)

    async def is_username_available(self, username: str) -> bool:
        """Whether nobody has the username, ignoring case.

        Raises InvalidUser when the username is malformed.
        """
        cleaned = validate_username(username)
        async with self._session_factory() as session:
            return not await UserRepository(session).is_username_taken(cleaned)
