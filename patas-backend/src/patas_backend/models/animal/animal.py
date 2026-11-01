import re
from dataclasses import dataclass
from uuid import UUID, uuid4

from patas_backend.models.animal.enums import (
    AdoptionStatus,
    AnimalCompatibility,
    AnimalSex,
    AnimalSize,
    FirstTimeOwnerSuitability,
    NeuteredStatus,
    Species,
)
from patas_backend.models.animal.match_profile import AnimalMatchProfile
from patas_backend.models.matching.scales import EnergyLevel


class InvalidAnimal(ValueError):
    """An Animal invariant was violated."""


class AnimalUnauthorized(PermissionError):
    """The caller is not the owner of the animal."""


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

    def unpublish(self, by_user_id: UUID) -> None:
        """Unpublish the listing so it disappears from the catalog."""
        if self.owner_id != by_user_id:
            raise AnimalUnauthorized("Only the owner can unpublish this animal")
        self.adoption_status = AdoptionStatus.UNAVAILABLE

    def match_profile(self) -> AnimalMatchProfile:
        """This animal on the Matchmaker scales. Built on each call, so it follows
        the animal when it changes."""
        return AnimalMatchProfile.of(self)
