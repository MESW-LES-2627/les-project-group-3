from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, ConfigDict

from patas_backend.auth.dependencies import get_current_user
from patas_backend.models.adoption import (
    AdoptionApplication,
    AlreadyRequested,
    ApplicationStatus,
    InvalidApplication,
    InvalidTransition,
    MatchmakerProfileRequired,
    OwnerCannotApply,
    SentRequest,
)
from patas_backend.models.animal import AnimalNotAvailable
from patas_backend.models.user import User
from patas_backend.services.adoption import AdoptionService

router = APIRouter()


class RequestToAdoptBody(BaseModel):
    # Types only. The note rules (not blank, at most 1000 characters) live in the
    # domain. Unknown fields are a 422: the owner and the profile are never sent.
    model_config = ConfigDict(extra="forbid")

    note: str


class ApplicationResponse(BaseModel):
    # What the applicant sent. The copy of their profile is for the owner and is not
    # part of this response.
    id: UUID
    animal_id: UUID
    status: ApplicationStatus
    note: str
    created_at: datetime | None

    @classmethod
    def from_domain(cls, application: AdoptionApplication) -> "ApplicationResponse":
        return cls(
            id=application.id,
            animal_id=application.animal_id,
            status=application.status,
            note=application.applicant_note,
            created_at=application.created_at,
        )


class SentRequestResponse(BaseModel):
    # One row of the applicant's list. The owner's reply is shown; the copy of the
    # applicant's own profile is not.
    id: UUID
    animal_id: UUID
    animal_name: str
    status: ApplicationStatus
    note: str
    owner_note: str | None
    created_at: datetime

    @classmethod
    def from_read_model(cls, request: SentRequest) -> "SentRequestResponse":
        return cls(
            id=request.id,
            animal_id=request.animal_id,
            animal_name=request.animal_name,
            status=request.status,
            note=request.applicant_note,
            owner_note=request.owner_note,
            created_at=request.created_at,
        )


def get_adoption_service(request: Request) -> AdoptionService:
    return AdoptionService(
        request.app.state.session_factory, request.app.state.dispatcher
    )


def _conflict(code: str, error: Exception) -> HTTPException:
    # One 409 with several causes: the code lets the page tell them apart.
    return HTTPException(
        status.HTTP_409_CONFLICT, {"code": code, "message": str(error)}
    )


@router.post(
    "/animals/{animal_id}/applications",
    response_model=ApplicationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def request_to_adopt(
    animal_id: UUID,
    body: RequestToAdoptBody,
    applicant: Annotated[User, Depends(get_current_user)],
    service: Annotated[AdoptionService, Depends(get_adoption_service)],
) -> ApplicationResponse:
    try:
        application = await service.request_to_adopt(applicant, animal_id, body.note)
    # OwnerCannotApply is an InvalidApplication, so it has to be caught first.
    except OwnerCannotApply as error:
        raise HTTPException(status.HTTP_403_FORBIDDEN, str(error)) from error
    except InvalidApplication as error:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, str(error)
        ) from error
    except AnimalNotAvailable as error:
        raise _conflict("animal_not_available", error) from error
    except AlreadyRequested as error:
        raise _conflict("already_requested", error) from error
    except MatchmakerProfileRequired as error:
        raise _conflict("matchmaker_profile_required", error) from error

    if application is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Animal not found")
    return ApplicationResponse.from_domain(application)


@router.get("/animals/{animal_id}/my-application", response_model=ApplicationResponse)
async def get_my_application(
    animal_id: UUID,
    applicant: Annotated[User, Depends(get_current_user)],
    service: Annotated[AdoptionService, Depends(get_adoption_service)],
) -> ApplicationResponse:
    """The caller's open or accepted request for this animal: 404 if there is none."""
    application = await service.get_active_request(applicant, animal_id)
    if application is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No active request")
    return ApplicationResponse.from_domain(application)


@router.get("/me/applications", response_model=list[SentRequestResponse])
async def list_my_applications(
    applicant: Annotated[User, Depends(get_current_user)],
    service: Annotated[AdoptionService, Depends(get_adoption_service)],
) -> list[SentRequestResponse]:
    """Every request the caller sent, newest first. Never anyone else's."""
    requests = await service.list_my_requests(applicant)
    return [SentRequestResponse.from_read_model(request) for request in requests]


@router.post(
    "/applications/{application_id}/withdraw", response_model=ApplicationResponse
)
async def withdraw_application(
    application_id: UUID,
    applicant: Annotated[User, Depends(get_current_user)],
    service: Annotated[AdoptionService, Depends(get_adoption_service)],
) -> ApplicationResponse:
    try:
        application = await service.withdraw(applicant, application_id)
    except InvalidTransition as error:
        raise _conflict("invalid_transition", error) from error
    if application is None:
        # Also for someone else's request: to them it does not exist.
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Request not found")
    return ApplicationResponse.from_domain(application)
