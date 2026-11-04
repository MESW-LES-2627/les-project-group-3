from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel

from patas_backend.auth.dependencies import get_current_user
from patas_backend.models.compatibility import (
    CompatibilityMode,
    CompatibilityResult,
    ReasonKind,
)
from patas_backend.models.user import User
from patas_backend.services.compatibility import (
    AnimalNotFound,
    CompatibilityService,
    NoMatchmakerProfile,
    OwnAnimal,
)

router = APIRouter()


class ReasonResponse(BaseModel):
    text: str
    kind: ReasonKind


class CompatibilityResponse(BaseModel):
    mode: CompatibilityMode
    score: int
    is_compatible: bool
    reasons: list[ReasonResponse]

    @classmethod
    def from_domain(
        cls, result: CompatibilityResult, mode: CompatibilityMode
    ) -> "CompatibilityResponse":
        return cls(
            mode=mode,
            score=result.score,
            is_compatible=result.is_compatible,
            reasons=[ReasonResponse(text=r.text, kind=r.kind) for r in result.reasons],
        )


def get_compatibility_service(request: Request) -> CompatibilityService:
    return CompatibilityService(request.app.state.session_factory)


@router.get("/animals/{animal_id}/compatibility", response_model=CompatibilityResponse)
async def get_animal_compatibility(
    animal_id: UUID,
    user: Annotated[User, Depends(get_current_user)],
    service: Annotated[CompatibilityService, Depends(get_compatibility_service)],
    mode: CompatibilityMode = CompatibilityMode.LOOSE,
) -> CompatibilityResponse:
    """How well this animal fits the caller's home. Nothing is stored."""
    try:
        result = await service.assess(user, animal_id, mode)
    except AnimalNotFound as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Animal not found") from error
    except OwnAnimal as error:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, str(error)
        ) from error
    except NoMatchmakerProfile as error:
        raise HTTPException(status.HTTP_409_CONFLICT, str(error)) from error
    return CompatibilityResponse.from_domain(result, mode)
