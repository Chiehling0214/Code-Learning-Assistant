"""Current-user endpoints (read + account deletion).

Returns the persisted user for the authenticated identity, provisioning it on
first sign-in (see ``get_current_db_user`` in ``app/api/deps.py``).
"""

from fastapi import APIRouter, status

from app.api.deps import CurrentDbUser, SettingsDep, TrackServiceDep, UserServiceDep
from app.core.security import delete_firebase_user
from app.schemas.user import CurrentUserResponse

router = APIRouter(tags=["users"])


@router.get("/me", response_model=CurrentUserResponse)
def read_me(current_user: CurrentDbUser, tracks: TrackServiceDep) -> CurrentUserResponse:
    return CurrentUserResponse(
        id=current_user.id,
        uid=current_user.firebase_uid,
        email=current_user.email,
        display_name=current_user.display_name,
        is_admin=current_user.is_admin,
        onboarded=tracks.has_tracks(current_user.id),
    )


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_me(
    current_user: CurrentDbUser, users: UserServiceDep, settings: SettingsDep
) -> None:
    """Delete the account and all learner data (tracks, courses, submissions,
    attempts, reviews, chats — cascaded by the database). Also removes the
    Firebase Auth user, best-effort."""
    users.delete_account(current_user.id)
    delete_firebase_user(current_user.firebase_uid, settings)
