from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from patas_backend.demo_catalog import seed_catalog
from patas_backend.models.animal import Animal, AnimalRepository, District, Species

Factory = async_sessionmaker[AsyncSession]


async def _catalog(factory: Factory) -> list[Animal]:
    async with factory() as session:
        return await AnimalRepository(session).list_all()


async def test_it_spreads_the_animals_over_the_owners_newest_last(
    session_factory: Factory,
) -> None:
    created = await seed_catalog(session_factory, animals=30, users=4)

    catalog = await _catalog(session_factory)
    assert created == 30
    assert [a.name for a in catalog] == [f"Load {n:03d}" for n in reversed(range(30))]
    assert len({a.owner_id for a in catalog}) == 4
    assert {a.species for a in catalog} == set(Species)
    assert {a.district for a in catalog} == set(District)


async def test_running_it_again_adds_nothing(session_factory: Factory) -> None:
    await seed_catalog(session_factory, animals=5, users=2)

    assert await seed_catalog(session_factory, animals=5, users=2) == 0
    assert len(await _catalog(session_factory)) == 5
