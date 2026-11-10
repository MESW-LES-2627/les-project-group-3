from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncEngine

INSERT_USER = text(
    "INSERT INTO patas.users (id, name, email) VALUES (:id, :name, :email)"
)


async def _insert(engine: AsyncEngine, name: str, email: str) -> None:
    async with engine.begin() as conn:
        await conn.execute(INSERT_USER, {"id": uuid4(), "name": name, "email": email})


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
