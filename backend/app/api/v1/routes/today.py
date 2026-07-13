"""Personalized daily plan endpoint."""

from fastapi import APIRouter

from app.api.deps import (
    CurrentDbUser,
    RecommendationServiceDep,
    ReviewServiceDep,
    UserServiceDep,
)
from app.schemas.today import TodayItem, TodayResponse

router = APIRouter(tags=["today"])


@router.get("/today", response_model=TodayResponse)
def get_today(
    current_user: CurrentDbUser,
    service: RecommendationServiceDep,
    users: UserServiceDep,
    reviews: ReviewServiceDep,
) -> TodayResponse:
    level = users.get_profile(current_user.id).skill_level
    items = service.get_today(user_id=current_user.id, skill_level=level)
    return TodayResponse(
        items=[TodayItem(**item) for item in items],
        reviews_due=reviews.due_count(current_user.id),
    )
