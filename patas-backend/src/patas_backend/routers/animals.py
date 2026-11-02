from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel

from patas_backend.auth.dependencies import get_current_user
from patas_backend.models.animal import (
    AdoptionStatus,
    Animal,
    AnimalCompatibility,
    AnimalMatchProfile,
    AnimalSex,
    AnimalSize,
    AnimalUnauthorized,
    FirstTimeOwnerSuitability,
    InvalidAnimal,
    NeuteredStatus,
    Species,
)
from patas_backend.models.matching.scales import (
    EnergyLevel,
    ExperienceLevel,
    LifeStage,
    TimeAway,
)
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


class AnimalMatchProfileResponse(BaseModel):
    # Derived from the animal, never sent by a client: the request model has no
    # counterpart.
    activity: EnergyLevel | None
    max_time_alone: TimeAway | None
    experience_needed: ExperienceLevel | None
    space_needed: AnimalSize | None
    safe_with_children: bool | None
    safe_with_dogs: bool | None
    safe_with_cats: bool | None
    size: AnimalSize | None
    training_needs: EnergyLevel | None
    noise_level: EnergyLevel | None
    life_stage: LifeStage | None

    @classmethod
    def from_domain(cls, profile: AnimalMatchProfile) -> "AnimalMatchProfileResponse":
        return cls(
            activity=profile.activity,
            max_time_alone=profile.max_time_alone,
            experience_needed=profile.experience_needed,
            space_needed=profile.space_needed,
            safe_with_children=profile.safe_with_children,
            safe_with_dogs=profile.safe_with_dogs,
            safe_with_cats=profile.safe_with_cats,
            size=profile.size,
            training_needs=profile.training_needs,
            noise_level=profile.noise_level,
            life_stage=profile.life_stage,
        )


class AnimalResponse(BaseModel):
    id: UUID
    owner_id: UUID
    owner_name: str
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
    match_profile: AnimalMatchProfileResponse

    @classmethod
    def from_domain(cls, animal: Animal) -> "AnimalResponse":
        return cls(
            id=animal.id,
            owner_id=animal.owner_id,
            owner_name=animal.owner_name,
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
            match_profile=AnimalMatchProfileResponse.from_domain(
                animal.match_profile()
            ),
        )


def get_animal_service(request: Request) -> AnimalService:
    return AnimalService(request.app.state.session_factory)


@router.get("/animals", response_model=list[AnimalResponse])
async def list_animals(
    service: Annotated[AnimalService, Depends(get_animal_service)],
    species: Species | None = None,
) -> list[AnimalResponse]:
    """The public catalog: public, lists only published animals."""
    return [
        AnimalResponse.from_domain(a)
        for a in await service.list_catalog(species=species)
    ]


@router.get("/me/animals", response_model=list[AnimalResponse])
async def list_my_animals(
    owner: Annotated[User, Depends(get_current_user)],
    service: Annotated[AnimalService, Depends(get_animal_service)],
) -> list[AnimalResponse]:
    """The logged-in user's animals, including unpublished ones."""
    return [AnimalResponse.from_domain(a) for a in await service.list_by_owner(owner)]


@router.get("/animals/{animal_id}", response_model=AnimalResponse)
async def get_animal(
    animal_id: UUID,
    service: Annotated[AnimalService, Depends(get_animal_service)],
) -> AnimalResponse:
    """Public animal profile: 404 if not found or unpublished."""
    animal = await service.get(animal_id)
    if animal is None or not animal.is_published:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Animal not found")
    return AnimalResponse.from_domain(animal)


@router.post("/animals/{animal_id}/unpublish", response_model=AnimalResponse)
async def unpublish_animal(
    animal_id: UUID,
    owner: Annotated[User, Depends(get_current_user)],
    service: Annotated[AnimalService, Depends(get_animal_service)],
) -> AnimalResponse:
    try:
        animal = await service.unpublish(owner, animal_id)
    except AnimalUnauthorized as error:
        raise HTTPException(status.HTTP_403_FORBIDDEN, str(error)) from error

    if animal is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Animal not found")
    return AnimalResponse.from_domain(animal)


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
