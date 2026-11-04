from dataclasses import asdict
from uuid import UUID, uuid4

import pytest

from patas_backend.models.animal import (
    AdoptionStatus,
    Animal,
    AnimalCompatibility,
    AnimalSex,
    AnimalSize,
    AnimalUnauthorized,
    District,
    FirstTimeOwnerSuitability,
    InvalidAnimal,
    NeuteredStatus,
    Species,
)
from patas_backend.models.matching.scales import EnergyLevel

OWNER_ID = UUID("0b1f2a3c-4d5e-4f60-8a7b-9c0d1e2f3a4b")


def _publish(**overrides: object) -> Animal:
    return Animal.publish(
        **{
            "owner_id": OWNER_ID,
            "name": "Rex",
            "species": Species.DOG,
            "age_in_months": 12,
            **overrides,
        }
    )


def test_a_published_animal_is_available_and_owned_by_the_publisher() -> None:
    animal = _publish()

    assert animal.owner_id == OWNER_ID
    assert animal.adoption_status is AdoptionStatus.AVAILABLE


def test_each_published_animal_gets_its_own_id() -> None:
    assert _publish().id != _publish().id


def test_name_is_trimmed() -> None:
    assert _publish(name="  Rex  ").name == "Rex"


@pytest.mark.parametrize("name", ["", "   "])
def test_blank_name_is_rejected(name: str) -> None:
    with pytest.raises(InvalidAnimal):
        _publish(name=name)


def test_negative_age_is_rejected() -> None:
    with pytest.raises(InvalidAnimal):
        _publish(age_in_months=-1)


def test_a_newborn_of_zero_months_is_accepted() -> None:
    assert _publish(age_in_months=0).age_in_months == 0


def test_age_is_optional() -> None:
    assert _publish(age_in_months=None).age_in_months is None


def test_invariants_hold_when_built_directly() -> None:
    # Loading from the database goes through the constructor, not `publish`.
    with pytest.raises(InvalidAnimal):
        Animal(id=uuid4(), owner_id=OWNER_ID, name=" ", species=Species.DOG)


def test_optional_profile_fields_are_empty_by_default() -> None:
    animal = _publish()

    assert animal.sex is None
    assert animal.is_neutered is None
    assert animal.activity_level is None
    assert animal.behaves_well_with_children is None
    assert animal.special_care_notes is None


def test_optional_profile_fields_are_kept_and_free_text_is_trimmed() -> None:
    animal = _publish(
        sex=AnimalSex.FEMALE,
        is_neutered=NeuteredStatus.YES,
        postal_code="1234-567",
        size=AnimalSize.SMALL,
        activity_level=EnergyLevel.MODERATE,
        behaves_well_with_children=AnimalCompatibility.WITH_SUPERVISION,
        suitable_for_first_time_owners=FirstTimeOwnerSuitability.WITH_SUPPORT,
        special_care_notes="  Daily medication  ",
    )

    assert animal.sex is AnimalSex.FEMALE
    assert animal.is_neutered is NeuteredStatus.YES
    assert animal.activity_level is EnergyLevel.MODERATE
    assert animal.behaves_well_with_children is AnimalCompatibility.WITH_SUPERVISION
    assert (
        animal.suitable_for_first_time_owners is FirstTimeOwnerSuitability.WITH_SUPPORT
    )
    assert animal.special_care_notes == "Daily medication"


@pytest.mark.parametrize("postal_code", ["1234567", "1234-56A", "123-4567"])
def test_invalid_portuguese_postal_code_is_rejected(postal_code: str) -> None:
    with pytest.raises(InvalidAnimal, match="Portuguese format"):
        _publish(postal_code=postal_code)


def test_owner_can_unpublish_animal() -> None:
    animal = _publish()
    assert animal.is_published is True

    animal.unpublish(by_user_id=OWNER_ID)

    assert animal.adoption_status is AdoptionStatus.UNAVAILABLE
    assert animal.is_published is False


def test_non_owner_cannot_unpublish_animal() -> None:
    animal = _publish()
    other_user = uuid4()

    with pytest.raises(AnimalUnauthorized):
        animal.unpublish(by_user_id=other_user)

    assert animal.adoption_status is AdoptionStatus.AVAILABLE
    assert animal.is_published is True


def _rex_before_edit() -> Animal:
    return _publish(
        size=AnimalSize.MEDIUM,
        sex=AnimalSex.MALE,
        postal_code="4000-001",
        district=District.PORTO,
        special_care_notes="Hip check every year",
    )


def test_owner_can_edit_the_description() -> None:
    animal = _rex_before_edit()
    id_before = animal.id

    animal.edit(
        OWNER_ID,
        name="  Rex  ",
        species=Species.DOG,
        age_in_months=36,
        sex=AnimalSex.MALE,
        size=AnimalSize.LARGE,
        postal_code="1000-001",
        district=District.LISBOA,
        activity_level=EnergyLevel.HIGH,
        other_details="  Loves the beach  ",
    )

    assert animal.size is AnimalSize.LARGE
    assert animal.postal_code == "1000-001"
    assert animal.district is District.LISBOA
    assert animal.age_in_months == 36
    assert animal.activity_level is EnergyLevel.HIGH
    # Cleaned by the same rules as publishing.
    assert animal.name == "Rex"
    assert animal.other_details == "Loves the beach"
    # Left out of the edit, so cleared.
    assert animal.special_care_notes is None
    assert animal.id == id_before
    assert animal.owner_id == OWNER_ID


def test_an_edit_keeps_the_adoption_status() -> None:
    animal = _rex_before_edit()
    animal.unpublish(by_user_id=OWNER_ID)

    animal.edit(OWNER_ID, name="Rex", species=Species.DOG)

    assert animal.adoption_status is AdoptionStatus.UNAVAILABLE


def test_non_owner_cannot_edit_and_the_animal_is_unchanged() -> None:
    animal = _rex_before_edit()
    before = asdict(animal)

    with pytest.raises(AnimalUnauthorized):
        animal.edit(uuid4(), name="Rex", species=Species.DOG, size=AnimalSize.LARGE)

    assert asdict(animal) == before


@pytest.mark.parametrize(
    "invalid",
    [
        pytest.param({"name": "   "}, id="blank-name"),
        pytest.param({"age_in_months": -1}, id="negative-age"),
        pytest.param({"postal_code": "12345"}, id="invalid-postal-code"),
    ],
)
def test_an_invalid_edit_changes_nothing(invalid: dict[str, object]) -> None:
    # The valid size change must not stick either.
    animal = _rex_before_edit()
    before = asdict(animal)
    edit: dict[str, object] = {
        "name": "Rex",
        "species": Species.DOG,
        "size": AnimalSize.LARGE,
        **invalid,
    }

    with pytest.raises(InvalidAnimal):
        animal.edit(OWNER_ID, **edit)

    assert asdict(animal) == before


def test_the_match_profile_follows_an_edit() -> None:
    animal = _rex_before_edit()
    assert animal.match_profile().size is AnimalSize.MEDIUM

    animal.edit(OWNER_ID, name="Rex", species=Species.DOG, size=AnimalSize.LARGE)

    assert animal.match_profile().size is AnimalSize.LARGE
