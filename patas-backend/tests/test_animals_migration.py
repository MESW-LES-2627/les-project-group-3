from uuid import UUID, uuid4

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.ext.asyncio import AsyncEngine

OWNER_ID = UUID("0b1f2a3c-4d5e-4f60-8a7b-9c0d1e2f3a4b")

INSERT_USER = text(
    "INSERT INTO patas.users (id, name, email) VALUES (:id, 'Ana', 'ana@example.com')"
)
INSERT_ANIMAL = text(
    "INSERT INTO patas.animals (id, owner_id, name, species, age_in_months) "
    "VALUES (:id, :owner_id, :name, CAST(:species AS patas.species), :age)"
)


@pytest_asyncio.fixture
async def owner_id(engine: AsyncEngine) -> UUID:
    async with engine.begin() as conn:
        await conn.execute(INSERT_USER, {"id": OWNER_ID})
    return OWNER_ID


async def _insert_animal(engine: AsyncEngine, **overrides: object) -> None:
    params = {
        "id": uuid4(),
        "owner_id": OWNER_ID,
        "name": "Rex",
        "species": "dog",
        "age": 12,
        **overrides,
    }
    async with engine.begin() as conn:
        await conn.execute(INSERT_ANIMAL, params)


async def test_rejects_blank_name(engine: AsyncEngine, owner_id: UUID) -> None:
    with pytest.raises(IntegrityError):
        await _insert_animal(engine, name="   ")


async def test_rejects_negative_age(engine: AsyncEngine, owner_id: UUID) -> None:
    with pytest.raises(IntegrityError):
        await _insert_animal(engine, age=-1)


async def test_age_is_optional(engine: AsyncEngine, owner_id: UUID) -> None:
    await _insert_animal(engine, age=None)


async def test_rejects_unknown_owner(engine: AsyncEngine) -> None:
    with pytest.raises(IntegrityError):
        await _insert_animal(engine, owner_id=uuid4())


async def test_rejects_unknown_species(engine: AsyncEngine, owner_id: UUID) -> None:
    # asyncpg's enum error reaches us as the generic DBAPIError, so match the reason.
    with pytest.raises(DBAPIError, match="invalid input value for enum"):
        await _insert_animal(engine, species="dragon")


async def test_owner_with_animals_cannot_be_deleted(
    engine: AsyncEngine, owner_id: UUID
) -> None:
    await _insert_animal(engine)
    with pytest.raises(IntegrityError):
        async with engine.begin() as conn:
            await conn.execute(
                text("DELETE FROM patas.users WHERE id = :id"), {"id": owner_id}
            )


async def test_adoption_status_defaults_to_available(
    engine: AsyncEngine, owner_id: UUID
) -> None:
    await _insert_animal(engine)
    async with engine.connect() as conn:
        status = await conn.scalar(text("SELECT adoption_status FROM patas.animals"))
    assert status == "available"


async def test_updated_at_changes_on_update(
    engine: AsyncEngine, owner_id: UUID
) -> None:
    await _insert_animal(engine)
    async with engine.begin() as conn:
        await conn.execute(text("UPDATE patas.animals SET name = 'Rex II'"))
    async with engine.connect() as conn:
        row = (
            await conn.execute(text("SELECT created_at, updated_at FROM patas.animals"))
        ).one()
    assert row.updated_at > row.created_at


async def test_animal_profile_columns_are_nullable(engine: AsyncEngine) -> None:
    async with engine.connect() as conn:
        rows = (
            await conn.execute(
                text(
                    """
                        SELECT column_name, is_nullable
                        FROM information_schema.columns
                        WHERE table_schema = 'patas' AND table_name = 'animals'
                          AND column_name IN (
                            'sex', 'is_neutered', 'postal_code', 'size',
                            'activity_level', 'space_requirement', 'shedding',
                            'grooming_needs',
                            'behaves_well_with_children', 'behaves_well_with_dogs',
                            'behaves_well_with_cats', 'behaves_well_with_other_animals',
                            'training_needs', 'tolerance_for_time_alone', 'noise_level',
                            'suitable_for_first_time_owners', 'special_care_notes',
                            'other_details'
                          )
                        """
                )
            )
        ).all()

    assert len(rows) == 18
    assert all(row.is_nullable == "YES" for row in rows)
