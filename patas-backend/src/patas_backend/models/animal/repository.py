from typing import Any
from uuid import UUID

from sqlalchemy import Row, text
from sqlalchemy.ext.asyncio import AsyncSession

from patas_backend.models.animal.animal import Animal
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
from patas_backend.models.matching.scales import EnergyLevel

_INSERT = text(
    """
    INSERT INTO patas.animals
        (
            id, owner_id, name, species, age_in_months, adoption_status, sex,
            is_neutered, postal_code, size, activity_level, space_requirement,
            shedding, grooming_needs, behaves_well_with_children,
            behaves_well_with_dogs, behaves_well_with_cats,
            behaves_well_with_other_animals, training_needs,
            tolerance_for_time_alone, noise_level, suitable_for_first_time_owners,
            special_care_notes, other_details, district
        )
    VALUES (
        :id, :owner_id, :name, CAST(:species AS patas.species), :age_in_months,
        CAST(:adoption_status AS patas.adoption_status),
        CAST(:sex AS patas.animal_sex),
        CAST(:is_neutered AS patas.neutered_status),
        :postal_code,
        CAST(:size AS patas.animal_size),
        CAST(:activity_level AS patas.energy_level),
        CAST(:space_requirement AS patas.animal_size),
        CAST(:shedding AS patas.energy_level),
        CAST(:grooming_needs AS patas.energy_level),
        CAST(:behaves_well_with_children AS patas.animal_compatibility),
        CAST(:behaves_well_with_dogs AS patas.animal_compatibility),
        CAST(:behaves_well_with_cats AS patas.animal_compatibility),
        CAST(:behaves_well_with_other_animals AS patas.animal_compatibility),
        CAST(:training_needs AS patas.energy_level),
        CAST(:tolerance_for_time_alone AS patas.energy_level),
        CAST(:noise_level AS patas.energy_level),
        CAST(:suitable_for_first_time_owners AS patas.first_time_owner_suitability),
        :special_care_notes,
        :other_details,
        CAST(:district AS patas.district)
    )
    """
)
# created_at ties only inside one transaction (now() is fixed per transaction), so
# id keeps the order deterministic there.
_SELECT_ALL_PUBLISHED = text(
    """
    SELECT
        a.id, a.owner_id, u.name AS owner_name, a.name, a.species,
        a.age_in_months, a.adoption_status, a.sex, a.is_neutered,
        a.postal_code, a.size, a.activity_level, a.space_requirement,
        a.shedding, a.grooming_needs, a.behaves_well_with_children,
        a.behaves_well_with_dogs, a.behaves_well_with_cats,
        a.behaves_well_with_other_animals, a.training_needs,
        a.tolerance_for_time_alone, a.noise_level,
        a.suitable_for_first_time_owners, a.special_care_notes,
        a.other_details, a.district
    FROM patas.animals a
    JOIN patas.users u ON u.id = a.owner_id
    WHERE a.adoption_status != 'unavailable'
    ORDER BY a.created_at DESC, a.id
    """
)

_SELECT_BY_OWNER = text(
    """
    SELECT
        a.id, a.owner_id, u.name AS owner_name, a.name, a.species,
        a.age_in_months, a.adoption_status, a.sex, a.is_neutered,
        a.postal_code, a.size, a.activity_level, a.space_requirement,
        a.shedding, a.grooming_needs, a.behaves_well_with_children,
        a.behaves_well_with_dogs, a.behaves_well_with_cats,
        a.behaves_well_with_other_animals, a.training_needs,
        a.tolerance_for_time_alone, a.noise_level,
        a.suitable_for_first_time_owners, a.special_care_notes,
        a.other_details, a.district
    FROM patas.animals a
    JOIN patas.users u ON u.id = a.owner_id
    WHERE a.owner_id = :owner_id
    ORDER BY a.created_at DESC, a.id
    """
)

_SELECT_BY_ID = text(
    """
    SELECT
        a.id, a.owner_id, u.name AS owner_name, a.name, a.species,
        a.age_in_months, a.adoption_status, a.sex, a.is_neutered,
        a.postal_code, a.size, a.activity_level, a.space_requirement,
        a.shedding, a.grooming_needs, a.behaves_well_with_children,
        a.behaves_well_with_dogs, a.behaves_well_with_cats,
        a.behaves_well_with_other_animals, a.training_needs,
        a.tolerance_for_time_alone, a.noise_level,
        a.suitable_for_first_time_owners, a.special_care_notes,
        a.other_details, a.district
    FROM patas.animals a
    JOIN patas.users u ON u.id = a.owner_id
    WHERE a.id = :id
    """
)
# OF a: lock the animal's row, not its owner's.
_SELECT_BY_ID_FOR_UPDATE = text(_SELECT_BY_ID.text + "FOR UPDATE OF a")


_UPDATE = text(
    """
    UPDATE patas.animals
    SET
        name = :name,
        species = CAST(:species AS patas.species),
        age_in_months = :age_in_months,
        adoption_status = CAST(:adoption_status AS patas.adoption_status),
        sex = CAST(:sex AS patas.animal_sex),
        is_neutered = CAST(:is_neutered AS patas.neutered_status),
        postal_code = :postal_code,
        size = CAST(:size AS patas.animal_size),
        activity_level = CAST(:activity_level AS patas.energy_level),
        space_requirement = CAST(:space_requirement AS patas.animal_size),
        shedding = CAST(:shedding AS patas.energy_level),
        grooming_needs = CAST(:grooming_needs AS patas.energy_level),
        behaves_well_with_children =
            CAST(:behaves_well_with_children AS patas.animal_compatibility),
        behaves_well_with_dogs =
            CAST(:behaves_well_with_dogs AS patas.animal_compatibility),
        behaves_well_with_cats =
            CAST(:behaves_well_with_cats AS patas.animal_compatibility),
        behaves_well_with_other_animals =
            CAST(:behaves_well_with_other_animals AS patas.animal_compatibility),
        training_needs = CAST(:training_needs AS patas.energy_level),
        tolerance_for_time_alone =
            CAST(:tolerance_for_time_alone AS patas.energy_level),
        noise_level = CAST(:noise_level AS patas.energy_level),
        suitable_for_first_time_owners =
            CAST(:suitable_for_first_time_owners AS patas.first_time_owner_suitability),
        special_care_notes = :special_care_notes,
        other_details = :other_details,
        district = CAST(:district AS patas.district)
    WHERE id = :id
    """
)


def _to_params(animal: Animal) -> dict[str, Any]:
    return {
        "id": animal.id,
        "owner_id": animal.owner_id,
        "name": animal.name,
        "species": animal.species.value,
        "age_in_months": animal.age_in_months,
        "adoption_status": animal.adoption_status.value,
        "sex": animal.sex.value if animal.sex is not None else None,
        "is_neutered": (
            animal.is_neutered.value if animal.is_neutered is not None else None
        ),
        "postal_code": animal.postal_code,
        "size": animal.size.value if animal.size is not None else None,
        "activity_level": (
            animal.activity_level.value if animal.activity_level is not None else None
        ),
        "space_requirement": (
            animal.space_requirement.value
            if animal.space_requirement is not None
            else None
        ),
        "shedding": animal.shedding.value if animal.shedding is not None else None,
        "grooming_needs": (
            animal.grooming_needs.value if animal.grooming_needs is not None else None
        ),
        "behaves_well_with_children": (
            animal.behaves_well_with_children.value
            if animal.behaves_well_with_children is not None
            else None
        ),
        "behaves_well_with_dogs": (
            animal.behaves_well_with_dogs.value
            if animal.behaves_well_with_dogs is not None
            else None
        ),
        "behaves_well_with_cats": (
            animal.behaves_well_with_cats.value
            if animal.behaves_well_with_cats is not None
            else None
        ),
        "behaves_well_with_other_animals": (
            animal.behaves_well_with_other_animals.value
            if animal.behaves_well_with_other_animals is not None
            else None
        ),
        "training_needs": (
            animal.training_needs.value if animal.training_needs is not None else None
        ),
        "tolerance_for_time_alone": (
            animal.tolerance_for_time_alone.value
            if animal.tolerance_for_time_alone is not None
            else None
        ),
        "noise_level": (
            animal.noise_level.value if animal.noise_level is not None else None
        ),
        "suitable_for_first_time_owners": (
            animal.suitable_for_first_time_owners.value
            if animal.suitable_for_first_time_owners is not None
            else None
        ),
        "special_care_notes": animal.special_care_notes,
        "other_details": animal.other_details,
        "district": animal.district.value if animal.district is not None else None,
    }


def _from_row(row: Row[Any]) -> Animal:
    return Animal(
        id=row.id,
        owner_id=row.owner_id,
        owner_name=getattr(row, "owner_name", ""),
        name=row.name,
        species=Species(row.species),
        age_in_months=row.age_in_months,
        adoption_status=AdoptionStatus(row.adoption_status),
        sex=AnimalSex(row.sex) if row.sex is not None else None,
        is_neutered=(
            NeuteredStatus(row.is_neutered) if row.is_neutered is not None else None
        ),
        postal_code=row.postal_code,
        size=AnimalSize(row.size) if row.size is not None else None,
        activity_level=(
            EnergyLevel(row.activity_level) if row.activity_level is not None else None
        ),
        space_requirement=(
            AnimalSize(row.space_requirement)
            if row.space_requirement is not None
            else None
        ),
        shedding=EnergyLevel(row.shedding) if row.shedding is not None else None,
        grooming_needs=(
            EnergyLevel(row.grooming_needs) if row.grooming_needs is not None else None
        ),
        behaves_well_with_children=(
            AnimalCompatibility(row.behaves_well_with_children)
            if row.behaves_well_with_children is not None
            else None
        ),
        behaves_well_with_dogs=(
            AnimalCompatibility(row.behaves_well_with_dogs)
            if row.behaves_well_with_dogs is not None
            else None
        ),
        behaves_well_with_cats=(
            AnimalCompatibility(row.behaves_well_with_cats)
            if row.behaves_well_with_cats is not None
            else None
        ),
        behaves_well_with_other_animals=(
            AnimalCompatibility(row.behaves_well_with_other_animals)
            if row.behaves_well_with_other_animals is not None
            else None
        ),
        training_needs=(
            EnergyLevel(row.training_needs) if row.training_needs is not None else None
        ),
        tolerance_for_time_alone=(
            EnergyLevel(row.tolerance_for_time_alone)
            if row.tolerance_for_time_alone is not None
            else None
        ),
        noise_level=(
            EnergyLevel(row.noise_level) if row.noise_level is not None else None
        ),
        suitable_for_first_time_owners=(
            FirstTimeOwnerSuitability(row.suitable_for_first_time_owners)
            if row.suitable_for_first_time_owners is not None
            else None
        ),
        special_care_notes=row.special_care_notes,
        other_details=row.other_details,
        district=District(row.district) if row.district is not None else None,
    )


class AnimalRepository:
    """Persistence for Animal. The caller owns the transaction (this never commits)."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, animal: Animal) -> None:
        await self._session.execute(_INSERT, _to_params(animal))

    async def update(self, animal: Animal) -> None:
        """Update an animal listing. Must be called within a transaction."""
        await self._session.execute(_UPDATE, _to_params(animal))

    async def get_by_id(self, animal_id: UUID) -> Animal | None:
        """Fetch a single animal by id, or None if not found."""
        result = await self._session.execute(_SELECT_BY_ID, {"id": animal_id})
        row = result.first()
        return _from_row(row) if row is not None else None

    async def get_for_update(self, animal_id: UUID) -> Animal | None:
        """Like get_by_id, but locks the row until the transaction ends (ADR 0014)."""
        result = await self._session.execute(
            _SELECT_BY_ID_FOR_UPDATE, {"id": animal_id}
        )
        row = result.first()
        return _from_row(row) if row is not None else None

    async def list_by_owner(self, owner_id: UUID) -> list[Animal]:
        """All animals owned by this user, published and unpublished, newest first."""
        result = await self._session.execute(_SELECT_BY_OWNER, {"owner_id": owner_id})
        return [_from_row(row) for row in result]

    async def list_all(self) -> list[Animal]:
        """Every published animal of every owner, newest first: the public catalog."""
        result = await self._session.execute(_SELECT_ALL_PUBLISHED)
        return [_from_row(row) for row in result]
