import asyncio
from uuid import UUID

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from patas_backend.models.matching import EnergyLevel, ExperienceLevel
from patas_backend.models.matchmaker_profile import (
    HousingType,
    MatchmakerProfile,
    MatchmakerProfileRepository,
    TimeAway,
)
from patas_backend.models.user import User, UserRepository

CARLA_ID = UUID("5d0c7a52-3b1e-4c8f-9a6d-2e4f8b1c7d90")
BRUNO_ID = UUID("8e1f3b6a-2c4d-4e5f-8a7b-1c2d3e4f5a6b")

Factory = async_sessionmaker[AsyncSession]


async def _provision(factory: Factory, user_id: UUID, email: str) -> UUID:
    async with factory.begin() as session:
        await UserRepository(session).ensure_exists(
            User.provision(id=user_id, name="Adopter", email=email)
        )
    return user_id


@pytest_asyncio.fixture
async def carla(session_factory: Factory) -> UUID:
    return await _provision(session_factory, CARLA_ID, "carla@example.com")


def _profile(user_id: UUID, **overrides: object) -> MatchmakerProfile:
    # Carla's answers from AT-07.
    return MatchmakerProfile(
        **{
            "user_id": user_id,
            "housing": HousingType.APARTMENT,
            "activity": EnergyLevel.LOW,
            "time_away": TimeAway.FEW_HOURS,
            "experience": ExperienceLevel.SOME,
            "has_children": False,
            "has_dogs": False,
            "has_cats": True,
            **overrides,
        }
    )


async def _save(factory: Factory, profile: MatchmakerProfile) -> None:
    async with factory.begin() as session:
        await MatchmakerProfileRepository(session).save(profile)


async def _get(factory: Factory, user_id: UUID) -> MatchmakerProfile | None:
    async with factory() as session:
        return await MatchmakerProfileRepository(session).get(user_id)


async def _count(factory: Factory) -> int:
    async with factory() as session:
        return await session.scalar(
            text("SELECT count(*) FROM patas.matchmaker_profiles")
        )


async def _updated_at(factory: Factory) -> object:
    async with factory() as session:
        return await session.scalar(
            text("SELECT updated_at FROM patas.matchmaker_profiles")
        )


async def test_a_user_without_a_profile_has_none(
    session_factory: Factory, carla: UUID
) -> None:
    assert await _get(session_factory, carla) is None


@pytest.mark.parametrize(
    "household",
    [
        {"has_children": True, "has_dogs": False, "has_cats": False},
        {"has_children": False, "has_dogs": True, "has_cats": False},
        {"has_children": False, "has_dogs": False, "has_cats": True},
    ],
)
async def test_every_answer_is_stored_and_loaded_back(
    session_factory: Factory, carla: UUID, household: dict[str, bool]
) -> None:
    # Different from the defaults and one household flag at a time, so a swapped
    # column in the SQL or in the row mapping changes the result.
    profile = _profile(
        carla,
        housing=HousingType.HOUSE_WITH_YARD,
        activity=EnergyLevel.HIGH,
        time_away=TimeAway.MOST_OF_DAY,
        experience=ExperienceLevel.EXPERIENCED,
        **household,
    )

    await _save(session_factory, profile)

    assert await _get(session_factory, carla) == profile


async def test_saving_again_replaces_the_answers_and_keeps_one_profile(
    session_factory: Factory, carla: UUID
) -> None:
    await _save(session_factory, _profile(carla))
    changed = _profile(carla, has_dogs=True)

    await _save(session_factory, changed)

    assert await _get(session_factory, carla) == changed
    assert await _count(session_factory) == 1


async def test_saving_again_refreshes_updated_at(
    session_factory: Factory, carla: UUID
) -> None:
    await _save(session_factory, _profile(carla))
    before = await _updated_at(session_factory)

    await _save(session_factory, _profile(carla, has_dogs=True))

    assert await _updated_at(session_factory) > before


async def test_two_saves_at_once_leave_one_profile(
    session_factory: Factory, carla: UUID
) -> None:
    # A "look, then insert" would let both see nothing and the second would fail.
    await asyncio.gather(
        _save(session_factory, _profile(carla)),
        _save(session_factory, _profile(carla, has_dogs=True)),
    )

    assert await _count(session_factory) == 1


async def test_each_user_gets_only_their_own_profile(
    session_factory: Factory, carla: UUID
) -> None:
    bruno = await _provision(session_factory, BRUNO_ID, "bruno@example.com")
    carlas = _profile(carla)
    brunos = _profile(bruno, housing=HousingType.HOUSE_NO_YARD, has_children=True)
    await _save(session_factory, carlas)
    await _save(session_factory, brunos)

    assert await _get(session_factory, carla) == carlas
    assert await _get(session_factory, bruno) == brunos


async def test_save_never_commits_so_the_caller_can_roll_back(
    session_factory: Factory, carla: UUID
) -> None:
    async with session_factory() as session:
        await MatchmakerProfileRepository(session).save(_profile(carla))
        await session.rollback()

    assert await _get(session_factory, carla) is None
