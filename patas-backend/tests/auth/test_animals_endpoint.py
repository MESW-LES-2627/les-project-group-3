import asyncio
from dataclasses import fields, replace
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
            "owner_name": "Ana",
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
                "training_needs": None,
                "noise_level": None,
                "life_stage": "adult",  # 14 months
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
    assert published["owner_name"] == "Ana"
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
        "training_needs": "low",
        "noise_level": "low",
        "life_stage": None,  # no age given
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
        if key
        not in {
            "id",
            "owner_id",
            "owner_name",
            "name",
            "species",
            "adoption_status",
        }
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
        pytest.param(
            {"name": "Rex", "species": "dog", "age_in_months": 2**31},
            id="age-beyond-storage",
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


async def test_acceptance_test_at_09_changing_name_updates_animal_publisher_display(
    client: httpx.AsyncClient, issuer: TokenIssuer, engine: AsyncEngine
) -> None:
    # AC 1: Given Ana is logged in, when she changes her name to "Ana Silva",
    # then Rex's page shows "Published by Ana Silva".
    rex, _, _ = await _seed_data(engine)

    # Initial check: Rex is published by Ana
    detail_res = await client.get(f"/animals/{rex.id}")
    assert detail_res.status_code == 200
    assert detail_res.json()["owner_name"] == "Ana"

    # Ana changes her name via PATCH /me
    patch_res = await client.patch(
        "/me",
        json={"name": "Ana Silva"},
        headers=_bearer(issuer.token(**ANA)),
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["name"] == "Ana Silva"

    # Rex's animal page now reflects the updated publisher name
    rex_page = await client.get(f"/animals/{rex.id}")
    assert rex_page.status_code == 200
    assert rex_page.json()["owner_name"] == "Ana Silva"

    # The public catalog also shows Rex with the updated publisher name
    catalog = (await client.get("/animals")).json()
    rex_in_catalog = next(a for a in catalog if a["id"] == str(rex.id))
    assert rex_in_catalog["owner_name"] == "Ana Silva"


async def _stored(engine: AsyncEngine, animal_id: UUID) -> Animal | None:
    async with async_sessionmaker(engine)() as session:
        return await AnimalRepository(session).get_by_id(animal_id)


def _rex_edit(**changes: object) -> dict[str, object]:
    """A PUT body for Rex: his seed description, with `changes` applied."""
    return {
        "name": "Rex",
        "species": "dog",
        "age_in_months": 36,
        "sex": "male",
        "size": "medium",
        **changes,
    }


async def test_acceptance_test_ana_edits_rex_and_his_page_shows_it(
    client: httpx.AsyncClient, issuer: TokenIssuer, engine: AsyncEngine
) -> None:
    # AT-03, edit half: when Ana changes Rex to large, his page shows large.
    # Lisboa and the filters come with US-06.
    rex, _, _ = await _seed_data(engine)

    response = await client.put(
        f"/animals/{rex.id}",
        json=_rex_edit(size="large"),
        headers=_bearer(issuer.token(**ANA)),
    )

    assert response.status_code == 200
    edited = response.json()
    assert edited["size"] == "large"
    # Derived from the animal, so it follows the edit (ADR 0011).
    assert edited["match_profile"]["size"] == "large"
    assert (await client.get(f"/animals/{rex.id}")).json() == edited
    catalog = (await client.get("/animals")).json()
    assert next(a for a in catalog if a["id"] == str(rex.id)) == edited


# Every description field, twice: each value differs between the two.
DESCRIBED = {
    "name": "Milo",
    "species": "cat",
    "age_in_months": 14,
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
}
REDESCRIBED = {
    "name": "Milo II",
    "species": "dog",
    "age_in_months": 15,
    "sex": "female",
    "is_neutered": "no",
    "postal_code": "4000-001",
    "size": "large",
    "activity_level": "high",
    "space_requirement": "large",
    "shedding": "high",
    "grooming_needs": "low",
    "behaves_well_with_children": "yes",
    "behaves_well_with_dogs": "no",
    "behaves_well_with_cats": "no",
    "behaves_well_with_other_animals": "yes",
    "training_needs": "high",
    "tolerance_for_time_alone": "low",
    "noise_level": "high",
    "suitable_for_first_time_owners": "no",
    "special_care_notes": "None any more",
    "other_details": "Loves the beach",
}


async def test_an_edit_saves_every_field(
    client: httpx.AsyncClient, issuer: TokenIssuer
) -> None:
    ana = _bearer(issuer.token(**ANA))
    milo = (await client.post("/animals", json=DESCRIBED, headers=ana)).json()

    response = await client.put(f"/animals/{milo['id']}", json=REDESCRIBED, headers=ana)

    assert response.status_code == 200
    edited = response.json()
    assert {key: edited[key] for key in REDESCRIBED} == REDESCRIBED
    assert (await client.get(f"/me/animals/{milo['id']}", headers=ana)).json() == edited


async def test_an_edit_clears_the_fields_it_leaves_out(
    client: httpx.AsyncClient, issuer: TokenIssuer
) -> None:
    ana = _bearer(issuer.token(**ANA))
    milo = (await client.post("/animals", json=DESCRIBED, headers=ana)).json()

    response = await client.put(
        f"/animals/{milo['id']}", json={"name": "Milo", "species": "cat"}, headers=ana
    )

    assert response.status_code == 200
    stored = (await client.get(f"/me/animals/{milo['id']}", headers=ana)).json()
    assert all(
        stored[key] is None for key in DESCRIBED if key not in {"name", "species"}
    )


@pytest.mark.parametrize(
    "invalid",
    [
        pytest.param({"name": "   "}, id="blank-name"),
        pytest.param({"age_in_months": -1}, id="negative-age"),
        pytest.param({"age_in_months": 2**31}, id="age-beyond-storage"),
        pytest.param({"species": "rabbit"}, id="unknown-species"),
        pytest.param({"postal_code": "12345"}, id="invalid-postal-code"),
        pytest.param({"activity_level": "extreme"}, id="invalid-activity-level"),
    ],
)
async def test_acceptance_test_an_invalid_edit_is_rejected_and_rex_is_unchanged(
    client: httpx.AsyncClient,
    issuer: TokenIssuer,
    engine: AsyncEngine,
    invalid: dict[str, object],
) -> None:
    # AT-02 for editing. The valid size change must not be saved either.
    rex, _, _ = await _seed_data(engine)

    response = await client.put(
        f"/animals/{rex.id}",
        json=_rex_edit(size="large", **invalid),
        headers=_bearer(issuer.token(**ANA)),
    )

    assert response.status_code == 422
    assert await _stored(engine, rex.id) == replace(rex, owner_name="Ana")


@pytest.mark.parametrize(
    "changes",
    [
        pytest.param({"size": "large"}, id="valid-edit"),
        # Ownership is checked before the rules: a broken rule is still a 403.
        pytest.param({"name": "   "}, id="edit-breaking-a-rule"),
    ],
)
async def test_acceptance_test_bruno_cannot_edit_rex(
    client: httpx.AsyncClient,
    issuer: TokenIssuer,
    engine: AsyncEngine,
    changes: dict[str, object],
) -> None:
    # AT-04: when Bruno tries to edit Rex, then it is refused and Rex is unchanged.
    rex, _, _ = await _seed_data(engine)

    response = await client.put(
        f"/animals/{rex.id}",
        json=_rex_edit(**changes),
        headers=_bearer(issuer.token(**BRUNO)),
    )

    assert response.status_code == 403
    assert await _stored(engine, rex.id) == replace(rex, owner_name="Ana")


async def test_acceptance_test_visitor_cannot_edit_rex(
    client: httpx.AsyncClient, engine: AsyncEngine
) -> None:
    # AT-04: a visitor who is not logged in is refused, and Rex is unchanged.
    rex, _, _ = await _seed_data(engine)

    response = await client.put(f"/animals/{rex.id}", json=_rex_edit(size="large"))

    assert response.status_code == 401
    assert await _stored(engine, rex.id) == replace(rex, owner_name="Ana")


async def test_editing_an_animal_that_does_not_exist_is_not_found(
    client: httpx.AsyncClient, issuer: TokenIssuer, engine: AsyncEngine
) -> None:
    await _seed_data(engine)

    response = await client.put(
        f"/animals/{uuid4()}", json=_rex_edit(), headers=_bearer(issuer.token(**ANA))
    )

    assert response.status_code == 404


async def test_owner_can_edit_an_unpublished_animal_and_it_stays_unpublished(
    client: httpx.AsyncClient, issuer: TokenIssuer, engine: AsyncEngine
) -> None:
    rex, _, _ = await _seed_data(engine)
    ana = _bearer(issuer.token(**ANA))
    await client.post(f"/animals/{rex.id}/unpublish", headers=ana)

    response = await client.put(
        f"/animals/{rex.id}", json=_rex_edit(size="large"), headers=ana
    )

    assert response.status_code == 200
    assert response.json()["size"] == "large"
    assert response.json()["adoption_status"] == "unavailable"
    assert all(a["id"] != str(rex.id) for a in (await client.get("/animals")).json())


@pytest.mark.parametrize(
    "unknown",
    [
        pytest.param({"adoption_status": "available"}, id="status"),
        pytest.param({"owner_id": BRUNO["sub"]}, id="owner"),
        pytest.param({"behaves_well_with_kids": "yes"}, id="misspelt-field"),
    ],
)
async def test_an_edit_with_a_field_outside_the_description_is_rejected(
    client: httpx.AsyncClient,
    issuer: TokenIssuer,
    engine: AsyncEngine,
    unknown: dict[str, object],
) -> None:
    rex, _, _ = await _seed_data(engine)

    response = await client.put(
        f"/animals/{rex.id}",
        json=_rex_edit(size="large", **unknown),
        headers=_bearer(issuer.token(**ANA)),
    )

    assert response.status_code == 422
    assert await _stored(engine, rex.id) == replace(rex, owner_name="Ana")


async def test_owner_loads_her_unpublished_animal_for_the_edit_form(
    client: httpx.AsyncClient, issuer: TokenIssuer, engine: AsyncEngine
) -> None:
    _, mia, _ = await _seed_data(engine)
    ana = _bearer(issuer.token(**ANA))
    await client.post(f"/animals/{mia.id}/unpublish", headers=ana)

    response = await client.get(f"/me/animals/{mia.id}", headers=ana)

    assert response.status_code == 200
    assert response.json()["name"] == "Mia"
    assert response.json()["adoption_status"] == "unavailable"


async def test_someone_elses_animal_is_not_in_my_animals(
    client: httpx.AsyncClient, issuer: TokenIssuer, engine: AsyncEngine
) -> None:
    rex, _, _ = await _seed_data(engine)
    bruno = _bearer(issuer.token(**BRUNO))

    rexs_page = await client.get(f"/me/animals/{rex.id}", headers=bruno)
    unknown_page = await client.get(f"/me/animals/{uuid4()}", headers=bruno)

    assert rexs_page.status_code == 404
    assert unknown_page.status_code == 404


async def test_a_visitor_cannot_load_an_animal_for_editing(
    client: httpx.AsyncClient, engine: AsyncEngine
) -> None:
    rex, _, _ = await _seed_data(engine)

    assert (await client.get(f"/me/animals/{rex.id}")).status_code == 401


async def _until_a_request_waits_for(engine: AsyncEngine, holder_pid: int) -> None:
    """Wait until a connection is blocked by `holder_pid`: the two writes met."""
    query = text(
        "SELECT count(*) FROM pg_stat_activity"
        " WHERE :holder = ANY(pg_blocking_pids(pid))"
    )
    # Autocommit, so each probe sees connections opened since the last one.
    async with engine.connect() as conn:
        conn = await conn.execution_options(isolation_level="AUTOCOMMIT")
        for _ in range(100):
            if await conn.scalar(query, {"holder": holder_pid}):
                return
            await asyncio.sleep(0.05)
    pytest.fail("no request waited for the lock")


async def test_an_edit_that_meets_an_unpublish_does_not_republish_rex(
    client: httpx.AsyncClient, issuer: TokenIssuer, engine: AsyncEngine
) -> None:
    # The edit waits for the unpublish instead of writing the old status back.
    rex, _, _ = await _seed_data(engine)

    async with async_sessionmaker(engine).begin() as session:
        repo = AnimalRepository(session)
        being_unpublished = await repo.get_for_update(rex.id)
        assert being_unpublished is not None
        holder_pid = await session.scalar(text("SELECT pg_backend_pid()"))
        edit = asyncio.create_task(
            client.put(
                f"/animals/{rex.id}",
                json=_rex_edit(size="large"),
                headers=_bearer(issuer.token(**ANA)),
            )
        )
        await _until_a_request_waits_for(engine, holder_pid)
        being_unpublished.unpublish(by_user_id=rex.owner_id)
        await repo.update(being_unpublished)

    assert (await edit).status_code == 200
    stored = await _stored(engine, rex.id)
    assert stored is not None
    assert stored.size is AnimalSize.LARGE
    assert stored.adoption_status is AdoptionStatus.UNAVAILABLE


async def test_an_unpublish_that_meets_an_edit_keeps_the_edit(
    client: httpx.AsyncClient, issuer: TokenIssuer, engine: AsyncEngine
) -> None:
    # The other order: the unpublish waits for the edit and keeps it.
    rex, _, _ = await _seed_data(engine)

    async with async_sessionmaker(engine).begin() as session:
        repo = AnimalRepository(session)
        being_edited = await repo.get_for_update(rex.id)
        assert being_edited is not None
        holder_pid = await session.scalar(text("SELECT pg_backend_pid()"))
        unpublish = asyncio.create_task(
            client.post(
                f"/animals/{rex.id}/unpublish", headers=_bearer(issuer.token(**ANA))
            )
        )
        await _until_a_request_waits_for(engine, holder_pid)
        being_edited.edit(
            rex.owner_id, name="Rex", species=Species.DOG, size=AnimalSize.LARGE
        )
        await repo.update(being_edited)

    assert (await unpublish).status_code == 200
    stored = await _stored(engine, rex.id)
    assert stored is not None
    assert stored.size is AnimalSize.LARGE
    assert stored.adoption_status is AdoptionStatus.UNAVAILABLE
