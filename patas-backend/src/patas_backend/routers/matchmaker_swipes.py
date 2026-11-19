from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, ConfigDict

from patas_backend.auth.dependencies import get_current_user
from patas_backend.models.animal import Species
from patas_backend.models.compatibility import CompatibilityResult, ReasonKind
from patas_backend.models.matchmaker_swipe import (
    AlreadySwiped,
    SwipeAnimalNotAvailable,
    SwipeDisposition,
    SwipeNotSaved,
    SwipeOwnAnimal,
    SwipeProfileRequired,
)
from patas_backend.models.user import User
from patas_backend.services.matchmaker_swipes import (
    MatchmakerSwipeService,
    SwipeAnimal,
)

router = APIRouter()


class ReasonResponse(BaseModel):
    text: str
    kind: ReasonKind


class FitResponse(BaseModel):
    score: int
    is_compatible: bool
    reasons: list[ReasonResponse]

    @classmethod
    def from_domain(cls, result: CompatibilityResult) -> "FitResponse":
        return cls(
            score=result.score,
            is_compatible=result.is_compatible,
            reasons=[
                ReasonResponse(text=reason.text, kind=reason.kind)
                for reason in result.reasons
            ],
        )


class SwipeAnimalResponse(BaseModel):
    id: UUID
    owner_id: UUID
    owner_name: str
    name: str
    species: Species
    age_in_months: int | None
    district: str | None
    size: str | None
    adoption_status: str
    fit: FitResponse | None

    @classmethod
    def from_domain(cls, result: SwipeAnimal) -> "SwipeAnimalResponse":
        animal = result.animal
        return cls(
            id=animal.id,
            owner_id=animal.owner_id,
            owner_name=animal.owner_name,
            name=animal.name,
            species=animal.species,
            age_in_months=animal.age_in_months,
            district=animal.district.value if animal.district is not None else None,
            size=animal.size.value if animal.size is not None else None,
            adoption_status=animal.adoption_status.value,
            fit=FitResponse.from_domain(result.fit) if result.fit is not None else None,
        )


class RecordSwipeBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    animal_id: UUID
    disposition: SwipeDisposition


class RecordedSwipeResponse(BaseModel):
    animal_id: UUID
    disposition: SwipeDisposition


def get_matchmaker_swipe_service(request: Request) -> MatchmakerSwipeService:
    return MatchmakerSwipeService(request.app.state.session_factory)


@router.get("/me/matchmaker/swipes/feed", response_model=list[SwipeAnimalResponse])
async def get_swipe_feed(
    user: Annotated[User, Depends(get_current_user)],
    service: Annotated[MatchmakerSwipeService, Depends(get_matchmaker_swipe_service)],
) -> list[SwipeAnimalResponse]:
    try:
        animals = await service.list_feed(user)
    except SwipeProfileRequired as error:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            {"code": "matchmaker_profile_required", "message": str(error)},
        ) from error
    return [SwipeAnimalResponse.from_domain(animal) for animal in animals]


@router.get("/me/matchmaker/swipes/saved", response_model=list[SwipeAnimalResponse])
async def list_saved_animals(
    user: Annotated[User, Depends(get_current_user)],
    service: Annotated[MatchmakerSwipeService, Depends(get_matchmaker_swipe_service)],
) -> list[SwipeAnimalResponse]:
    animals = await service.list_saved(user)
    return [SwipeAnimalResponse.from_domain(animal) for animal in animals]


@router.post(
    "/me/matchmaker/swipes",
    response_model=RecordedSwipeResponse,
    status_code=status.HTTP_201_CREATED,
)
async def record_swipe(
    body: RecordSwipeBody,
    user: Annotated[User, Depends(get_current_user)],
    service: Annotated[MatchmakerSwipeService, Depends(get_matchmaker_swipe_service)],
) -> RecordedSwipeResponse:
    try:
        swipe = await service.record_swipe(user, body.animal_id, body.disposition)
    except SwipeOwnAnimal as error:
        raise HTTPException(status.HTTP_403_FORBIDDEN, str(error)) from error
    except SwipeProfileRequired as error:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            {"code": "matchmaker_profile_required", "message": str(error)},
        ) from error
    except SwipeAnimalNotAvailable as error:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            {"code": "animal_not_available", "message": str(error)},
        ) from error
    except AlreadySwiped as error:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            {"code": "already_swiped", "message": str(error)},
        ) from error
    return RecordedSwipeResponse(
        animal_id=swipe.animal_id, disposition=swipe.disposition
    )


@router.delete(
    "/me/matchmaker/swipes/{animal_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def remove_saved_animal(
    animal_id: UUID,
    user: Annotated[User, Depends(get_current_user)],
    service: Annotated[MatchmakerSwipeService, Depends(get_matchmaker_swipe_service)],
) -> None:
    try:
        await service.remove_saved(user, animal_id)
    except SwipeNotSaved as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(error)) from error
