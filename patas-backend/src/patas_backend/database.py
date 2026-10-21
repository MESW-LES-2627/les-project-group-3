import os
import ssl

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://patas_admin:securepassword@localhost:5433/patas_db",
)

ssl_context = ssl.create_default_context()

connect_args = {
    "server_settings": {
        "search_path": "patas,public",
    },
}

# Only require SSL when not connecting to local Docker Postgres
if "localhost" not in DATABASE_URL and "127.0.0.1" not in DATABASE_URL:
    connect_args["ssl"] = ssl_context

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    connect_args=connect_args,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)