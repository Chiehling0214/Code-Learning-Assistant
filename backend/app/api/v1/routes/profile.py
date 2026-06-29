"""Student profile endpoints: read and update the current user's profile."""

from fastapi import APIRouter

from app.api.deps import CurrentDbUser, UserServiceDep
from app.schemas.user import ProfileResponse, UpdateProfileRequest

router = APIRouter(tags=["users"])


@router.get("/me/profile", response_model=ProfileResponse)
def get_my_profile(current_user: CurrentDbUser, service: UserServiceDep) -> ProfileResponse:
    profile = service.get_profile(current_user.id)
    return ProfileResponse(
        display_name=current_user.display_name,
        email=current_user.email,
        skill_level=profile.skill_level,
        is_admin=current_user.is_admin,
    )


@router.put("/me/profile", response_model=ProfileResponse)
def update_my_profile(
    payload: UpdateProfileRequest,
    current_user: CurrentDbUser,
    service: UserServiceDep,
) -> ProfileResponse:
    user, profile = service.update_profile(
        current_user.id,
        display_name=payload.display_name,
        skill_level=payload.skill_level,
    )
    return ProfileResponse(
        display_name=user.display_name,
        email=user.email,
        skill_level=profile.skill_level,
        is_admin=user.is_admin,
    )
