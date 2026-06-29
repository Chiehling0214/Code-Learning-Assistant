"""Current-user endpoint.

In Sprint 0 this returns the authenticated identity straight from the (stubbed)
token verifier. Sprint 1 will resolve and enrich it from the database.
"""

from fastapi import APIRouter

from app.api.deps import CurrentUser
from app.schemas.user import CurrentUserResponse

router = APIRouter(tags=["users"])


@router.get("/me", response_model=CurrentUserResponse)
def read_me(current_user: CurrentUser) -> CurrentUserResponse:
    return CurrentUserResponse(
        uid=current_user.uid,
        email=current_user.email,
        is_admin=current_user.is_admin,
    )
