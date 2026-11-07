from uuid import UUID, uuid4

import pytest
from adoption_factory import Factory
from sqlalchemy import text

from patas_backend.demo_applications import DemoDataMissing, seed_applications
from patas_backend.models.adoption import ApplicationStatus, ProfileSnapshot
from patas_backend.models.animal import Animal, AnimalRepository, Species
from patas_backend.models.matching import EnergyLevel, ExperienceLevel, TimeAway
from patas_backend.models.matchmaker_profile import (
    HousingType,
    MatchmakerProfile,
    MatchmakerProfileRepository,
)
from patas_backend.models.user import User, UserRepository

# The demo users and animals that `pnpm seed:demo` publishes.
DEMO_ANIMALS = {
    "Ana Demo": ("Luna", "Milo"),
    "Bruno Demo": ("Pipoca", "Nina"),
    "Carla Demo": ("Bobby", "Cenoura"),
}
EXPECTED = {
    ("Luna", "Bruno Demo", "open"),
    ("Luna", "Carla Demo", "open"),
    ("Milo", "Bruno Demo", "accepted"),
    ("Bobby", "Bruno Demo", "declined"),
    ("Nina", "Carla Demo", "withdrawn"),
    ("Pipoca", "Ana Demo", "closed"),
    ("Cenoura", "Ana Demo", "adopted"),
}


async def _publish_demo_animals(
    factory: Factory, owners: dict[str, tuple[str, ...]] = DEMO_ANIMALS
) -> dict[str, UUID]:
    ids: dict[str, UUID] = {}
    async with factory.begin() as session:
        for name, animals in owners.items():
            user_id = uuid4()
            email = f"{name.split()[0].lower()}.demo@example.com"
            await UserRepository(session).ensure_exists(
                User.provision(id=user_id, name=name, email=email)
            )
            for animal_name in animals:
                await AnimalRepository(session).add(
                    Animal.publish(
                        owner_id=user_id, name=animal_name, species=Species.DOG
                    )
                )
            ids[name] = user_id
    return ids


async def _rows(factory: Factory) -> list[dict]:
    async with factory() as session:
        result = await session.execute(
            text(
                """
                SELECT a.name AS animal, u.name AS applicant,
                       ap.status::text AS status, ap.owner_note,
                       ap.owner_confirmed_at IS NOT NULL AS owner_confirmed,
                       ap.applicant_confirmed_at IS NOT NULL AS applicant_confirmed,
                       ap.applicant_id, ap.applicant_profile
                FROM patas.adoption_applications ap
                JOIN patas.animals a ON a.id = ap.animal_id
                JOIN patas.users u ON u.id = ap.applicant_id
                ORDER BY a.name, u.name
                """
            )
        )
        return [dict(row._mapping) for row in result]


async def _animal_statuses(factory: Factory) -> dict[str, str]:
    async with factory() as session:
        result = await session.execute(
            text("SELECT name, adoption_status::text FROM patas.animals")
        )
        return {name: status for name, status in result}


async def test_the_demo_applications_are_the_pinned_ones(
    session_factory: Factory,
) -> None:
    await _publish_demo_animals(session_factory)

    created = await seed_applications(session_factory)

    rows = await _rows(session_factory)
    assert created == 7
    assert {(r["animal"], r["applicant"], r["status"]) for r in rows} == EXPECTED
    assert {r["status"] for r in rows} == {s.value for s in ApplicationStatus}


async def test_the_answered_and_adopted_requests_carry_their_notes_and_confirmations(
    session_factory: Factory,
) -> None:
    await _publish_demo_animals(session_factory)

    await seed_applications(session_factory)

    by_status = {r["status"]: r for r in await _rows(session_factory)}
    assert by_status["accepted"]["owner_note"]
    assert by_status["declined"]["owner_note"]
    assert by_status["adopted"]["owner_confirmed"]
    assert by_status["adopted"]["applicant_confirmed"]
    assert not by_status["open"]["owner_confirmed"]


async def test_animals_are_left_in_the_status_that_goes_with_their_request(
    session_factory: Factory,
) -> None:
    await _publish_demo_animals(session_factory)

    await seed_applications(session_factory)

    statuses = await _animal_statuses(session_factory)
    assert statuses["Milo"] == "reserved"
    assert statuses["Cenoura"] == "adopted"
    others = set(statuses) - {"Milo", "Cenoura"}
    assert {statuses[name] for name in others} == {"available"}


async def test_seeding_twice_adds_nothing_the_second_time(
    session_factory: Factory,
) -> None:
    await _publish_demo_animals(session_factory)
    await seed_applications(session_factory)

    assert await seed_applications(session_factory) == 0

    assert len(await _rows(session_factory)) == 7


async def test_an_existing_matchmaker_profile_is_kept_and_snapshots_follow_it(
    session_factory: Factory,
) -> None:
    ids = await _publish_demo_animals(session_factory)
    brunos = MatchmakerProfile(
        user_id=ids["Bruno Demo"],
        housing=HousingType.HOUSE_WITH_YARD,
        activity=EnergyLevel.HIGH,
        time_away=TimeAway.MOST_OF_DAY,
        experience=ExperienceLevel.EXPERIENCED,
        has_children=True,
        has_dogs=True,
        has_cats=True,
    )
    async with session_factory.begin() as session:
        await MatchmakerProfileRepository(session).save(brunos)

    await seed_applications(session_factory)

    async with session_factory() as session:
        repository = MatchmakerProfileRepository(session)
        profiles = {name: await repository.get(i) for name, i in ids.items()}
    assert profiles["Bruno Demo"] == brunos  # not overwritten
    assert profiles["Ana Demo"] is not None
    assert profiles["Carla Demo"] is not None
    for row in await _rows(session_factory):
        expected = ProfileSnapshot.of(profiles[row["applicant"]])
        assert ProfileSnapshot.from_json(row["applicant_profile"]) == expected


async def test_missing_demo_data_fails_and_names_the_way_to_fix_it(
    session_factory: Factory,
) -> None:
    with pytest.raises(DemoDataMissing, match="seed:demo"):
        await seed_applications(session_factory)


async def test_a_partial_demo_world_writes_nothing(
    session_factory: Factory,
) -> None:
    ids = await _publish_demo_animals(session_factory, {"Ana Demo": ("Luna", "Milo")})

    with pytest.raises(DemoDataMissing):
        await seed_applications(session_factory)

    assert await _rows(session_factory) == []
    async with session_factory() as session:
        saved = await MatchmakerProfileRepository(session).get(ids["Ana Demo"])
    assert saved is None
