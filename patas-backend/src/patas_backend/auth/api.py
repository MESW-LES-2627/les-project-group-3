from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel

from patas_backend.auth.dependencies import get_current_user
from patas_backend.models.user import InvalidUser, User, UserRepository

router = APIRouter()


class UpdateUserRequest(BaseModel):
    name: str


class UserResponse(BaseModel):
    id: UUID
    name: str
    email: str
    is_platform_admin: bool


@router.get("/me", response_model=UserResponse)
async def me(user: Annotated[User, Depends(get_current_user)]) -> UserResponse:
    return UserResponse(
        id=user.id,
        name=user.name,
        email=user.email,
        is_platform_admin=user.is_platform_admin,
    )


@router.patch("/me", response_model=UserResponse)
async def update_me(
    body: UpdateUserRequest,
    user: Annotated[User, Depends(get_current_user)],
    request: Request,
) -> UserResponse:
    try:
        user.change_name(body.name)
    except InvalidUser as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(error)
        ) from error

    async with request.app.state.session_factory.begin() as session:
        updated = await UserRepository(session).update(user)

    return UserResponse(
        id=updated.id,
        name=updated.name,
        email=updated.email,
        is_platform_admin=updated.is_platform_admin,
    )
