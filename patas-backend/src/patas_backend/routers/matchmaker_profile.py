from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, StrictBool

from patas_backend.auth.dependencies import get_current_user
from patas_backend.models.matching import EnergyLevel, ExperienceLevel
from patas_backend.models.matchmaker_profile import (
    HousingType,
    MatchmakerProfile,
    TimeAway,
)
from patas_backend.models.user import User
from patas_backend.services.matchmaker_profile import MatchmakerProfileService

router = APIRouter()


class SaveMatchmakerProfileRequest(BaseModel):
    # Types only, and every answer is required. StrictBool: only a real true or
    # false, never the text "yes" or the number 1.
    housing: HousingType
    activity: EnergyLevel
    time_away: TimeAway
    experience: ExperienceLevel
    has_children: StrictBool
    has_dogs: StrictBool
    has_cats: StrictBool


class MatchmakerProfileResponse(BaseModel):
    housing: HousingType
    activity: EnergyLevel
    time_away: TimeAway
    experience: ExperienceLevel
    has_children: bool
    has_dogs: bool
    has_cats: bool

    @classmethod
    def from_domain(cls, profile: MatchmakerProfile) -> "MatchmakerProfileResponse":
        return cls(
            housing=profile.housing,
            activity=profile.activity,
            time_away=profile.time_away,
            experience=profile.experience,
            has_children=profile.has_children,
            has_dogs=profile.has_dogs,
            has_cats=profile.has_cats,
        )


def get_matchmaker_profile_service(request: Request) -> MatchmakerProfileService:
    return MatchmakerProfileService(request.app.state.session_factory)


@router.get("/me/matchmaker-profile", response_model=MatchmakerProfileResponse)
async def get_matchmaker_profile(
    user: Annotated[User, Depends(get_current_user)],
    service: Annotated[
        MatchmakerProfileService, Depends(get_matchmaker_profile_service)
    ],
) -> MatchmakerProfileResponse:
    """Always the caller's own profile: the URL carries no user id."""
    profile = await service.get(user)
    if profile is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No Matchmaker profile yet")
    return MatchmakerProfileResponse.from_domain(profile)


@router.put("/me/matchmaker-profile", response_model=MatchmakerProfileResponse)
async def save_matchmaker_profile(
    body: SaveMatchmakerProfileRequest,
    user: Annotated[User, Depends(get_current_user)],
    service: Annotated[
        MatchmakerProfileService, Depends(get_matchmaker_profile_service)
    ],
) -> MatchmakerProfileResponse:
    profile = await service.save(
        user,
        housing=body.housing,
        activity=body.activity,
        time_away=body.time_away,
        experience=body.experience,
        has_children=body.has_children,
        has_dogs=body.has_dogs,
        has_cats=body.has_cats,
    )
    return MatchmakerProfileResponse.from_domain(profile)
