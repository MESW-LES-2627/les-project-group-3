import uuid
from typing import Annotated
from uuid import UUID

import boto3
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Request,
    Response,
    status,
)
from pydantic import BaseModel, ConfigDict, Field

from patas_backend.auth.dependencies import get_current_user
from patas_backend.config import Settings
from patas_backend.models.animal import (
    AdoptionStatus,
    Animal,
    AnimalCompatibility,
    AnimalMatchProfile,
    AnimalSex,
    AnimalSize,
    AnimalUnauthorized,
    CatalogFilter,
    CatalogPage,
    District,
    FirstTimeOwnerSuitability,
    InvalidAnimal,
    InvalidAnimalTransition,
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

ALLOWED_IMAGE_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}


# Placeholder until the team agrees on the limit.
MAX_PHOTO_BYTES = 5 * 1024 * 1024
UPLOAD_URL_LIFETIME_SECONDS = 300


class PresignedUrlRequest(BaseModel):
    content_type: str = "image/jpeg"
    # Signed into the URL, so the storage refuses a file of any other size.
    size: int = Field(gt=0, le=MAX_PHOTO_BYTES)


class PresignedUrlResponse(BaseModel):
    upload_url: str
    public_url: str


class PublishAnimalRequest(BaseModel):
    # Types only. The business rules (non-blank name, age >= 0) live in the domain.
    name: str
    species: Species
    # The column's limit: a larger age would be a database error (500), not a 422.
    age_in_months: Annotated[int, Field(le=2_147_483_647)] | None = None
    sex: AnimalSex | None = None
    is_neutered: NeuteredStatus | None = None
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
    photo_urls: list[str] = Field(default_factory=list)


class EditAnimalRequest(PublishAnimalRequest):
    # Unknown fields are a 422, not ignored: with full replacement a misspelt field
    # would clear the real one, and owner_id or adoption_status must not be sent.
    model_config = ConfigDict(extra="forbid")


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
    owner_username: str
    name: str
    species: Species
    age_in_months: int | None
    adoption_status: AdoptionStatus
    sex: AnimalSex | None
    is_neutered: NeuteredStatus | None
    district: District | None
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
    photo_urls: list[str]
    match_profile: AnimalMatchProfileResponse

    @classmethod
    def from_domain(cls, animal: Animal) -> "AnimalResponse":
        return cls(
            id=animal.id,
            owner_id=animal.owner_id,
            owner_name=animal.owner_name,
            owner_username=animal.owner_username,
            name=animal.name,
            species=animal.species,
            age_in_months=animal.age_in_months,
            adoption_status=animal.adoption_status,
            sex=animal.sex,
            is_neutered=animal.is_neutered,
            district=animal.district,
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
            photo_urls=animal.photo_urls,
            match_profile=AnimalMatchProfileResponse.from_domain(
                animal.match_profile()
            ),
        )


def get_animal_service(request: Request) -> AnimalService:
    return AnimalService(
        request.app.state.session_factory, request.app.state.dispatcher
    )


def get_settings(request: Request) -> Settings:
    settings: Settings = request.app.state.settings
    return settings


def check_own_uploads(photo_urls: list[str], owner: User, settings: Settings) -> None:
    """Only photos the owner uploaded through Patas: no third-party URLs."""
    prefix = f"{settings.public_upload_url.rstrip('/')}/animals/{owner.id}/"
    if any(not url.startswith(prefix) for url in photo_urls):
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "Photos must be uploaded through Patas",
        )


@router.post("/animals/presigned-url", response_model=PresignedUrlResponse)
async def create_presigned_url(
    body: PresignedUrlRequest,
    owner: Annotated[User, Depends(get_current_user)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> PresignedUrlResponse:
    """A short-lived URL the browser uses to upload a photo straight to R2."""
    if not settings.uploads_configured:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE, "Photo uploads are not configured"
        )
    extension = ALLOWED_IMAGE_TYPES.get(body.content_type)
    if extension is None:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "Unsupported image type. Use JPEG, PNG, or WebP.",
        )

    file_name = f"animals/{owner.id}/{uuid.uuid4()}{extension}"

    s3_client = boto3.client(
        "s3",
        endpoint_url=settings.aws_s3_endpoint_url,
        region_name="auto",
        # Passed explicitly so credentials loaded from .env work too (boto3 alone
        # only reads the process environment).
        aws_access_key_id=settings.aws_access_key_id or None,
        aws_secret_access_key=settings.aws_secret_access_key or None,
    )

    upload_url = s3_client.generate_presigned_url(
        "put_object",
        Params={
            "Bucket": settings.aws_storage_bucket_name,
            "Key": file_name,
            "ContentType": body.content_type,
            "ContentLength": body.size,
        },
        ExpiresIn=UPLOAD_URL_LIFETIME_SECONDS,
    )

    return PresignedUrlResponse(
        upload_url=upload_url,
        public_url=f"{settings.public_upload_url.rstrip('/')}/{file_name}",
    )


@router.get("/animals", response_model=list[AnimalResponse])
async def list_animals(
    response: Response,
    service: Annotated[AnimalService, Depends(get_animal_service)],
    species: Species | None = None,
    size: AnimalSize | None = None,
    district: District | None = None,
    age_group: LifeStage | None = None,
    page: Annotated[int, Query(ge=1)] = 1,
) -> list[AnimalResponse]:
    """The public catalog: one page of the published animals that match the
    filters. X-Total-Count says how many match in all (ADR 0025)."""
    catalog_filter = CatalogFilter(
        species=species, size=size, district=district, age_group=age_group
    )
    animals, total = await service.list_catalog(catalog_filter, CatalogPage(page))
    response.headers["X-Total-Count"] = str(total)
    return [AnimalResponse.from_domain(a) for a in animals]


@router.get("/me/animals", response_model=list[AnimalResponse])
async def list_my_animals(
    owner: Annotated[User, Depends(get_current_user)],
    service: Annotated[AnimalService, Depends(get_animal_service)],
) -> list[AnimalResponse]:
    """The logged-in user's animals, including unpublished ones."""
    return [AnimalResponse.from_domain(a) for a in await service.list_by_owner(owner)]


@router.get("/me/animals/{animal_id}", response_model=AnimalResponse)
async def get_my_animal(
    animal_id: UUID,
    owner: Annotated[User, Depends(get_current_user)],
    service: Annotated[AnimalService, Depends(get_animal_service)],
) -> AnimalResponse:
    """One of the user's animals, unpublished included: 404 otherwise."""
    animal = await service.get_owned(owner, animal_id)
    if animal is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Animal not found")
    return AnimalResponse.from_domain(animal)


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
    except InvalidAnimalTransition as error:
        raise HTTPException(status.HTTP_409_CONFLICT, str(error)) from error

    if animal is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Animal not found")
    return AnimalResponse.from_domain(animal)


@router.post("/animals/{animal_id}/republish", response_model=AnimalResponse)
async def republish_animal(
    animal_id: UUID,
    owner: Annotated[User, Depends(get_current_user)],
    service: Annotated[AnimalService, Depends(get_animal_service)],
) -> AnimalResponse:
    try:
        animal = await service.republish(owner, animal_id)
    except AnimalUnauthorized as error:
        raise HTTPException(status.HTTP_403_FORBIDDEN, str(error)) from error
    except InvalidAnimalTransition as error:
        raise HTTPException(status.HTTP_409_CONFLICT, str(error)) from error

    if animal is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Animal not found")
    return AnimalResponse.from_domain(animal)


@router.put("/animals/{animal_id}", response_model=AnimalResponse)
async def edit_animal(
    animal_id: UUID,
    body: EditAnimalRequest,
    owner: Annotated[User, Depends(get_current_user)],
    service: Annotated[AnimalService, Depends(get_animal_service)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> AnimalResponse:
    """The owner replaces the description: 403 if not the owner, 404 if not found."""
    check_own_uploads(body.photo_urls, owner, settings)
    try:
        animal = await service.edit(
            owner,
            animal_id,
            name=body.name,
            species=body.species,
            age_in_months=body.age_in_months,
            sex=body.sex,
            is_neutered=body.is_neutered,
            district=body.district,
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
            photo_urls=body.photo_urls,
        )
    except AnimalUnauthorized as error:
        raise HTTPException(status.HTTP_403_FORBIDDEN, str(error)) from error
    except InvalidAnimal as error:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, str(error)
        ) from error

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
    settings: Annotated[Settings, Depends(get_settings)],
) -> AnimalResponse:
    check_own_uploads(body.photo_urls, owner, settings)
    try:
        animal = await service.publish(
            owner,
            name=body.name,
            species=body.species,
            age_in_months=body.age_in_months,
            sex=body.sex,
            is_neutered=body.is_neutered,
            district=body.district,
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
            photo_urls=body.photo_urls,
        )
    except InvalidAnimal as error:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, str(error)
        ) from error
    return AnimalResponse.from_domain(animal)
