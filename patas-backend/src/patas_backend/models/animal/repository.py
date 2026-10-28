from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from patas_backend.models.animal.animal import Animal
from patas_backend.models.animal.enums import (
    AdoptionStatus,
    AnimalCompatibility,
    AnimalSex,
    AnimalSize,
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
            special_care_notes, other_details
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
        :other_details
    )
    """
)
# created_at ties only inside one transaction (now() is fixed per transaction), so
# id keeps the order deterministic there.
_SELECT_ALL = text(
    """
    SELECT
        id, owner_id, name, species, age_in_months, adoption_status, sex,
        is_neutered, postal_code, size, activity_level, space_requirement,
        shedding, grooming_needs, behaves_well_with_children,
        behaves_well_with_dogs, behaves_well_with_cats,
        behaves_well_with_other_animals, training_needs,
        tolerance_for_time_alone, noise_level, suitable_for_first_time_owners,
        special_care_notes, other_details
    FROM patas.animals
    ORDER BY created_at DESC, id
    """
)


class AnimalRepository:
    """Persistence for Animal. The caller owns the transaction (this never commits)."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, animal: Animal) -> None:
        await self._session.execute(
            _INSERT,
            {
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
                    animal.activity_level.value
                    if animal.activity_level is not None
                    else None
                ),
                "space_requirement": (
                    animal.space_requirement.value
                    if animal.space_requirement is not None
                    else None
                ),
                "shedding": animal.shedding.value
                if animal.shedding is not None
                else None,
                "grooming_needs": (
                    animal.grooming_needs.value
                    if animal.grooming_needs is not None
                    else None
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
                    animal.training_needs.value
                    if animal.training_needs is not None
                    else None
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
            },
        )

    async def list_all(self) -> list[Animal]:
        """Every animal of every owner, newest first: the public catalog."""
        result = await self._session.execute(_SELECT_ALL)
        return [
            Animal(
                id=row.id,
                owner_id=row.owner_id,
                name=row.name,
                species=Species(row.species),
                age_in_months=row.age_in_months,
                adoption_status=AdoptionStatus(row.adoption_status),
                sex=AnimalSex(row.sex) if row.sex is not None else None,
                is_neutered=(
                    NeuteredStatus(row.is_neutered)
                    if row.is_neutered is not None
                    else None
                ),
                postal_code=row.postal_code,
                size=AnimalSize(row.size) if row.size is not None else None,
                activity_level=(
                    EnergyLevel(row.activity_level)
                    if row.activity_level is not None
                    else None
                ),
                space_requirement=(
                    AnimalSize(row.space_requirement)
                    if row.space_requirement is not None
                    else None
                ),
                shedding=EnergyLevel(row.shedding)
                if row.shedding is not None
                else None,
                grooming_needs=(
                    EnergyLevel(row.grooming_needs)
                    if row.grooming_needs is not None
                    else None
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
                    EnergyLevel(row.training_needs)
                    if row.training_needs is not None
                    else None
                ),
                tolerance_for_time_alone=(
                    EnergyLevel(row.tolerance_for_time_alone)
                    if row.tolerance_for_time_alone is not None
                    else None
                ),
                noise_level=(
                    EnergyLevel(row.noise_level)
                    if row.noise_level is not None
                    else None
                ),
                suitable_for_first_time_owners=(
                    FirstTimeOwnerSuitability(row.suitable_for_first_time_owners)
                    if row.suitable_for_first_time_owners is not None
                    else None
                ),
                special_care_notes=row.special_care_notes,
                other_details=row.other_details,
            )
            for row in result
        ]
