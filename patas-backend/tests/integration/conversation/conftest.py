import pytest_asyncio
from adoption_factory import World, seed_world
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


@pytest_asyncio.fixture
async def world(session_factory: async_sessionmaker[AsyncSession]) -> World:
    return await seed_world(session_factory)
