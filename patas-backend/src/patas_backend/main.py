from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from patas_backend.auth.api import router as auth_router
from patas_backend.auth.keys import JwksKeyProvider, RemoteJwksKeyProvider
from patas_backend.auth.verifier import JwtVerifier
from patas_backend.config import Settings
from patas_backend.routers import animals, compatibility, health, matchmaker_profile


def create_app(
    settings: Settings | None = None,
    key_provider: JwksKeyProvider | None = None,
) -> FastAPI:
    """Build the app. `key_provider` is the seam tests use to inject a key set."""
    settings = settings or Settings()
    engine = create_async_engine(settings.database_url)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        yield
        await engine.dispose()

    app = FastAPI(title="Patas", lifespan=lifespan)
    app.state.engine = engine
    app.state.session_factory = async_sessionmaker(engine, expire_on_commit=False)
    app.state.verifier = JwtVerifier(
        key_provider or RemoteJwksKeyProvider(settings.jwks_url),
        issuer=settings.jwt_issuer,
        audience=settings.jwt_audience,
    )

    app.include_router(auth_router)
    app.include_router(animals.router)
    app.include_router(matchmaker_profile.router)
    app.include_router(compatibility.router)
    app.include_router(health.router)

    return app


app = create_app()
