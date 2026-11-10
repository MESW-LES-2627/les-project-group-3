import pytest
import pytest_asyncio
from adoption_factory import World, seed_world
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker


@pytest.fixture
def session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False)


@pytest_asyncio.fixture
async def world(session_factory: async_sessionmaker[AsyncSession]) -> World:
    return await seed_world(session_factory)
