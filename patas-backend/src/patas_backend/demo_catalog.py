"""A large catalog for checking the paging by hand (#58): many users, each with a
few animals that vary in species, size, district and age.

The users exist only in the backend, so they cannot sign in; the catalog is public.
Running it again adds nothing: every id comes from its number.
"""

from uuid import NAMESPACE_URL, uuid5

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from patas_backend.models.animal import (
    Animal,
    AnimalRepository,
    AnimalSize,
    District,
    Species,
)
from patas_backend.models.user import User, UserRepository

_NAMESPACE = uuid5(NAMESPACE_URL, "patas:catalog-load")
_SPECIES = list(Species)
_SIZES = list(AnimalSize)
_DISTRICTS = list(District)


async def seed_catalog(
    factory: async_sessionmaker[AsyncSession], *, animals: int, users: int
) -> int:
    """Publish up to `animals` animals among `users` owners; return how many are new."""
    owners = [
        User.provision(
            id=uuid5(_NAMESPACE, f"user-{n}"),
            name=f"Load User {n:03d}",
            email=f"load.user{n:03d}@example.test",
        )
        for n in range(users)
    ]
    async with factory.begin() as session:
        repo = UserRepository(session)
        for owner in owners:
            await repo.ensure_exists(owner)

    created = 0
    for n in range(animals):
        animal = Animal(
            id=uuid5(_NAMESPACE, f"animal-{n}"),
            owner_id=owners[n % users].id,
            name=f"Load {n:03d}",
            species=_SPECIES[n % len(_SPECIES)],
            size=_SIZES[n % len(_SIZES)],
            district=_DISTRICTS[n % len(_DISTRICTS)],
            age_in_months=None if n % 10 == 0 else (n * 7) % 180,
        )
        # One transaction each, so each animal is newer than the last and the
        # catalog order (newest first) is the reverse of the numbers.
        async with factory.begin() as session:
            repo = AnimalRepository(session)
            if await repo.get_by_id(animal.id) is None:
                await repo.add(animal)
                created += 1
    return created
