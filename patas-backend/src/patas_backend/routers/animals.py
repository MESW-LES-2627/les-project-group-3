from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel

from patas_backend.auth.dependencies import get_current_user
from patas_backend.models.animal import (
    AdoptionStatus,
    Animal,
    AnimalCompatibility,
    AnimalSex,
    AnimalSize,
    FirstTimeOwnerSuitability,
    InvalidAnimal,
    NeuteredStatus,
    Species,
)
from patas_backend.models.matching.scales import EnergyLevel
from patas_backend.models.user import User
from patas_backend.services.animals import AnimalService

router = APIRouter()


class PublishAnimalRequest(BaseModel):
    # Types only. The business rules (non-blank name, age >= 0) live in the domain.
    name: str
    species: Species
    age_in_months: int | None = None
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


class AnimalResponse(BaseModel):
    id: UUID
    owner_id: UUID
    name: str
    species: Species
    age_in_months: int | None
    adoption_status: AdoptionStatus
    sex: AnimalSex | None
    is_neutered: NeuteredStatus | None
    postal_code: str | None
    size: AnimalSize | None
    activity_level: EnergyLevel | None
    space_requirement: AnimalSize | None
    shedding: EnergyLevel | None
    grooming_needs: EnergyLevel | None
    behaves_well_with_children: AnimalCompatibility | None
    behaves_well_with_dogs: AnimalCompatibility | None
    behaves_well_with_cats: AnimalCompatibility | None
    behaves_well_with_other_animals: AnimalCompatibility | None
    training_needs: EnergyLevel | None
    tolerance_for_time_alone: EnergyLevel | None
    noise_level: EnergyLevel | None
    suitable_for_first_time_owners: FirstTimeOwnerSuitability | None
    special_care_notes: str | None
    other_details: str | None

    @classmethod
    def from_domain(cls, animal: Animal) -> "AnimalResponse":
        return cls(
            id=animal.id,
            owner_id=animal.owner_id,
            name=animal.name,
            species=animal.species,
            age_in_months=animal.age_in_months,
            adoption_status=animal.adoption_status,
            sex=animal.sex,
            is_neutered=animal.is_neutered,
            postal_code=animal.postal_code,
            size=animal.size,
            activity_level=animal.activity_level,
            space_requirement=animal.space_requirement,
            shedding=animal.shedding,
            grooming_needs=animal.grooming_needs,
            behaves_well_with_children=animal.behaves_well_with_children,
            behaves_well_with_dogs=animal.behaves_well_with_dogs,
            behaves_well_with_cats=animal.behaves_well_with_cats,
            behaves_well_with_other_animals=animal.behaves_well_with_other_animals,
            training_needs=animal.training_needs,
            tolerance_for_time_alone=animal.tolerance_for_time_alone,
            noise_level=animal.noise_level,
            suitable_for_first_time_owners=animal.suitable_for_first_time_owners,
            special_care_notes=animal.special_care_notes,
            other_details=animal.other_details,
        )


def get_animal_service(request: Request) -> AnimalService:
    return AnimalService(request.app.state.session_factory)


@router.get("/animals", response_model=list[AnimalResponse])
async def list_animals(
    service: Annotated[AnimalService, Depends(get_animal_service)],
) -> list[AnimalResponse]:
    """The public catalog: no authentication dependency (AC5)."""
    return [AnimalResponse.from_domain(a) for a in await service.list_catalog()]


@router.post(
    "/animals", status_code=status.HTTP_201_CREATED, response_model=AnimalResponse
)
async def publish_animal(
    body: PublishAnimalRequest,
    owner: Annotated[User, Depends(get_current_user)],
    service: Annotated[AnimalService, Depends(get_animal_service)],
) -> AnimalResponse:
    try:
        animal = await service.publish(
            owner,
            name=body.name,
            species=body.species,
            age_in_months=body.age_in_months,
            sex=body.sex,
            is_neutered=body.is_neutered,
            postal_code=body.postal_code,
            size=body.size,
            activity_level=body.activity_level,
            space_requirement=body.space_requirement,
            shedding=body.shedding,
            grooming_needs=body.grooming_needs,
            behaves_well_with_children=body.behaves_well_with_children,
            behaves_well_with_dogs=body.behaves_well_with_dogs,
            behaves_well_with_cats=body.behaves_well_with_cats,
            behaves_well_with_other_animals=body.behaves_well_with_other_animals,
            training_needs=body.training_needs,
            tolerance_for_time_alone=body.tolerance_for_time_alone,
            noise_level=body.noise_level,
            suitable_for_first_time_owners=body.suitable_for_first_time_owners,
            special_care_notes=body.special_care_notes,
            other_details=body.other_details,
        )
    except InvalidAnimal as error:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, str(error)
        ) from error
    return AnimalResponse.from_domain(animal)
