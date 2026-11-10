from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine
from token_issuer import AUDIENCE, ISSUER, TokenIssuer

from patas_backend.auth.keys import StaticJwksKeyProvider
from patas_backend.config import Settings
from patas_backend.main import create_app

ALEMBIC_INI = Path(__file__).resolve().parents[3] / "alembic.ini"


async def test_startup_migrates_the_database_inside_the_servers_event_loop(
    migrated_database_url: str, issuer: TokenIssuer, engine: AsyncEngine
) -> None:
    # The other tests' clients never run the lifespan, so this is the only place the
    # startup migration runs, from a running loop as under uvicorn.
    settings = Settings(
        database_url=migrated_database_url, jwt_issuer=ISSUER, jwt_audience=AUDIENCE
    )
    app = create_app(settings, StaticJwksKeyProvider(issuer.jwks()))

    async with app.router.lifespan_context(app):
        pass

    head = ScriptDirectory.from_config(Config(str(ALEMBIC_INI))).get_current_head()
    async with engine.connect() as conn:
        version = await conn.scalar(
            text("SELECT version_num FROM patas.alembic_version")
        )
    assert version == head
