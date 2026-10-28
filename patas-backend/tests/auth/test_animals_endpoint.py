from dataclasses import fields
from uuid import UUID, uuid4

import httpx
import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker
from token_issuer import USER_ID, TokenIssuer

from patas_backend.models.animal import (
    AdoptionStatus,
    Animal,
    AnimalMatchProfile,
    AnimalRepository,
    AnimalSex,
    AnimalSize,
    Species,
)
from patas_backend.models.user import User, UserRepository
from patas_backend.routers.animals import AnimalMatchProfileResponse


def _bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def _stored_animals(engine: AsyncEngine) -> int:
    async with engine.connect() as conn:
        return await conn.scalar(text("SELECT count(*) FROM patas.animals"))


async def test_catalog_is_public_and_lists_published_animals(
    client: httpx.AsyncClient, engine: AsyncEngine
) -> None:
    # AC5: a visitor without a token sees what was published.
    owner = User.provision(id=uuid4(), name="Ana", email="ana@example.com")
    animal = Animal.publish(
        owner_id=owner.id, name="Milo", species=Species.CAT, age_in_months=14
    )
    async with async_sessionmaker(engine).begin() as session:
        await UserRepository(session).ensure_exists(owner)
        await AnimalRepository(session).add(animal)

    response = await client.get("/animals")

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": str(animal.id),
            "owner_id": str(owner.id),
            "name": "Milo",
            "species": "cat",
            "age_in_months": 14,
            "adoption_status": "available",
            "sex": None,
            "is_neutered": None,
            "postal_code": None,
            "size": None,
            "activity_level": None,
            "space_requirement": None,
            "shedding": None,
            "grooming_needs": None,
            "behaves_well_with_children": None,
            "behaves_well_with_dogs": None,
            "behaves_well_with_cats": None,
            "behaves_well_with_other_animals": None,
            "training_needs": None,
            "tolerance_for_time_alone": None,
            "noise_level": None,
            "suitable_for_first_time_owners": None,
            "special_care_notes": None,
            "other_details": None,
            "match_profile": {
                "activity": None,
                "max_time_alone": None,
                "experience_needed": None,
                "space_needed": None,
                "safe_with_children": None,
                "safe_with_dogs": None,
                "safe_with_cats": None,
                "size": None,
            },
        }
    ]


async def test_published_animal_appears_in_the_catalog_owned_by_the_publisher(
    client: httpx.AsyncClient, issuer: TokenIssuer
) -> None:
    # AC1, the vertical slice: HTTP in, row stored, read back through the catalog.
    response = await client.post(
        "/animals",
        json={"name": "  Rex  ", "species": "dog", "age_in_months": 30},
        headers=_bearer(issuer.token()),
    )

    assert response.status_code == 201
    published = response.json()
    assert published["owner_id"] == USER_ID
    assert published["name"] == "Rex"
    assert published["adoption_status"] == "available"
    assert published["sex"] is None
    assert published["behaves_well_with_dogs"] is None
    catalog = (await client.get("/animals")).json()
    assert catalog == [published]


async def test_animal_profile_fields_are_saved_and_listed(
    client: httpx.AsyncClient, issuer: TokenIssuer
) -> None:
    response = await client.post(
        "/animals",
        json={
            "name": "Milo",
            "species": "cat",
            "sex": "male",
            "is_neutered": "yes",
            "postal_code": "1234-567",
            "size": "small",
            "activity_level": "moderate",
            "space_requirement": "small",
            "shedding": "low",
            "grooming_needs": "high",
            "behaves_well_with_children": "with_supervision",
            "behaves_well_with_dogs": "unknown",
            "behaves_well_with_cats": "yes",
            "behaves_well_with_other_animals": "no",
            "training_needs": "low",
            "tolerance_for_time_alone": "moderate",
            "noise_level": "low",
            "suitable_for_first_time_owners": "with_support",
            "special_care_notes": "Needs daily medication",
            "other_details": "Enjoys sunny spots",
        },
        headers=_bearer(issuer.token()),
    )

    assert response.status_code == 201
    published = response.json()
    assert published["sex"] == "male"
    assert published["is_neutered"] == "yes"
    assert published["behaves_well_with_children"] == "with_supervision"
    assert published["suitable_for_first_time_owners"] == "with_support"
    assert published["special_care_notes"] == "Needs daily medication"
    assert published["match_profile"] == {
        "activity": "moderate",
        "max_time_alone": "half_day",  # tolerance moderate
        "experience_needed": "some",  # with_support
        "space_needed": "small",
        "safe_with_children": None,  # with_supervision: not settled
        "safe_with_dogs": None,  # unknown
        "safe_with_cats": True,
        "size": "small",
    }
    assert (await client.get("/animals")).json() == [published]


async def test_animal_profile_fields_are_optional(
    client: httpx.AsyncClient, issuer: TokenIssuer
) -> None:
    response = await client.post(
        "/animals",
        json={"name": "Milo", "species": "cat"},
        headers=_bearer(issuer.token()),
    )

    assert response.status_code == 201
    published = response.json()
    # The derived view is an object, so its values are checked on their own.
    assert all(value is None for value in published.pop("match_profile").values())
    assert all(
        value is None
        for key, value in published.items()
        if key not in {"id", "owner_id", "name", "species", "adoption_status"}
    )


def test_the_match_profile_response_carries_every_domain_field() -> None:
    assert set(AnimalMatchProfileResponse.model_fields) == {
        f.name for f in fields(AnimalMatchProfile)
    }


async def test_publishing_without_a_token_is_rejected_and_nothing_is_stored(
    client: httpx.AsyncClient, engine: AsyncEngine
) -> None:
    # AC2
    response = await client.post("/animals", json={"name": "Rex", "species": "dog"})

    assert response.status_code == 401
    assert await _stored_animals(engine) == 0


@pytest.mark.parametrize(
    "body",
    [
        pytest.param({"name": "   ", "species": "dog"}, id="blank-name"),
        pytest.param(
            {"name": "Rex", "species": "dog", "age_in_months": -1}, id="negative-age"
        ),
        pytest.param({"name": "Rex", "species": "rabbit"}, id="unknown-species"),
        pytest.param(
            {"name": "Rex", "species": "dog", "postal_code": "12345"},
            id="invalid-postal-code",
        ),
        pytest.param(
            {"name": "Rex", "species": "dog", "activity_level": "extreme"},
            id="invalid-activity-level",
        ),
    ],
)
async def test_invalid_animal_is_rejected_and_nothing_is_stored(
    client: httpx.AsyncClient,
    issuer: TokenIssuer,
    engine: AsyncEngine,
    body: dict[str, object],
) -> None:
    # AC3
    response = await client.post("/animals", json=body, headers=_bearer(issuer.token()))

    assert response.status_code == 422
    assert await _stored_animals(engine) == 0


ANA = {
    "sub": "11111111-1111-1111-1111-111111111111",
    "name": "Ana",
    "email": "ana@example.com",
}
BRUNO = {
    "sub": "22222222-2222-2222-2222-222222222222",
    "name": "Bruno",
    "email": "bruno@example.com",
}


async def _seed_data(engine: AsyncEngine) -> tuple[Animal, Animal, Animal]:
    """Seed data: Rex (Ana), Mia (Ana), Bolt (Bruno)."""
    ana_user = User.provision(id=UUID(ANA["sub"]), name=ANA["name"], email=ANA["email"])
    bruno_user = User.provision(
        id=UUID(BRUNO["sub"]), name=BRUNO["name"], email=BRUNO["email"]
    )
    rex = Animal.publish(
        owner_id=ana_user.id,
        name="Rex",
        species=Species.DOG,
        size=AnimalSize.MEDIUM,
        sex=AnimalSex.MALE,
        age_in_months=36,
    )
    mia = Animal.publish(
        owner_id=ana_user.id,
        name="Mia",
        species=Species.CAT,
        size=AnimalSize.SMALL,
        sex=AnimalSex.FEMALE,
        age_in_months=6,
    )
    bolt = Animal.publish(
        owner_id=bruno_user.id,
        name="Bolt",
        species=Species.DOG,
        size=AnimalSize.LARGE,
        sex=AnimalSex.MALE,
        age_in_months=120,
    )
    async with async_sessionmaker(engine).begin() as session:
        user_repo = UserRepository(session)
        await user_repo.ensure_exists(ana_user)
        await user_repo.ensure_exists(bruno_user)
        animal_repo = AnimalRepository(session)
        await animal_repo.add(rex)
        await animal_repo.add(mia)
        await animal_repo.add(bolt)
    return rex, mia, bolt


async def test_acceptance_test_ana_sees_rex_and_mia_but_not_bolt(
    client: httpx.AsyncClient, issuer: TokenIssuer, engine: AsyncEngine
) -> None:
    # Given the seed data, Ana's "My animals" shows Rex and Mia but not Bolt.
    await _seed_data(engine)

    response = await client.get(
        "/me/animals",
        headers=_bearer(issuer.token(**ANA)),
    )

    assert response.status_code == 200
    names = [animal["name"] for animal in response.json()]
    assert "Rex" in names
    assert "Mia" in names
    assert "Bolt" not in names


async def test_acceptance_test_bruno_cannot_unpublish_rex(
    client: httpx.AsyncClient, issuer: TokenIssuer, engine: AsyncEngine
) -> None:
    # When Bruno tries to unpublish Rex, then it is refused and Rex is unchanged.
    rex, _, _ = await _seed_data(engine)

    response = await client.post(
        f"/animals/{rex.id}/unpublish",
        headers=_bearer(issuer.token(**BRUNO)),
    )

    assert response.status_code == 403

    # Rex is unchanged
    async with async_sessionmaker(engine)() as session:
        loaded = await AnimalRepository(session).get_by_id(rex.id)
        assert loaded is not None
        assert loaded.adoption_status is AdoptionStatus.AVAILABLE


async def test_acceptance_test_visitor_cannot_unpublish_rex_or_view_my_animals(
    client: httpx.AsyncClient, engine: AsyncEngine
) -> None:
    # When a visitor who is not logged in tries unpublish or my animals, it is refused.
    rex, _, _ = await _seed_data(engine)

    unpublish_response = await client.post(f"/animals/{rex.id}/unpublish")
    assert unpublish_response.status_code == 401

    my_animals_response = await client.get("/me/animals")
    assert my_animals_response.status_code == 401


async def test_acceptance_test_unpublish_flow_catalog_and_detail(
    client: httpx.AsyncClient, issuer: TokenIssuer, engine: AsyncEngine
) -> None:
    # Seed data: Rex (Ana), Mia (Ana), Bolt (Bruno)
    rex, _, _ = await _seed_data(engine)

    # Given Rex appears in the catalog filtered by "dog"
    catalog_dog = await client.get("/animals?species=dog")
    assert catalog_dog.status_code == 200
    dog_names = [a["name"] for a in catalog_dog.json()]
    assert "Rex" in dog_names

    # When Ana unpublishes him
    unpublish_res = await client.post(
        f"/animals/{rex.id}/unpublish",
        headers=_bearer(issuer.token(**ANA)),
    )
    assert unpublish_res.status_code == 200
    assert unpublish_res.json()["adoption_status"] == "unavailable"

    # Then Rex is in neither the catalog nor the "dog" results.
    general_catalog = (await client.get("/animals")).json()
    assert all(a["id"] != str(rex.id) for a in general_catalog)

    filtered_catalog = (await client.get("/animals?species=dog")).json()
    assert all(a["id"] != str(rex.id) for a in filtered_catalog)

    # A visitor gets "not found" on Rex's page.
    visitor_detail = await client.get(f"/animals/{rex.id}")
    assert visitor_detail.status_code == 404

    # Rex still appears in Ana's "My animals", marked as unpublished.
    ana_animals = (
        await client.get("/me/animals", headers=_bearer(issuer.token(**ANA)))
    ).json()
    rex_in_mine = next(a for a in ana_animals if a["id"] == str(rex.id))
    assert rex_in_mine["adoption_status"] == "unavailable"
