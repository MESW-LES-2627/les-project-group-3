from typing import Any
from uuid import UUID

from sqlalchemy import Row, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from patas_backend.models.user.user import User
from patas_backend.models.user.username import username_candidates

EMAIL_UNIQUE_INDEX = "idx_users_email_lower"
USERNAME_UNIQUE_INDEX = "idx_users_username_lower"

_COLUMNS = "id, name, email, username, is_platform_admin"

_INSERT = text(
    """
    INSERT INTO patas.users (id, name, email, username)
    VALUES (:id, :name, :email, :username)
    ON CONFLICT (id) DO NOTHING
    """
)
_SELECT = text(f"SELECT {_COLUMNS} FROM patas.users WHERE id = :id")
_SELECT_FOR_UPDATE = text(
    f"SELECT {_COLUMNS} FROM patas.users WHERE id = :id FOR UPDATE"
)
_UPDATE = text(
    f"""
    UPDATE patas.users
    SET name = :name, username = :username
    WHERE id = :id
    RETURNING {_COLUMNS}
    """
)
_USERNAME_EXISTS = text(
    "SELECT EXISTS (SELECT 1 FROM patas.users WHERE lower(username) = lower(:username))"
)


class EmailAlreadyRegistered(Exception):
    """The email already belongs to a different user id."""


class UsernameTaken(Exception):
    """The username already belongs to another user, ignoring case."""


class UserRepository:
    """Persistence for User. The caller owns the transaction (this never commits)."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def ensure_exists(self, user: User) -> User:
        """Create the user if the id is new, and return the stored row.

        The stored row is returned, never the argument: the database is the source
        of truth (e.g. is_platform_admin). A new user whose derived username is
        taken gets the next free candidate (ana_demo2 ...). INSERT ... ON CONFLICT
        (id) keeps concurrent first requests for the same id from racing.
        """
        row = (await self._session.execute(_SELECT, {"id": user.id})).one_or_none()
        if row is not None:
            return _from_row(row)
        for username in username_candidates(user.username, fallback=user.id.hex[:8]):
            try:
                # A savepoint per attempt: a refused INSERT must not abort the
                # caller's transaction.
                async with self._session.begin_nested():
                    await self._session.execute(
                        _INSERT,
                        {
                            "id": user.id,
                            "name": user.name,
                            "email": user.email,
                            "username": username,
                        },
                    )
                break
            except IntegrityError as error:
                if _violates(error, EMAIL_UNIQUE_INDEX):
                    raise EmailAlreadyRegistered(user.email) from error
                if not _violates(error, USERNAME_UNIQUE_INDEX):
                    raise
        else:
            raise UsernameTaken(user.username)
        row = (await self._session.execute(_SELECT, {"id": user.id})).one()
        return _from_row(row)

    async def get_for_update(self, user_id: UUID) -> User:
        """Load an existing user and lock the row until the transaction ends."""
        row = (await self._session.execute(_SELECT_FOR_UPDATE, {"id": user_id})).one()
        return _from_row(row)

    async def update(self, user: User) -> User:
        """Store the user's name and username and return the stored row."""
        try:
            row = (
                await self._session.execute(
                    _UPDATE,
                    {"id": user.id, "name": user.name, "username": user.username},
                )
            ).one()
        except IntegrityError as error:
            if _violates(error, USERNAME_UNIQUE_INDEX):
                raise UsernameTaken(user.username) from error
            raise
        return _from_row(row)

    async def is_username_taken(self, username: str) -> bool:
        return bool(
            await self._session.scalar(_USERNAME_EXISTS, {"username": username})
        )


def _from_row(row: Row[Any]) -> User:
    return User(
        id=row.id,
        name=row.name,
        email=row.email,
        username=row.username,
        is_platform_admin=row.is_platform_admin,
    )


def _violates(error: IntegrityError, index: str) -> bool:
    # error.orig is SQLAlchemy's adapter; its __cause__ is the asyncpg exception.
    driver_error = error.orig.__cause__ if error.orig else None
    return getattr(driver_error, "constraint_name", None) == index
