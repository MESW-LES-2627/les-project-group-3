from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker

from patas_backend.models.animal import Animal, AnimalRepository, Species
from patas_backend.models.user import User, UserRepository

OWNER = User.provision(
    id=UUID("c3a1f0d2-7b64-4e19-9d85-0a2b3c4d5e6f"),
    name="Ana",
    email="ana@example.com",
)


async def _publish(
    engine: AsyncEngine,
    name: str,
    owner: User = OWNER,
    **fields: object,
) -> Animal:
    animal = Animal.publish(
        owner_id=owner.id,
        owner_name=owner.name,
        name=name,
        species=Species.DOG,
        **fields,  # type: ignore[arg-type]
    )
    async with async_sessionmaker(engine).begin() as session:
        await UserRepository(session).ensure_exists(owner)
        await AnimalRepository(session).add(animal)
    return animal


def _owner_claims() -> dict[str, str]:
    return {"sub": str(OWNER.id), "name": OWNER.name, "email": OWNER.email}
