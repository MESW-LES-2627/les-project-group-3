from dataclasses import asdict
from uuid import UUID, uuid4

import pytest

from patas_backend.models.animal import (
    AdoptionStatus,
    Animal,
    AnimalCompatibility,
    AnimalNotAvailable,
    AnimalSex,
    AnimalSize,
    AnimalUnauthorized,
    AnimalUnpublished,
    District,
    FirstTimeOwnerSuitability,
    InvalidAnimal,
    InvalidAnimalTransition,
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


def _animal_in(status: AdoptionStatus) -> Animal:
    animal = _publish()
    animal.adoption_status = status
    return animal


# action -> (the only status it starts from, the status it ends in)
TRANSITIONS = {
    "reserve": (AdoptionStatus.AVAILABLE, AdoptionStatus.RESERVED),
    "release": (AdoptionStatus.RESERVED, AdoptionStatus.AVAILABLE),
    "mark_adopted": (AdoptionStatus.RESERVED, AdoptionStatus.ADOPTED),
}
REFUSED = [
    (action, status)
    for action, (source, _) in TRANSITIONS.items()
    for status in AdoptionStatus
    if status is not source
]


@pytest.mark.parametrize("action", TRANSITIONS)
def test_a_transition_moves_the_animal_from_its_required_status(action: str) -> None:
    source, target = TRANSITIONS[action]
    animal = _animal_in(source)

    getattr(animal, action)()

    assert animal.adoption_status is target


@pytest.mark.parametrize(("action", "status"), REFUSED)
def test_a_transition_is_refused_from_any_other_status(
    action: str, status: AdoptionStatus
) -> None:
    animal = _animal_in(status)

    with pytest.raises(InvalidAnimalTransition):
        getattr(animal, action)()

    assert animal.adoption_status is status


def test_unpublishing_records_one_event_that_can_be_pulled_once() -> None:
    animal = _publish()

    animal.unpublish(by_user_id=OWNER_ID)

    assert animal.pull_events() == [AnimalUnpublished(animal_id=animal.id)]
    assert animal.pull_events() == []


@pytest.mark.parametrize("status", [AdoptionStatus.RESERVED, AdoptionStatus.ADOPTED])
def test_unpublish_is_refused_while_reserved_or_adopted(
    status: AdoptionStatus,
) -> None:
    animal = _animal_in(status)

    with pytest.raises(InvalidAnimalTransition):
        animal.unpublish(by_user_id=OWNER_ID)

    assert animal.adoption_status is status
    assert animal.pull_events() == []


def test_unpublishing_twice_changes_nothing_the_second_time() -> None:
    animal = _publish()
    animal.unpublish(by_user_id=OWNER_ID)
    animal.pull_events()

    animal.unpublish(by_user_id=OWNER_ID)

    assert animal.adoption_status is AdoptionStatus.UNAVAILABLE
    assert animal.pull_events() == []


def test_a_non_owner_is_refused_before_the_status_is_checked() -> None:
    animal = _animal_in(AdoptionStatus.RESERVED)

    with pytest.raises(AnimalUnauthorized):
        animal.unpublish(by_user_id=uuid4())


def test_an_edit_keeps_the_recorded_events() -> None:
    animal = _publish()
    animal.unpublish(by_user_id=OWNER_ID)

    animal.edit(OWNER_ID, name="Rex", species=Species.DOG)

    assert animal.pull_events() == [AnimalUnpublished(animal_id=animal.id)]


def test_an_available_animal_is_open_to_requests() -> None:
    animal = _publish()

    animal.ensure_open_to_requests()

    assert animal.adoption_status is AdoptionStatus.AVAILABLE


@pytest.mark.parametrize(
    "status",
    [AdoptionStatus.RESERVED, AdoptionStatus.ADOPTED, AdoptionStatus.UNAVAILABLE],
)
def test_an_animal_that_is_not_available_is_not_open_to_requests(
    status: AdoptionStatus,
) -> None:
    animal = _animal_in(status)

    with pytest.raises(AnimalNotAvailable):
        animal.ensure_open_to_requests()

    assert animal.adoption_status is status
    assert animal.pull_events() == []


def test_an_unpublished_animal_is_not_open_to_requests() -> None:
    # The real way to reach UNAVAILABLE, not a status set by hand.
    animal = _publish()
    animal.unpublish(by_user_id=OWNER_ID)

    with pytest.raises(AnimalNotAvailable):
        animal.ensure_open_to_requests()
