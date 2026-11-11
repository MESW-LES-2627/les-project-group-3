import httpx
from compatibility_endpoint import (
    ANA,
    CARLA,
    MILO,
    UNKNOWN_ANIMAL,
    _as,
    _publish,
    _save_home,
    _url,
)
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker
from token_issuer import TokenIssuer

from patas_backend.models.animal import (
    AnimalRepository,
)


async def test_an_unknown_animal_is_404(
    client: httpx.AsyncClient, issuer: TokenIssuer, engine: AsyncEngine
) -> None:
    await _save_home(client, issuer, CARLA)

    response = await client.get(
        f"/animals/{UNKNOWN_ANIMAL}/compatibility", headers=_as(issuer, CARLA)
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Animal not found"}


async def test_an_unpublished_animal_is_404(
    client: httpx.AsyncClient, issuer: TokenIssuer, engine: AsyncEngine
) -> None:
    animal = await _publish(engine, **MILO)
    animal.unpublish(by_user_id=ANA.id)
    async with async_sessionmaker(engine).begin() as session:
        await AnimalRepository(session).update(animal)
    await _save_home(client, issuer, CARLA)

    response = await client.get(_url(animal), headers=_as(issuer, CARLA))

    # The detail tells our 404 from the router's "Not Found" for an unknown route.
    assert response.status_code == 404
    assert response.json() == {"detail": "Animal not found"}
