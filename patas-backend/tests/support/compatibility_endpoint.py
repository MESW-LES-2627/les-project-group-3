from uuid import UUID

import httpx
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker
from token_issuer import TokenIssuer

from patas_backend.models.animal import (
    Animal,
    AnimalRepository,
    AnimalSize,
    FirstTimeOwnerSuitability,
    Species,
)
from patas_backend.models.matching import EnergyLevel
from patas_backend.models.user import User, UserRepository

CARLA = {"sub": "5d0c7a52-3b1e-4c8f-9a6d-2e4f8b1c7d90",
         "email": "carla@example.com", "name": "Carla"}  # fmt: skip
BRUNO = {"sub": "8e1f3b6a-2c4d-4e5f-8a7b-1c2d3e4f5a6b",
         "email": "bruno@example.com", "name": "Bruno"}  # fmt: skip
ANA = User.provision(
    id=UUID("c3a1f0d2-7b64-4e19-9d85-0a2b3c4d5e6f"),
    name="Ana",
    email="ana@example.com",
)

# The worked example: an apartment, away half a day, some experience, no household.
HOME = {
    "housing": "apartment",
    "activity": "moderate",
    "time_away": "half_day",
    "experience": "some",
    "has_children": False,
    "has_dogs": False,
    "has_cats": False,
}
# Moderate energy, a few hours alone, fine for a first-timer, needs medium space.
MILO = {
    "activity_level": EnergyLevel.MODERATE,
    "tolerance_for_time_alone": EnergyLevel.LOW,
    "suitable_for_first_time_owners": FirstTimeOwnerSuitability.YES,
    "space_requirement": AnimalSize.MEDIUM,
}
UNKNOWN_ANIMAL = "00000000-0000-4000-8000-000000000000"


def _as(issuer: TokenIssuer, person: dict[str, str]) -> dict[str, str]:
    return {"Authorization": f"Bearer {issuer.token(**person)}"}


async def _publish(engine: AsyncEngine, owner: User = ANA, **fields: object) -> Animal:
    animal = Animal.publish(
        owner_id=owner.id,
        name="Milo",
        species=Species.DOG,
        age_in_months=36,
        **fields,  # type: ignore[arg-type]
    )
    async with async_sessionmaker(engine).begin() as session:
        await UserRepository(session).ensure_exists(owner)
        await AnimalRepository(session).add(animal)
    return animal


async def _save_home(
    client: httpx.AsyncClient,
    issuer: TokenIssuer,
    person: dict[str, str],
    **changes: object,
) -> None:
    saved = await client.put(
        "/me/matchmaker-profile",
        json={**HOME, **changes},
        headers=_as(issuer, person),
    )
    assert saved.status_code == 200


def _url(animal: Animal, mode: str | None = None) -> str:
    base = f"/animals/{animal.id}/compatibility"
    return base if mode is None else f"{base}?mode={mode}"
