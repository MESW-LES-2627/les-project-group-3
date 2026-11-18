import asyncio
from uuid import uuid4

import pytest
from alembic.config import Config
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from alembic import command

INSERT_USER = text(
    "INSERT INTO patas.users (id, name, email, username) "
    "VALUES (:id, :name, :email, :username)"
)


async def _insert(
    engine: AsyncEngine, name: str, email: str, username: str | None = None
) -> None:
    # A fresh valid username by default, so only the column under test can refuse.
    params = {
        "id": uuid4(),
        "name": name,
        "email": email,
        "username": username or f"user_{uuid4().hex[:8]}",
    }
    async with engine.begin() as conn:
        await conn.execute(INSERT_USER, params)


async def test_rejects_blank_name(engine: AsyncEngine) -> None:
    with pytest.raises(IntegrityError):
        await _insert(engine, "   ", "ana@example.com")


async def test_rejects_email_without_at_sign(engine: AsyncEngine) -> None:
    with pytest.raises(IntegrityError):
        await _insert(engine, "Ana", "no-at-sign")


async def test_rejects_duplicate_email_ignoring_case(engine: AsyncEngine) -> None:
    await _insert(engine, "Ana", "Ana@Example.com")
    with pytest.raises(IntegrityError):
        await _insert(engine, "Another Ana", "ana@example.com")


async def test_admin_flag_defaults_to_false(engine: AsyncEngine) -> None:
    await _insert(engine, "Ana", "ana@example.com")
    async with engine.connect() as conn:
        is_admin = await conn.scalar(text("SELECT is_platform_admin FROM patas.users"))
    assert is_admin is False


async def test_updated_at_changes_on_update(engine: AsyncEngine) -> None:
    await _insert(engine, "Ana", "ana@example.com")
    async with engine.begin() as conn:
        await conn.execute(text("UPDATE patas.users SET name = 'Ana Maria'"))
    async with engine.connect() as conn:
        row = (
            await conn.execute(text("SELECT created_at, updated_at FROM patas.users"))
        ).one()
    assert row.updated_at > row.created_at


@pytest.mark.parametrize("username", ["an", "a" * 31, ".ana", "ana.", "ana demo"])
async def test_rejects_a_malformed_username(engine: AsyncEngine, username: str) -> None:
    with pytest.raises(IntegrityError, match="users_username_format_check"):
        await _insert(engine, "Ana", "ana@example.com", username)


async def test_rejects_a_duplicate_username_ignoring_case(engine: AsyncEngine) -> None:
    await _insert(engine, "Ana", "ana@example.com", "Ana.Demo")
    with pytest.raises(IntegrityError, match="idx_users_username_lower"):
        await _insert(engine, "Another Ana", "other@example.com", "ana.demo")


# --- 0008 on a throwaway database: users from before get a username ---------

_BEFORE_0008 = text(
    "INSERT INTO patas.users (id, name, email, created_at) "
    "VALUES (gen_random_uuid(), :name, :email, now() - make_interval(secs => :age))"
)


async def test_existing_users_get_a_username_from_their_name(
    scratch_database: tuple[Config, str],
) -> None:
    config, url = scratch_database
    await asyncio.to_thread(command.upgrade, config, "0007")
    engine = create_async_engine(url)
    people = [  # oldest first: the oldest "Ana Demo" keeps the plain form
        ("Ana Demo", 90),
        ("ana demo", 80),
        ("José Conceição", 70),
        ("Al", 60),
        ("Ana", 50),
        ("Ana2", 40),  # takes "ana2", so the next "Ana" must go on to "ana3"
        ("Ana", 30),
        ("a" * 40, 20),  # a suffix must still fit in 30 characters
        ("a" * 40, 10),
    ]
    async with engine.begin() as conn:
        for number, (name, age) in enumerate(people):
            email = f"user{number}@example.com"
            await conn.execute(_BEFORE_0008, {"name": name, "email": email, "age": age})

    await asyncio.to_thread(command.upgrade, config, "head")

    async with engine.connect() as conn:
        rows = await conn.execute(
            text("SELECT name, username FROM patas.users ORDER BY created_at")
        )
        usernames = [tuple(row) for row in rows]
    await engine.dispose()
    assert usernames == [
        ("Ana Demo", "ana_demo"),
        ("ana demo", "ana_demo2"),
        ("José Conceição", "jose_conceicao"),
        ("Al", "al_user"),
        ("Ana", "ana"),
        ("Ana2", "ana2"),
        ("Ana", "ana3"),
        ("a" * 40, "a" * 30),
        ("a" * 40, "a" * 29 + "2"),
    ]


async def test_downgrade_drops_the_username(
    scratch_database: tuple[Config, str],
) -> None:
    config, url = scratch_database
    await asyncio.to_thread(command.upgrade, config, "head")
    await asyncio.to_thread(command.downgrade, config, "0007")

    engine = create_async_engine(url)
    async with engine.connect() as conn:
        columns = await conn.scalar(
            text(
                "SELECT count(*) FROM information_schema.columns "
                "WHERE table_schema = 'patas' AND table_name = 'users' "
                "AND column_name = 'username'"
            )
        )
    await engine.dispose()
    assert columns == 0
