import asyncio
from collections.abc import AsyncIterator, Callable
from pathlib import Path

import httpx
import pytest
import pytest_asyncio
from alembic.config import Config
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from token_issuer import AUDIENCE, ISSUER, TokenIssuer

from alembic import command
from patas_backend.auth.keys import JwksKeyProvider, StaticJwksKeyProvider
from patas_backend.config import Settings
from patas_backend.main import create_app

TEST_DATABASE = "patas_test"
ALEMBIC_INI = Path(__file__).resolve().parents[1] / "alembic.ini"


def _test_database_url() -> str:
    url = make_url(Settings().database_url)
    return url.set(database=TEST_DATABASE).render_as_string(hide_password=False)


async def _create_test_database_if_missing() -> None:
    admin = create_async_engine(Settings().database_url, isolation_level="AUTOCOMMIT")
    async with admin.connect() as conn:
        exists = await conn.scalar(
            text("SELECT 1 FROM pg_database WHERE datname = :name"),
            {"name": TEST_DATABASE},
        )
        if not exists:
            await conn.execute(text(f"CREATE DATABASE {TEST_DATABASE}"))
    await admin.dispose()


async def _drop_domain_schema(url: str) -> None:
    engine = create_async_engine(url)
    async with engine.begin() as conn:
        await conn.execute(text("DROP SCHEMA IF EXISTS patas CASCADE"))
        await conn.execute(text("DROP SCHEMA IF EXISTS patas_auth CASCADE"))
    await engine.dispose()


@pytest.fixture(scope="session")
def migrated_database_url() -> str:
    """A real PostgreSQL database with every migration applied from scratch."""
    url = _test_database_url()
    asyncio.run(_create_test_database_if_missing())
    asyncio.run(_drop_domain_schema(url))

    config = Config(str(ALEMBIC_INI))
    config.set_main_option("sqlalchemy.url", url)
    command.upgrade(config, "head")
    return url


@pytest_asyncio.fixture
async def engine(migrated_database_url: str) -> AsyncIterator[AsyncEngine]:
    engine = create_async_engine(migrated_database_url)
    async with engine.begin() as conn:
        await conn.execute(text("TRUNCATE patas.users CASCADE"))
    yield engine
    await engine.dispose()


ClientFactory = Callable[[JwksKeyProvider], httpx.AsyncClient]


@pytest_asyncio.fixture
async def make_client(
    engine: AsyncEngine, migrated_database_url: str
) -> AsyncIterator[ClientFactory]:
    """Builds clients for the real FastAPI app, wired to the test database."""
    settings = Settings(
        database_url=migrated_database_url, jwt_issuer=ISSUER, jwt_audience=AUDIENCE
    )
    clients: list[httpx.AsyncClient] = []
    apps = []

    def build(key_provider: JwksKeyProvider) -> httpx.AsyncClient:
        app = create_app(settings, key_provider)
        client = httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://testserver"
        )
        apps.append(app)
        clients.append(client)
        return client

    yield build
    for client in clients:
        await client.aclose()
    for app in apps:
        await app.state.engine.dispose()


@pytest.fixture
def client(make_client: ClientFactory, issuer: TokenIssuer) -> httpx.AsyncClient:
    return make_client(StaticJwksKeyProvider(issuer.jwks()))


@pytest.fixture
def issuer() -> TokenIssuer:
    return TokenIssuer()


@pytest.fixture
def other_issuer() -> TokenIssuer:
    """A different keypair that reuses the same key id."""
    return TokenIssuer()


KINDS = ("unit", "integration", "acceptance")
TESTS_DIRECTORY = Path(__file__).parent


def pytest_collection_modifyitems(
    config: pytest.Config, items: list[pytest.Item]
) -> None:
    """Mark every test with its kind, which is the folder it lives in."""
    for item in items:
        relative = item.path.relative_to(TESTS_DIRECTORY)
        kind = relative.parts[0]
        if kind not in KINDS:
            raise pytest.UsageError(
                f"{relative}: tests must live in tests/unit, tests/integration "
                "or tests/acceptance"
            )
        item.add_marker(getattr(pytest.mark, kind))
