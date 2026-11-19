"""Fill the catalog for the paging check (#58). Safe to run again. Usage, with the
stack running (defaults: 300 animals among 100 users):

    docker compose exec backend python scripts/seed_catalog.py [animals] [users]
"""

import asyncio
import sys

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from patas_backend.config import Settings
from patas_backend.demo_catalog import seed_catalog


async def main(animals: int, users: int) -> int:
    engine = create_async_engine(Settings().database_url)
    try:
        created = await seed_catalog(
            async_sessionmaker(engine, expire_on_commit=False),
            animals=animals,
            users=users,
        )
    finally:
        await engine.dispose()
    print(f"Added {created} animal(s) among {users} user(s).")
    return 0


if __name__ == "__main__":
    args = sys.argv[1:]
    animals = int(args[0]) if args else 300
    users = int(args[1]) if len(args) > 1 else 100
    if animals < 0 or users < 1:
        sys.exit("usage: seed_catalog.py [animals >= 0] [users >= 1]")
    sys.exit(asyncio.run(main(animals, users)))
