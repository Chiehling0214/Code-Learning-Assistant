"""Current-user endpoint.

Returns the persisted user for the authenticated identity, provisioning it on
first sign-in (see ``get_current_db_user`` in ``app/api/deps.py``).
"""

from fastapi import APIRouter

from app.api.deps import CurrentDbUser
from app.schemas.user import CurrentUserResponse

router = APIRouter(tags=["users"])


@router.get("/me", response_model=CurrentUserResponse)
def read_me(current_user: CurrentDbUser) -> CurrentUserResponse:
    return CurrentUserResponse(
        id=current_user.id,
        uid=current_user.firebase_uid,
        email=current_user.email,
        display_name=current_user.display_name,
        is_admin=current_user.is_admin,
    )
