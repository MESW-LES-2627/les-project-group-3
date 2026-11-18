"""#58: GET /animals returns one page of 24 and the total in X-Total-Count."""

from uuid import uuid4

import httpx
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from patas_backend.models.animal import Animal, AnimalRepository, Species
from patas_backend.models.user import User, UserRepository

Factory = async_sessionmaker[AsyncSession]


async def _publish(factory: Factory, count: int, species: Species) -> list[str]:
    """Publish `count` animals, each in its own transaction so each is newer.

    Returns their names, newest first, the catalog's order."""
    owner = User.provision(id=uuid4(), name="Ana", email=f"{uuid4()}@example.com")
    async with factory.begin() as session:
        await UserRepository(session).ensure_exists(owner)
    names = []
    for number in range(count):
        name = f"{species.value} {number:02d}"
        async with factory.begin() as session:
            await AnimalRepository(session).add(
                Animal.publish(owner_id=owner.id, name=name, species=species)
            )
        names.append(name)
    return names[::-1]


def _names(response: httpx.Response) -> list[str]:
    return [animal["name"] for animal in response.json()]


async def test_the_catalog_is_split_into_pages_of_24_newest_first(
    client: httpx.AsyncClient, session_factory: Factory
) -> None:
    newest_first = await _publish(session_factory, 30, Species.DOG)

    first = await client.get("/animals")
    second = await client.get("/animals?page=2")
    past_the_end = await client.get("/animals?page=3")

    assert _names(first) == newest_first[:24]
    assert _names(second) == newest_first[24:]
    assert past_the_end.json() == []
    assert {r.headers["X-Total-Count"] for r in (first, second, past_the_end)} == {"30"}


async def test_filters_apply_before_paging_and_to_the_total(
    client: httpx.AsyncClient, session_factory: Factory
) -> None:
    cats = await _publish(session_factory, 26, Species.CAT)
    # Newer than every cat, so paging before filtering would shift the cats.
    await _publish(session_factory, 3, Species.DOG)

    second = await client.get("/animals?species=cat&page=2")

    assert _names(second) == cats[24:]
    assert second.headers["X-Total-Count"] == "26"


async def test_an_empty_catalog_counts_zero(client: httpx.AsyncClient) -> None:
    response = await client.get("/animals")

    assert response.json() == []
    assert response.headers["X-Total-Count"] == "0"


@pytest.mark.parametrize("page", ["0", "-1", "two"])
async def test_a_page_that_is_not_a_positive_number_is_refused(
    client: httpx.AsyncClient, page: str
) -> None:
    assert (await client.get(f"/animals?page={page}")).status_code == 422
