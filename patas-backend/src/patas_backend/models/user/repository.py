from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from patas_backend.models.user.user import User

EMAIL_UNIQUE_INDEX = "idx_users_email_lower"

_INSERT = text(
    """
    INSERT INTO patas.users (id, name, email)
    VALUES (:id, :name, :email)
    ON CONFLICT (id) DO NOTHING
    """
)
_SELECT = text(
    "SELECT id, name, email, is_platform_admin FROM patas.users WHERE id = :id"
)
_UPDATE = text(
    """
    UPDATE patas.users
    SET name = :name
    WHERE id = :id
    RETURNING id, name, email, is_platform_admin
    """
)


class EmailAlreadyRegistered(Exception):
    """The email already belongs to a different user id."""


class UserRepository:
    """Persistence for User. The caller owns the transaction (this never commits)."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def ensure_exists(self, user: User) -> User:
        """Create the user if the id is new, and return the stored row.

        A single INSERT ... ON CONFLICT is atomic, so concurrent first requests
        for the same id cannot race. The stored row is returned, never the
        argument: the database is the source of truth (e.g. is_platform_admin).
        """
        try:
            await self._session.execute(
                _INSERT, {"id": user.id, "name": user.name, "email": user.email}
            )
        except IntegrityError as error:
            if _violates_email_uniqueness(error):
                raise EmailAlreadyRegistered(user.email) from error
            raise
        row = (await self._session.execute(_SELECT, {"id": user.id})).one()
        return User(
            id=row.id,
            name=row.name,
            email=row.email,
            is_platform_admin=row.is_platform_admin,
        )

    async def update(self, user: User) -> User:
        """Update an existing user's mutable attributes and return the stored row."""
        row = (
            await self._session.execute(_UPDATE, {"id": user.id, "name": user.name})
        ).one()
        return User(
            id=row.id,
            name=row.name,
            email=row.email,
            is_platform_admin=row.is_platform_admin,
        )


def _violates_email_uniqueness(error: IntegrityError) -> bool:
    # error.orig is SQLAlchemy's adapter; its __cause__ is the asyncpg exception.
    driver_error = error.orig.__cause__ if error.orig else None
    return getattr(driver_error, "constraint_name", None) == EMAIL_UNIQUE_INDEX
