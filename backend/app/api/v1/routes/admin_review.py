"""Admin AI-content review console (Sprint 13).

Replaces the retired content-CRUD admin surface. Every endpoint requires an admin
user via ``require_admin`` (non-admins get 403).
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import AdminReviewServiceDep, require_admin
from app.schemas.admin_review import ReviewItemResponse, UsageResponse

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])


def _item(item) -> ReviewItemResponse:  # noqa: ANN001 - service dataclass
    return ReviewItemResponse(
        lesson_id=item.lesson_id,
        title=item.title,
        course_id=item.course_id,
        course_title=item.course_title,
        source=item.source,
        review_status=item.review_status,
        exercise_count=item.exercise_count,
        quiz_count=item.quiz_count,
    )


@router.get("/content", response_model=list[ReviewItemResponse])
def list_content(
    service: AdminReviewServiceDep, source: str = "ai"
) -> list[ReviewItemResponse]:
    return [_item(i) for i in service.list_content(source=source)]


@router.post("/content/lessons/{lesson_id}/hide", response_model=ReviewItemResponse)
def hide_lesson(lesson_id: uuid.UUID, service: AdminReviewServiceDep) -> ReviewItemResponse:
    try:
        return _item(service.set_status(lesson_id=lesson_id, review_status="hidden"))
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/content/lessons/{lesson_id}/approve", response_model=ReviewItemResponse)
def approve_lesson(lesson_id: uuid.UUID, service: AdminReviewServiceDep) -> ReviewItemResponse:
    try:
        return _item(service.set_status(lesson_id=lesson_id, review_status="approved"))
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/usage", response_model=UsageResponse)
def get_usage(service: AdminReviewServiceDep) -> UsageResponse:
    return UsageResponse(**service.usage())
