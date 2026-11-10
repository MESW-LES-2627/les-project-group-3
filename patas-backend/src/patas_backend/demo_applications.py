"""Demo adoption requests, one per status, on top of the animals `pnpm seed:demo`
publishes.

Each row is built directly in its final status, so this bypasses the transitions on
purpose: every adoption story starts from a known state, and some states (closed,
withdrawn) cannot be reached through the application until later stories land.
Running it again is safe: a row is identified by its animal, applicant and status.
"""

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import NAMESPACE_URL, UUID, uuid5

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from patas_backend.models.adoption import (
    AdoptionApplication,
    AdoptionApplicationRepository,
    ApplicationStatus,
    ProfileSnapshot,
)
from patas_backend.models.animal import Animal, AnimalRepository
from patas_backend.models.matching import EnergyLevel, ExperienceLevel, TimeAway
from patas_backend.models.matchmaker_profile import (
    HousingType,
    MatchmakerProfile,
    MatchmakerProfileRepository,
)

S = ApplicationStatus
_NAMESPACE = uuid5(NAMESPACE_URL, "patas:demo-applications")
_FIX = "run `pnpm seed:demo` (in patas-frontend) first"


class DemoDataMissing(Exception):
    """The demo users and animals this script builds on are not there."""


@dataclass(frozen=True)
class _Request:
    animal: str
    owner: str
    applicant: str
    status: ApplicationStatus
    note: str
    owner_note: str | None = None


_REQUESTS = (
    _Request(
        "Luna", "Ana Demo", "Bruno Demo", S.OPEN,
        "I work from home and have a calm flat, with a park next door.",
    ),
    _Request(
        "Luna", "Ana Demo", "Carla Demo", S.OPEN,
        "We have a garden and two children who love dogs.",
    ),
    _Request(
        "Milo", "Ana Demo", "Bruno Demo", S.ACCEPTED,
        "I have had cats before and I am home most evenings.",
        "Welcome! Let's arrange a visit this weekend.",
    ),
    _Request(
        "Bobby", "Carla Demo", "Bruno Demo", S.DECLINED,
        "I would love to give Bobby a home.",
        "Thank you, but Bobby needs a garden and a lot of space.",
    ),
    _Request(
        "Nina", "Bruno Demo", "Carla Demo", S.WITHDRAWN,
        "Nina looks like a perfect companion for us.",
    ),
    _Request(
        "Pipoca", "Bruno Demo", "Ana Demo", S.CLOSED,
        "I would like to adopt Pipoca.",
    ),
    _Request(
        "Cenoura", "Carla Demo", "Ana Demo", S.ADOPTED,
        "Cenoura would fit well in our home.",
        "She is all yours. Enjoy!",
    ),
)  # fmt: skip

# What each demo user answered, so the owners see different profiles.
_PROFILES = {
    "Ana Demo": dict(
        housing=HousingType.HOUSE_NO_YARD,
        activity=EnergyLevel.MODERATE,
        time_away=TimeAway.HALF_DAY,
        experience=ExperienceLevel.SOME,
        has_children=False,
        has_dogs=True,
        has_cats=True,
    ),
    "Bruno Demo": dict(
        housing=HousingType.APARTMENT,
        activity=EnergyLevel.LOW,
        time_away=TimeAway.FEW_HOURS,
        experience=ExperienceLevel.NONE,
        has_children=False,
        has_dogs=False,
        has_cats=True,
    ),
    "Carla Demo": dict(
        housing=HousingType.HOUSE_WITH_YARD,
        activity=EnergyLevel.HIGH,
        time_away=TimeAway.FEW_HOURS,
        experience=ExperienceLevel.EXPERIENCED,
        has_children=True,
        has_dogs=True,
        has_cats=False,
    ),
}


async def seed_applications(session_factory: async_sessionmaker[AsyncSession]) -> int:
    """Add the demo requests that are not there yet. Returns how many were added.

    All or nothing: if the demo data is missing, nothing is written.
    """
    async with session_factory.begin() as session:
        animals = {
            (animal.owner_name, animal.name): animal
            for animal in await AnimalRepository(session).list_all()
        }
        people = {animal.owner_name: animal.owner_id for animal in animals.values()}
        resolved = [
            (request, _find_animal(animals, request), _find_person(people, request))
            for request in _REQUESTS
        ]
        profiles = await _ensure_profiles(session, people)
        applications = AdoptionApplicationRepository(session)

        created = 0
        for request, animal, applicant_id in resolved:
            application_id = uuid5(
                _NAMESPACE, f"{animal.id}:{applicant_id}:{request.status.value}"
            )
            if await applications.get_by_id(application_id) is not None:
                continue
            await applications.add(
                _build(application_id, request, animal, applicant_id, profiles)
            )
            await _settle_animal(session, animal.id, request.status)
            created += 1
        return created


def _find_animal(animals: dict[tuple[str, str], Animal], request: _Request) -> Animal:
    animal = animals.get((request.owner, request.animal))
    if animal is None:
        raise DemoDataMissing(f"{request.owner}'s {request.animal} is missing: {_FIX}")
    return animal


def _find_person(people: dict[str, UUID], request: _Request) -> UUID:
    person = people.get(request.applicant)
    if person is None:
        raise DemoDataMissing(f"{request.applicant} is missing: {_FIX}")
    return person


async def _ensure_profiles(
    session: AsyncSession, people: dict[str, UUID]
) -> dict[UUID, MatchmakerProfile]:
    """The demo users' Matchmaker profiles; one a user already saved is kept."""
    repository = MatchmakerProfileRepository(session)
    profiles: dict[UUID, MatchmakerProfile] = {}
    for name, answers in _PROFILES.items():
        user_id = people[name]
        profile = await repository.get(user_id)
        if profile is None:
            profile = MatchmakerProfile(user_id=user_id, **answers)
            await repository.save(profile)
        profiles[user_id] = profile
    return profiles


def _build(
    application_id: UUID,
    request: _Request,
    animal: Animal,
    applicant_id: UUID,
    profiles: dict[UUID, MatchmakerProfile],
) -> AdoptionApplication:
    # An adopted request has both handover confirmations: the database requires it.
    confirmed = datetime.now(UTC) if request.status is S.ADOPTED else None
    return AdoptionApplication(
        id=application_id,
        animal_id=animal.id,
        owner_id=animal.owner_id,
        applicant_id=applicant_id,
        applicant_note=request.note,
        applicant_profile=ProfileSnapshot.of(profiles[applicant_id]),
        status=request.status,
        owner_note=request.owner_note,
        owner_confirmed_at=confirmed,
        applicant_confirmed_at=confirmed,
    )


async def _settle_animal(
    session: AsyncSession, animal_id: UUID, status: ApplicationStatus
) -> None:
    """An accepted request reserves its animal; an adopted one means it went home."""
    if status not in (S.ACCEPTED, S.ADOPTED):
        return
    repository = AnimalRepository(session)
    animal = await repository.get_for_update(animal_id)
    if animal is None:
        raise DemoDataMissing(f"an animal disappeared while seeding: {_FIX}")
    animal.reserve()
    if status is S.ADOPTED:
        animal.mark_adopted()
    await repository.update(animal)
