"""Add sample adoption requests, one per status, on top of the `pnpm seed:demo`
animals. Safe to run again. Usage, with the stack running:

    docker compose exec backend python scripts/seed_applications.py
"""

import asyncio
import sys

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from patas_backend.config import Settings
from patas_backend.demo_applications import DemoDataMissing, seed_applications


async def main() -> int:
    engine = create_async_engine(Settings().database_url)
    try:
        created = await seed_applications(
            async_sessionmaker(engine, expire_on_commit=False)
        )
    except DemoDataMissing as error:
        print(error, file=sys.stderr)
        return 1
    finally:
        await engine.dispose()
    print(f"Added {created} demo adoption request(s).")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
