import asyncio
from uuid import uuid4

from adoption_factory import Factory, World, new_application, save

from patas_backend.models.adoption import AdoptionApplication
from patas_backend.models.animal import AnimalRepository
from patas_backend.services.locking import lock_animal_and_application


async def test_the_lock_helper_returns_only_the_application(
    session_factory: Factory, world: World
) -> None:
    application = new_application(world, applicant=world.bruno)
    await save(session_factory, application)

    async with session_factory.begin() as session:
        locked = await lock_animal_and_application(session, application.id)

    # The animal is locked, not handed out: a handler loads and saves its own copy,
    # so a copy kept here and saved later would revert what the handler did.
    assert isinstance(locked, AdoptionApplication)
    assert locked.id == application.id


async def test_the_helper_locks_the_animal_row_until_the_transaction_ends(
    session_factory: Factory, world: World
) -> None:
    application = new_application(world, applicant=world.bruno)
    await save(session_factory, application)

    async with session_factory() as holder, session_factory() as contender:
        await lock_animal_and_application(holder, application.id)
        waiting = asyncio.create_task(
            AnimalRepository(contender).get_for_update(world.rex)
        )
        done, _ = await asyncio.wait({waiting}, timeout=0.5)
        assert not done  # still waiting for the animal's lock

        await holder.commit()  # releases it
        animal = await asyncio.wait_for(waiting, timeout=5)

    assert animal is not None


async def test_a_missing_application_returns_none(
    session_factory: Factory, world: World
) -> None:
    async with session_factory() as session:
        assert await lock_animal_and_application(session, uuid4()) is None
