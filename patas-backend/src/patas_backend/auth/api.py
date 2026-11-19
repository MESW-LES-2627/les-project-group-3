from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, model_validator

from patas_backend.auth.dependencies import get_current_user
from patas_backend.models.user import InvalidUser, User, UsernameTaken
from patas_backend.services.users import UserService

router = APIRouter()


class UpdateUserRequest(BaseModel):
    name: str | None = None
    username: str | None = None

    @model_validator(mode="after")
    def _changes_something(self) -> "UpdateUserRequest":
        if self.name is None and self.username is None:
            raise ValueError("give a name, a username or both")
        return self


class UserResponse(BaseModel):
    id: UUID
    name: str
    email: str
    username: str
    is_platform_admin: bool

    @classmethod
    def from_domain(cls, user: User) -> "UserResponse":
        return cls(
            id=user.id,
            name=user.name,
            email=user.email,
            username=user.username,
            is_platform_admin=user.is_platform_admin,
        )


class UsernameAvailabilityResponse(BaseModel):
    username: str
    available: bool


def get_user_service(request: Request) -> UserService:
    return UserService(request.app.state.session_factory)


@router.get("/me", response_model=UserResponse)
async def me(user: Annotated[User, Depends(get_current_user)]) -> UserResponse:
    return UserResponse.from_domain(user)


@router.patch("/me", response_model=UserResponse)
async def update_me(
    body: UpdateUserRequest,
    user: Annotated[User, Depends(get_current_user)],
    service: Annotated[UserService, Depends(get_user_service)],
) -> UserResponse:
    try:
        updated = await service.update_profile(
            user, name=body.name, username=body.username
        )
    except InvalidUser as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(error)
        ) from error
    except UsernameTaken as error:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            {"code": "username_taken", "message": "That username is already taken"},
        ) from error
    return UserResponse.from_domain(updated)


# Public: the register page asks before the account exists. It says no more than
# trying to sign up with the username would (ADR 0024, decision 5).
@router.get("/usernames/{username}", response_model=UsernameAvailabilityResponse)
async def username_availability(
    username: str, service: Annotated[UserService, Depends(get_user_service)]
) -> UsernameAvailabilityResponse:
    try:
        available = await service.is_username_available(username)
    except InvalidUser as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(error)
        ) from error
    return UsernameAvailabilityResponse(username=username.strip(), available=available)
