from uuid import UUID

import httpx
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker
from token_issuer import TokenIssuer

from patas_backend.models.animal import (
    Animal,
    AnimalCompatibility,
    AnimalRepository,
    AnimalSize,
    FirstTimeOwnerSuitability,
    Species,
)
from patas_backend.models.compatibility import rules
from patas_backend.models.matching import EnergyLevel
from patas_backend.models.user import User, UserRepository

CARLA = {"sub": "5d0c7a52-3b1e-4c8f-9a6d-2e4f8b1c7d90",
         "email": "carla@example.com", "name": "Carla"}  # fmt: skip
BRUNO = {"sub": "8e1f3b6a-2c4d-4e5f-8a7b-1c2d3e4f5a6b",
         "email": "bruno@example.com", "name": "Bruno"}  # fmt: skip
ANA = User.provision(
    id=UUID("c3a1f0d2-7b64-4e19-9d85-0a2b3c4d5e6f"),
    name="Ana",
    email="ana@example.com",
)

# The worked example: an apartment, away half a day, some experience, no household.
HOME = {
    "housing": "apartment",
    "activity": "moderate",
    "time_away": "half_day",
    "experience": "some",
    "has_children": False,
    "has_dogs": False,
    "has_cats": False,
}
# Moderate energy, a few hours alone, fine for a first-timer, needs medium space.
MILO = {
    "activity_level": EnergyLevel.MODERATE,
    "tolerance_for_time_alone": EnergyLevel.LOW,
    "suitable_for_first_time_owners": FirstTimeOwnerSuitability.YES,
    "space_requirement": AnimalSize.MEDIUM,
}
UNKNOWN_ANIMAL = "00000000-0000-4000-8000-000000000000"


def _as(issuer: TokenIssuer, person: dict[str, str]) -> dict[str, str]:
    return {"Authorization": f"Bearer {issuer.token(**person)}"}


async def _publish(engine: AsyncEngine, owner: User = ANA, **fields: object) -> Animal:
    animal = Animal.publish(
        owner_id=owner.id,
        name="Milo",
        species=Species.DOG,
        age_in_months=36,
        **fields,  # type: ignore[arg-type]
    )
    async with async_sessionmaker(engine).begin() as session:
        await UserRepository(session).ensure_exists(owner)
        await AnimalRepository(session).add(animal)
    return animal


async def _save_home(
    client: httpx.AsyncClient,
    issuer: TokenIssuer,
    person: dict[str, str],
    **changes: object,
) -> None:
    saved = await client.put(
        "/me/matchmaker-profile",
        json={**HOME, **changes},
        headers=_as(issuer, person),
    )
    assert saved.status_code == 200


def _url(animal: Animal, mode: str | None = None) -> str:
    base = f"/animals/{animal.id}/compatibility"
    return base if mode is None else f"{base}?mode={mode}"


async def test_at_10_the_animal_page_gets_a_score_and_reasons_by_kind(
    client: httpx.AsyncClient, issuer: TokenIssuer, engine: AsyncEngine
) -> None:
    animal = await _publish(engine, **MILO)
    await _save_home(client, issuer, CARLA)

    response = await client.get(_url(animal), headers=_as(issuer, CARLA))

    # Fits 1.0, 0.5, 1.0, 0.5: a base of 0.75, so 75 in the flexible match.
    assert response.status_code == 200
    assert response.json() == {
        "mode": "loose",
        "score": 75,
        "is_compatible": True,
        "reasons": [
            {"text": rules.ACTIVITY_WORDING.fits, "kind": "strength"},
            {"text": rules.TIME_ALONE_WORDING.partly, "kind": "concern"},
            {"text": rules.EXPERIENCE_WORDING.fits, "kind": "strength"},
            {"text": rules.SPACE_WORDING.partly, "kind": "concern"},
        ],
    }


async def test_at_10_an_animal_not_safe_with_her_children_is_marked_not_suitable(
    client: httpx.AsyncClient, issuer: TokenIssuer, engine: AsyncEngine
) -> None:
    animal = await _publish(
        engine, behaves_well_with_children=AnimalCompatibility.NO, **MILO
    )
    await _save_home(client, issuer, CARLA, has_children=True)

    response = await client.get(_url(animal), headers=_as(issuer, CARLA))

    assert response.status_code == 200
    assert response.json()["is_compatible"] is False
    assert response.json()["score"] == 0
    assert response.json()["reasons"] == [
        {"text": rules.household_wording("children").misfit, "kind": "concern"}
    ]


async def test_at_10_updating_the_profile_changes_the_score(
    client: httpx.AsyncClient, issuer: TokenIssuer, engine: AsyncEngine
) -> None:
    animal = await _publish(engine, **MILO)
    await _save_home(client, issuer, CARLA)
    before = await client.get(_url(animal), headers=_as(issuer, CARLA))

    # Away only a few hours now: time alone fits in full, so 3.5 / 4 = 87.5.
    await _save_home(client, issuer, CARLA, time_away="few_hours")
    after = await client.get(_url(animal), headers=_as(issuer, CARLA))

    assert before.json()["score"] == 75
    assert after.json()["score"] == 88


async def test_at_10_her_own_animal_is_refused(
    client: httpx.AsyncClient, issuer: TokenIssuer, engine: AsyncEngine
) -> None:
    carla = User.provision(
        id=UUID(CARLA["sub"]), name=CARLA["name"], email=CARLA["email"]
    )
    animal = await _publish(engine, owner=carla, **MILO)
    await _save_home(client, issuer, CARLA)

    response = await client.get(_url(animal), headers=_as(issuer, CARLA))

    assert response.status_code == 422
    assert response.json() == {"detail": "This is your own animal"}


async def test_at_10_without_a_profile_the_caller_is_asked_to_create_one(
    client: httpx.AsyncClient, issuer: TokenIssuer, engine: AsyncEngine
) -> None:
    animal = await _publish(engine, **MILO)

    response = await client.get(_url(animal), headers=_as(issuer, CARLA))

    assert response.status_code == 409
    assert response.json() == {"detail": "No Matchmaker profile yet"}


async def test_at_10_a_visitor_without_a_token_gets_401(
    client: httpx.AsyncClient, engine: AsyncEngine
) -> None:
    animal = await _publish(engine, **MILO)

    response = await client.get(_url(animal))

    assert response.status_code == 401


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


async def test_at_11_the_strict_match_recalculates_the_score(
    client: httpx.AsyncClient, issuer: TokenIssuer, engine: AsyncEngine
) -> None:
    animal = await _publish(engine, **MILO)
    await _save_home(client, issuer, CARLA)

    response = await client.get(_url(animal, "strict"), headers=_as(issuer, CARLA))

    # The same 0.75 base, scaled by the weakest link (0.5): 37.5, rounded up.
    assert response.status_code == 200
    assert response.json()["mode"] == "strict"
    assert response.json()["score"] == 38
    assert response.json()["is_compatible"] is True


async def test_at_11_a_clear_shortfall_is_not_suitable_in_strict_only(
    client: httpx.AsyncClient, issuer: TokenIssuer, engine: AsyncEngine
) -> None:
    animal = await _publish(engine, **MILO)
    # Away most of the day, for an animal that tolerates a few hours alone.
    await _save_home(client, issuer, CARLA, time_away="most_of_day")

    strict = await client.get(_url(animal, "strict"), headers=_as(issuer, CARLA))
    loose = await client.get(_url(animal, "loose"), headers=_as(issuer, CARLA))

    assert strict.json()["is_compatible"] is False
    assert strict.json()["score"] == 0
    assert strict.json()["reasons"] == [
        {"text": rules.TIME_ALONE_WORDING.misfit, "kind": "concern"}
    ]
    assert loose.json()["is_compatible"] is True
    assert rules.TIME_ALONE_WORDING.misfit in [
        reason["text"] for reason in loose.json()["reasons"]
    ]


async def test_at_11_the_mode_defaults_to_loose_and_rejects_unknown_values(
    client: httpx.AsyncClient, issuer: TokenIssuer, engine: AsyncEngine
) -> None:
    animal = await _publish(engine, **MILO)
    await _save_home(client, issuer, CARLA)
    headers = _as(issuer, CARLA)

    default = await client.get(_url(animal), headers=headers)
    explicit = await client.get(_url(animal, "loose"), headers=headers)
    unknown = await client.get(_url(animal, "gentle"), headers=headers)

    assert default.json() == explicit.json()
    assert unknown.status_code == 422


async def test_at_11_one_users_mode_does_not_change_what_another_sees(
    client: httpx.AsyncClient, issuer: TokenIssuer, engine: AsyncEngine
) -> None:
    animal = await _publish(engine, **MILO)
    await _save_home(client, issuer, CARLA)
    await _save_home(client, issuer, BRUNO)

    carla = await client.get(_url(animal, "strict"), headers=_as(issuer, CARLA))
    bruno = await client.get(_url(animal), headers=_as(issuer, BRUNO))

    assert carla.json()["mode"] == "strict"
    assert bruno.json()["mode"] == "loose"
    assert bruno.json()["score"] == 75
