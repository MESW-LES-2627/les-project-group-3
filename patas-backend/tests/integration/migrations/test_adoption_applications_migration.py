import asyncio
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from pathlib import Path
from typing import NamedTuple
from uuid import UUID, uuid4

import pytest
import pytest_asyncio
from alembic.config import Config
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from alembic import command
from patas_backend.config import Settings

ALEMBIC_INI = Path(__file__).resolve().parents[3] / "alembic.ini"
SCRATCH_DATABASE = "patas_migration_scratch"
NOW = datetime.now(UTC)

INSERT_USER = text(
    "INSERT INTO patas.users (id, name, email) VALUES (:id, :name, :email)"
)
INSERT_ANIMAL = text(
    "INSERT INTO patas.animals (id, owner_id, name, species) "
    "VALUES (:id, :owner_id, 'Rex', 'dog')"
)
INSERT_APPLICATION = text(
    """
    INSERT INTO patas.adoption_applications
        (id, animal_id, owner_id, applicant_id, applicant_note, applicant_profile,
         status, owner_confirmed_at, applicant_confirmed_at)
    VALUES (:id, :animal_id, :owner_id, :applicant_id, 'Hello', CAST('{}' AS jsonb),
            CAST(:status AS patas.application_status),
            :owner_confirmed_at, :applicant_confirmed_at)
    """
)


class World(NamedTuple):
    owner: UUID
    bruno: UUID
    carla: UUID
    animal: UUID


@pytest_asyncio.fixture
async def world(engine: AsyncEngine) -> World:
    ids = World(uuid4(), uuid4(), uuid4(), uuid4())
    people = ((ids.owner, "Ana"), (ids.bruno, "Bruno"), (ids.carla, "Carla"))
    async with engine.begin() as conn:
        for user_id, name in people:
            email = f"{name.lower()}@example.com"
            await conn.execute(
                INSERT_USER, {"id": user_id, "name": name, "email": email}
            )
        await conn.execute(INSERT_ANIMAL, {"id": ids.animal, "owner_id": ids.owner})
    return ids


async def _apply(
    engine: AsyncEngine,
    world: World,
    *,
    applicant: UUID | None = None,
    status: str = "open",
    owner_confirmed: bool = False,
    applicant_confirmed: bool = False,
) -> None:
    async with engine.begin() as conn:
        await conn.execute(
            INSERT_APPLICATION,
            {
                "id": uuid4(),
                "animal_id": world.animal,
                "owner_id": world.owner,
                "applicant_id": applicant or world.bruno,
                "status": status,
                "owner_confirmed_at": NOW if owner_confirmed else None,
                "applicant_confirmed_at": NOW if applicant_confirmed else None,
            },
        )


async def _count(engine: AsyncEngine) -> int:
    async with engine.connect() as conn:
        return await conn.scalar(
            text("SELECT count(*) FROM patas.adoption_applications")
        )


# --- the table's rules -------------------------------------------------------


async def test_new_animals_still_default_to_available(
    engine: AsyncEngine, world: World
) -> None:
    async with engine.connect() as conn:
        status = await conn.scalar(
            text("SELECT adoption_status::text FROM patas.animals WHERE id = :id"),
            {"id": world.animal},
        )
    assert status == "available"


async def test_rejects_applicant_equal_to_owner(
    engine: AsyncEngine, world: World
) -> None:
    with pytest.raises(IntegrityError, match="applicant_not_owner_check"):
        await _apply(engine, world, applicant=world.owner)


@pytest.mark.parametrize("status", ["open", "closed"])
async def test_rejects_a_confirmation_on_an_open_or_closed_application(
    engine: AsyncEngine, world: World, status: str
) -> None:
    with pytest.raises(IntegrityError, match="confirmations_status_check"):
        await _apply(engine, world, status=status, owner_confirmed=True)


@pytest.mark.parametrize("status", ["accepted", "declined", "withdrawn"])
async def test_accepted_declined_and_withdrawn_may_keep_a_confirmation(
    engine: AsyncEngine, world: World, status: str
) -> None:
    await _apply(engine, world, status=status, owner_confirmed=True)
    assert await _count(engine) == 1


@pytest.mark.parametrize(
    ("owner_confirmed", "applicant_confirmed"),
    [(False, False), (True, False), (False, True)],
)
async def test_rejects_adopted_without_both_confirmations(
    engine: AsyncEngine, world: World, owner_confirmed: bool, applicant_confirmed: bool
) -> None:
    with pytest.raises(IntegrityError, match="adopted_both_confirmed_check"):
        await _apply(
            engine,
            world,
            status="adopted",
            owner_confirmed=owner_confirmed,
            applicant_confirmed=applicant_confirmed,
        )


async def test_adopted_with_both_confirmations_is_accepted(
    engine: AsyncEngine, world: World
) -> None:
    await _apply(
        engine, world, status="adopted", owner_confirmed=True, applicant_confirmed=True
    )
    assert await _count(engine) == 1


async def test_a_second_accepted_application_for_one_animal_is_rejected(
    engine: AsyncEngine, world: World
) -> None:
    await _apply(engine, world, applicant=world.bruno, status="accepted")
    with pytest.raises(IntegrityError, match="one_accepted_per_animal"):
        await _apply(engine, world, applicant=world.carla, status="accepted")


@pytest.mark.parametrize("second", ["open", "accepted"])
async def test_an_applicant_has_one_active_application_per_animal(
    engine: AsyncEngine, world: World, second: str
) -> None:
    await _apply(engine, world, status="open")
    with pytest.raises(IntegrityError, match="one_active_per_applicant"):
        await _apply(engine, world, status=second)


@pytest.mark.parametrize("finished", ["declined", "withdrawn", "closed"])
async def test_a_finished_application_does_not_block_a_new_request(
    engine: AsyncEngine, world: World, finished: str
) -> None:
    await _apply(engine, world, status=finished)
    await _apply(engine, world, status=finished)
    await _apply(engine, world, status="open")
    assert await _count(engine) == 3


async def test_deleting_the_applicant_deletes_their_applications(
    engine: AsyncEngine, world: World
) -> None:
    await _apply(engine, world, applicant=world.bruno)
    await _apply(engine, world, applicant=world.carla)
    async with engine.begin() as conn:
        await conn.execute(
            text("DELETE FROM patas.users WHERE id = :id"), {"id": world.bruno}
        )
    assert await _count(engine) == 1


async def test_deleting_an_animal_with_applications_is_restricted(
    engine: AsyncEngine, world: World
) -> None:
    await _apply(engine, world)
    with pytest.raises(IntegrityError, match="animal_id_fkey"):
        async with engine.begin() as conn:
            await conn.execute(
                text("DELETE FROM patas.animals WHERE id = :id"),
                {"id": world.animal},
            )


# --- the enum change, on a throwaway database -------------------------------


@pytest_asyncio.fixture
async def scratch_database() -> AsyncIterator[tuple[Config, str]]:
    """An empty database of its own, so a failure cannot break the shared one."""
    base = Settings().database_url
    admin = create_async_engine(base, isolation_level="AUTOCOMMIT")
    drop = text(f"DROP DATABASE IF EXISTS {SCRATCH_DATABASE} WITH (FORCE)")
    async with admin.connect() as conn:
        await conn.execute(drop)
        await conn.execute(text(f"CREATE DATABASE {SCRATCH_DATABASE}"))
    url = (
        make_url(base)
        .set(database=SCRATCH_DATABASE)
        .render_as_string(hide_password=False)
    )
    config = Config(str(ALEMBIC_INI))
    config.set_main_option("sqlalchemy.url", url)
    yield config, url
    async with admin.connect() as conn:
        await conn.execute(drop)
    await admin.dispose()


_LABELS = text("SELECT unnest(enum_range(NULL::patas.adoption_status))::text")


async def test_in_trial_rows_become_reserved(
    scratch_database: tuple[Config, str],
) -> None:
    config, url = scratch_database
    owner, animal = uuid4(), uuid4()
    await asyncio.to_thread(command.upgrade, config, "0006")
    engine = create_async_engine(url)
    async with engine.begin() as conn:
        await conn.execute(
            INSERT_USER, {"id": owner, "name": "Ana", "email": "ana@example.com"}
        )
        await conn.execute(
            text(
                "INSERT INTO patas.animals "
                "(id, owner_id, name, species, adoption_status) "
                "VALUES (:id, :owner_id, 'Rex', 'dog', 'in_trial')"
            ),
            {"id": animal, "owner_id": owner},
        )
    await asyncio.to_thread(command.upgrade, config, "head")
    async with engine.connect() as conn:
        status = await conn.scalar(
            text("SELECT adoption_status::text FROM patas.animals WHERE id = :id"),
            {"id": animal},
        )
        labels = (await conn.execute(_LABELS)).scalars().all()
    await engine.dispose()
    assert status == "reserved"
    assert labels == ["available", "reserved", "adopted", "unavailable"]


async def test_downgrade_restores_in_trial_and_drops_the_table(
    scratch_database: tuple[Config, str],
) -> None:
    config, url = scratch_database
    await asyncio.to_thread(command.upgrade, config, "head")
    engine = create_async_engine(url)
    async with engine.connect() as conn:
        # Without this, a missing 0007 would make the downgrade a silent no-op.
        at_head = await conn.scalar(
            text("SELECT to_regclass('patas.adoption_applications')")
        )
    assert at_head is not None
    await asyncio.to_thread(command.downgrade, config, "0006")
    async with engine.connect() as conn:
        labels = (await conn.execute(_LABELS)).scalars().all()
        table = await conn.scalar(
            text("SELECT to_regclass('patas.adoption_applications')")
        )
        kind = await conn.scalar(text("SELECT to_regtype('patas.application_status')"))
    await engine.dispose()
    assert labels == ["available", "reserved", "in_trial", "adopted", "unavailable"]
    assert table is None
    assert kind is None
