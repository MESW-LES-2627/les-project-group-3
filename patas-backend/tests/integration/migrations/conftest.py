from collections.abc import AsyncIterator
from pathlib import Path

import pytest_asyncio
from alembic.config import Config
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import create_async_engine

from patas_backend.config import Settings

ALEMBIC_INI = Path(__file__).resolve().parents[3] / "alembic.ini"
SCRATCH_DATABASE = "patas_migration_scratch"


@pytest_asyncio.fixture
async def scratch_database() -> AsyncIterator[tuple[Config, str]]:
    """An empty database of its own, so a failure cannot break the shared one."""
    base = Settings().database_url
    admin = create_async_engine(base, isolation_level="AUTOCOMMIT")
    drop = text(f"DROP DATABASE IF EXISTS {SCRATCH_DATABASE} WITH (FORCE)")
    async with admin.connect() as conn:
        await conn.execute(drop)
        await conn.execute(text(f"CREATE DATABASE {SCRATCH_DATABASE}"))
    url = (
        make_url(base)
        .set(database=SCRATCH_DATABASE)
        .render_as_string(hide_password=False)
    )
    config = Config(str(ALEMBIC_INI))
    config.set_main_option("sqlalchemy.url", url)
    yield config, url
    async with admin.connect() as conn:
        await conn.execute(drop)
    await admin.dispose()
