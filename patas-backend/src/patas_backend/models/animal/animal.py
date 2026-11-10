import re
from dataclasses import dataclass, fields, replace
from uuid import UUID, uuid4

from patas_backend.models.animal.enums import (
    AdoptionStatus,
    AnimalCompatibility,
    AnimalSex,
    AnimalSize,
    District,
    FirstTimeOwnerSuitability,
    NeuteredStatus,
    Species,
)
from patas_backend.models.animal.events import AnimalUnpublished
from patas_backend.models.animal.match_profile import AnimalMatchProfile
from patas_backend.models.events import DomainEvent
from patas_backend.models.matching.scales import EnergyLevel


class InvalidAnimal(ValueError):
    """An Animal invariant was violated."""


class AnimalUnauthorized(PermissionError):
    """The caller is not the owner of the animal."""


class InvalidAnimalTransition(Exception):
    """The animal's adoption status does not allow this change."""


def validate_name(name: str) -> str:
    cleaned = name.strip()
    if not cleaned:
        raise InvalidAnimal("name must not be blank")
    return cleaned


def validate_age_in_months(age_in_months: int | None) -> int | None:
    if age_in_months is not None and age_in_months < 0:
        raise InvalidAnimal("age must not be negative")
    return age_in_months


def validate_optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


def validate_postal_code(value: str | None) -> str | None:
    cleaned = validate_optional_text(value)
    if cleaned is not None and re.fullmatch(r"[0-9]{4}-[0-9]{3}", cleaned) is None:
        raise InvalidAnimal("postal code must use the Portuguese format NNNN-NNN")
    return cleaned


@dataclass
class Animal:
    id: UUID
    owner_id: UUID
    name: str
    species: Species
    owner_name: str = ""
    age_in_months: int | None = None
    adoption_status: AdoptionStatus = AdoptionStatus.AVAILABLE
    sex: AnimalSex | None = None
    is_neutered: NeuteredStatus | None = None
    postal_code: str | None = None
    district: District | None = None
    size: AnimalSize | None = None
    activity_level: EnergyLevel | None = None
    space_requirement: AnimalSize | None = None
    shedding: EnergyLevel | None = None
    grooming_needs: EnergyLevel | None = None
    behaves_well_with_children: AnimalCompatibility | None = None
    behaves_well_with_dogs: AnimalCompatibility | None = None
    behaves_well_with_cats: AnimalCompatibility | None = None
    behaves_well_with_other_animals: AnimalCompatibility | None = None
    training_needs: EnergyLevel | None = None
    tolerance_for_time_alone: EnergyLevel | None = None
    noise_level: EnergyLevel | None = None
    suitable_for_first_time_owners: FirstTimeOwnerSuitability | None = None
    special_care_notes: str | None = None
    other_details: str | None = None

    def __post_init__(self) -> None:
        # Invariants hold however an Animal is built (published or loaded from the DB).
        self.name = validate_name(self.name)
        self.age_in_months = validate_age_in_months(self.age_in_months)
        self.postal_code = validate_postal_code(self.postal_code)
        self.special_care_notes = validate_optional_text(self.special_care_notes)
        self.other_details = validate_optional_text(self.other_details)
        # Not a dataclass field: it is not part of the animal's data, so asdict()
        # and replace() never see it.
        self._events: list[DomainEvent] = []

    @classmethod
    def publish(
        cls,
        *,
        owner_id: UUID,
        name: str,
        species: Species,
        owner_name: str = "",
        age_in_months: int | None = None,
        sex: AnimalSex | None = None,
        is_neutered: NeuteredStatus | None = None,
        postal_code: str | None = None,
        district: District | None = None,
        size: AnimalSize | None = None,
        activity_level: EnergyLevel | None = None,
        space_requirement: AnimalSize | None = None,
        shedding: EnergyLevel | None = None,
        grooming_needs: EnergyLevel | None = None,
        behaves_well_with_children: AnimalCompatibility | None = None,
        behaves_well_with_dogs: AnimalCompatibility | None = None,
        behaves_well_with_cats: AnimalCompatibility | None = None,
        behaves_well_with_other_animals: AnimalCompatibility | None = None,
        training_needs: EnergyLevel | None = None,
        tolerance_for_time_alone: EnergyLevel | None = None,
        noise_level: EnergyLevel | None = None,
        suitable_for_first_time_owners: FirstTimeOwnerSuitability | None = None,
        special_care_notes: str | None = None,
        other_details: str | None = None,
    ) -> "Animal":
        """Create a new listing. It always starts available, owned by its publisher."""
        return cls(
            id=uuid4(),
            owner_id=owner_id,
            name=name,
            species=species,
            owner_name=owner_name,
            age_in_months=age_in_months,
            sex=sex,
            is_neutered=is_neutered,
            postal_code=postal_code,
            district=district,
            size=size,
            activity_level=activity_level,
            space_requirement=space_requirement,
            shedding=shedding,
            grooming_needs=grooming_needs,
            behaves_well_with_children=behaves_well_with_children,
            behaves_well_with_dogs=behaves_well_with_dogs,
            behaves_well_with_cats=behaves_well_with_cats,
            behaves_well_with_other_animals=behaves_well_with_other_animals,
            training_needs=training_needs,
            tolerance_for_time_alone=tolerance_for_time_alone,
            noise_level=noise_level,
            suitable_for_first_time_owners=suitable_for_first_time_owners,
            special_care_notes=special_care_notes,
            other_details=other_details,
        )

    @property
    def is_published(self) -> bool:
        """An animal is published if its adoption status is not unavailable."""
        return self.adoption_status != AdoptionStatus.UNAVAILABLE

    def is_owned_by(self, user_id: UUID) -> bool:
        return self.owner_id == user_id

    def edit(
        self,
        by_user_id: UUID,
        *,
        name: str,
        species: Species,
        age_in_months: int | None = None,
        sex: AnimalSex | None = None,
        is_neutered: NeuteredStatus | None = None,
        postal_code: str | None = None,
        district: District | None = None,
        size: AnimalSize | None = None,
        activity_level: EnergyLevel | None = None,
        space_requirement: AnimalSize | None = None,
        shedding: EnergyLevel | None = None,
        grooming_needs: EnergyLevel | None = None,
        behaves_well_with_children: AnimalCompatibility | None = None,
        behaves_well_with_dogs: AnimalCompatibility | None = None,
        behaves_well_with_cats: AnimalCompatibility | None = None,
        behaves_well_with_other_animals: AnimalCompatibility | None = None,
        training_needs: EnergyLevel | None = None,
        tolerance_for_time_alone: EnergyLevel | None = None,
        noise_level: EnergyLevel | None = None,
        suitable_for_first_time_owners: FirstTimeOwnerSuitability | None = None,
        special_care_notes: str | None = None,
        other_details: str | None = None,
    ) -> None:
        """Replace the description; a field left out is cleared. All or nothing."""
        if not self.is_owned_by(by_user_id):
            raise AnimalUnauthorized("Only the owner can edit this animal")
        # replace() runs the constructor's checks on a copy, so a broken rule
        # leaves this animal untouched.
        edited = replace(
            self,
            name=name,
            species=species,
            age_in_months=age_in_months,
            sex=sex,
            is_neutered=is_neutered,
            postal_code=postal_code,
            district=district,
            size=size,
            activity_level=activity_level,
            space_requirement=space_requirement,
            shedding=shedding,
            grooming_needs=grooming_needs,
            behaves_well_with_children=behaves_well_with_children,
            behaves_well_with_dogs=behaves_well_with_dogs,
            behaves_well_with_cats=behaves_well_with_cats,
            behaves_well_with_other_animals=behaves_well_with_other_animals,
            training_needs=training_needs,
            tolerance_for_time_alone=tolerance_for_time_alone,
            noise_level=noise_level,
            suitable_for_first_time_owners=suitable_for_first_time_owners,
            special_care_notes=special_care_notes,
            other_details=other_details,
        )
        # Only the declared fields: vars() would also copy the edited copy's empty
        # event list over the events this animal has recorded.
        for field in fields(edited):
            setattr(self, field.name, getattr(edited, field.name))

    def _move(
        self, source: AdoptionStatus, target: AdoptionStatus, action: str
    ) -> None:
        if self.adoption_status is not source:
            raise InvalidAnimalTransition(
                f"an animal that is {self.adoption_status.value} cannot be {action}"
            )
        self.adoption_status = target

    def reserve(self) -> None:
        """An application was accepted for this animal."""
        self._move(AdoptionStatus.AVAILABLE, AdoptionStatus.RESERVED, "reserved")

    def release(self) -> None:
        """The accepted application ended without an adoption."""
        self._move(AdoptionStatus.RESERVED, AdoptionStatus.AVAILABLE, "released")

    def mark_adopted(self) -> None:
        """Owner and applicant both confirmed the handover."""
        self._move(AdoptionStatus.RESERVED, AdoptionStatus.ADOPTED, "adopted")

    def pull_events(self) -> list[DomainEvent]:
        """The events recorded since the last call; each is returned once."""
        events, self._events = self._events, []
        return events

    def unpublish(self, by_user_id: UUID) -> None:
        """Unpublish the listing so it disappears from the catalog.

        Only an available animal can be unpublished: a reserved or adopted one is
        part of an adoption. Unpublishing twice changes nothing.
        """
        if not self.is_owned_by(by_user_id):
            raise AnimalUnauthorized("Only the owner can unpublish this animal")
        if self.adoption_status is AdoptionStatus.UNAVAILABLE:
            return
        self._move(AdoptionStatus.AVAILABLE, AdoptionStatus.UNAVAILABLE, "unpublished")
        self._events.append(AnimalUnpublished(animal_id=self.id))

    def match_profile(self) -> AnimalMatchProfile:
        """This animal on the Matchmaker scales. Built on each call, so it follows
        the animal when it changes."""
        return AnimalMatchProfile.of(self)
