from uuid import UUID

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.ext.asyncio import AsyncEngine

from patas_backend.models.matching import EnergyLevel, ExperienceLevel
from patas_backend.models.matchmaker_profile import HousingType, TimeAway

USER_ID = UUID("5d0c7a52-3b1e-4c8f-9a6d-2e4f8b1c7d90")

ANSWERS = (
    "housing", "activity", "time_away", "experience",
    "has_children", "has_dogs", "has_cats",
)  # fmt: skip

INSERT_USER = text(
    "INSERT INTO patas.users (id, name, email) "
    "VALUES (:id, 'Carla', 'carla@example.com')"
)
INSERT_PROFILE = text(
    "INSERT INTO patas.matchmaker_profiles "
    "(user_id, housing, activity, time_away, experience, "
    "has_children, has_dogs, has_cats) "
    "VALUES (:user_id, CAST(:housing AS patas.housing_type), "
    "CAST(:activity AS patas.energy_level), CAST(:time_away AS patas.time_away), "
    "CAST(:experience AS patas.experience_level), "
    ":has_children, :has_dogs, :has_cats)"
)


@pytest_asyncio.fixture
async def user_id(engine: AsyncEngine) -> UUID:
    async with engine.begin() as conn:
        await conn.execute(INSERT_USER, {"id": USER_ID})
    return USER_ID


async def _insert_profile(engine: AsyncEngine, **overrides: object) -> None:
    params = {
        "user_id": USER_ID,
        "housing": "apartment",
        "activity": "low",
        "time_away": "few_hours",
        "experience": "some",
        "has_children": False,
        "has_dogs": False,
        "has_cats": True,
        **overrides,
    }
    async with engine.begin() as conn:
        await conn.execute(INSERT_PROFILE, params)


async def test_stores_a_complete_profile(engine: AsyncEngine, user_id: UUID) -> None:
    await _insert_profile(engine)
    async with engine.connect() as conn:
        row = (
            await conn.execute(text("SELECT * FROM patas.matchmaker_profiles"))
        ).one()
    assert (row.housing, row.activity, row.experience) == ("apartment", "low", "some")
    assert row.has_cats is True


@pytest.mark.parametrize(
    ("column", "value"),
    [
        ("housing", "castle"),
        ("activity", "extreme"),
        ("time_away", "forever"),
        ("experience", "expert"),
    ],
)
async def test_rejects_a_value_outside_the_scale(
    engine: AsyncEngine, user_id: UUID, column: str, value: str
) -> None:
    # asyncpg's enum error reaches us as the generic DBAPIError, so match the reason.
    with pytest.raises(DBAPIError, match="invalid input value for enum"):
        await _insert_profile(engine, **{column: value})


@pytest.mark.parametrize("column", ANSWERS)
async def test_rejects_a_missing_answer(
    engine: AsyncEngine, user_id: UUID, column: str
) -> None:
    with pytest.raises(IntegrityError):
        await _insert_profile(engine, **{column: None})


async def test_rejects_an_unknown_user(engine: AsyncEngine) -> None:
    with pytest.raises(IntegrityError):
        await _insert_profile(engine)


async def test_a_user_has_only_one_profile(engine: AsyncEngine, user_id: UUID) -> None:
    await _insert_profile(engine)
    with pytest.raises(IntegrityError):
        await _insert_profile(engine, housing="house_with_yard")


async def test_deleting_the_user_deletes_the_profile(
    engine: AsyncEngine, user_id: UUID
) -> None:
    await _insert_profile(engine)
    async with engine.begin() as conn:
        await conn.execute(
            text("DELETE FROM patas.users WHERE id = :id"), {"id": user_id}
        )
    async with engine.connect() as conn:
        remaining = await conn.scalar(
            text("SELECT count(*) FROM patas.matchmaker_profiles")
        )
    assert remaining == 0


async def test_updated_at_changes_on_update(engine: AsyncEngine, user_id: UUID) -> None:
    await _insert_profile(engine)
    async with engine.connect() as conn:
        before = await conn.scalar(
            text("SELECT updated_at FROM patas.matchmaker_profiles")
        )
    async with engine.begin() as conn:
        await conn.execute(text("UPDATE patas.matchmaker_profiles SET has_dogs = true"))
    async with engine.connect() as conn:
        after = await conn.scalar(
            text("SELECT updated_at FROM patas.matchmaker_profiles")
        )
    assert after > before


@pytest.mark.parametrize(
    ("database_type", "scale"),
    [
        ("housing_type", HousingType),
        ("energy_level", EnergyLevel),
        ("time_away", TimeAway),
        ("experience_level", ExperienceLevel),
    ],
)
async def test_database_enums_match_the_domain_scales(
    engine: AsyncEngine, database_type: str, scale: type
) -> None:
    # A value added on one side only would break at runtime on the repository's CAST.
    async with engine.connect() as conn:
        values = await conn.scalar(
            text(f"SELECT enum_range(NULL::patas.{database_type})::text[]")
        )
    assert values == [member.value for member in scale]
