import asyncio
from uuid import UUID

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from patas_backend.models.user import EmailAlreadyRegistered, User, UserRepository

ANA_ID = UUID("0b1f2a3c-4d5e-4f60-8a7b-9c0d1e2f3a4b")
BOB_ID = UUID("5c6d7e8f-9a0b-4c1d-8e2f-3a4b5c6d7e8f")

Factory = async_sessionmaker[AsyncSession]


def _ana(**overrides: str) -> User:
    return User.provision(
        **{"id": ANA_ID, "name": "Ana", "email": "ana@example.com", **overrides}
    )


async def _ensure(factory: Factory, user: User) -> User:
    async with factory.begin() as session:
        return await UserRepository(session).ensure_exists(user)


async def _rows(engine: AsyncEngine) -> list[tuple[UUID, str, str, bool]]:
    async with engine.connect() as conn:
        result = await conn.execute(
            text("SELECT id, name, email, is_platform_admin FROM patas.users")
        )
        return [tuple(row) for row in result]


async def test_creates_the_user_on_first_call(
    engine: AsyncEngine, session_factory: Factory
) -> None:
    returned = await _ensure(session_factory, _ana())

    assert returned == _ana()
    assert await _rows(engine) == [(ANA_ID, "Ana", "ana@example.com", False)]


async def test_second_call_does_not_duplicate(
    engine: AsyncEngine, session_factory: Factory
) -> None:
    await _ensure(session_factory, _ana())
    returned = await _ensure(session_factory, _ana())

    assert returned == _ana()
    assert len(await _rows(engine)) == 1


async def test_existing_user_is_not_overwritten(
    engine: AsyncEngine, session_factory: Factory
) -> None:
    await _ensure(session_factory, _ana())

    returned = await _ensure(session_factory, _ana(name="Ana Maria"))

    assert returned.name == "Ana"
    assert await _rows(engine) == [(ANA_ID, "Ana", "ana@example.com", False)]


async def test_concurrent_first_requests_create_one_row(
    engine: AsyncEngine, session_factory: Factory
) -> None:
    results = await asyncio.gather(
        *(_ensure(session_factory, _ana()) for _ in range(5))
    )

    assert results == [_ana()] * 5
    assert len(await _rows(engine)) == 1


async def test_email_owned_by_another_user_is_rejected(
    engine: AsyncEngine, session_factory: Factory
) -> None:
    await _ensure(session_factory, _ana())

    with pytest.raises(EmailAlreadyRegistered):
        await _ensure(session_factory, _ana(id=BOB_ID, email="ANA@Example.com"))

    assert await _rows(engine) == [(ANA_ID, "Ana", "ana@example.com", False)]


async def test_admin_flag_comes_from_the_database(
    engine: AsyncEngine, session_factory: Factory
) -> None:
    async with engine.begin() as conn:
        await conn.execute(
            text(
                "INSERT INTO patas.users (id, name, email, is_platform_admin) "
                "VALUES (:id, 'Ana', 'ana@example.com', true)"
            ),
            {"id": ANA_ID},
        )

    returned = await _ensure(session_factory, _ana())

    assert returned.is_platform_admin is True


async def test_update_persists_name_change(
    engine: AsyncEngine, session_factory: Factory
) -> None:
    user = await _ensure(session_factory, _ana())
    user.change_name("Ana Silva")

    async with session_factory.begin() as session:
        updated = await UserRepository(session).update(user)

    assert updated.name == "Ana Silva"
    assert await _rows(engine) == [(ANA_ID, "Ana Silva", "ana@example.com", False)]

