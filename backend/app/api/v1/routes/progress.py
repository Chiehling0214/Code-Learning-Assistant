"""Progress analytics + lesson mark-complete endpoints."""

import uuid

from fastapi import APIRouter, HTTPException, status

from app.api.deps import CurrentDbUser, ProgressServiceDep
from app.schemas.progress import CourseProgress, MarkCompleteResponse, ProgressResponse

router = APIRouter(tags=["progress"])


@router.get("/progress", response_model=ProgressResponse)
def get_progress(
    current_user: CurrentDbUser, service: ProgressServiceDep
) -> ProgressResponse:
    data = service.get_progress(current_user.id)
    return ProgressResponse(
        courses=[CourseProgress(**c) for c in data["courses"]],
        total=data["total"],
        completed=data["completed"],
        percent=data["percent"],
        streak=data["streak"],
    )


@router.post("/lessons/{lesson_id}/complete", response_model=MarkCompleteResponse)
def mark_lesson_complete(
    lesson_id: uuid.UUID,
    current_user: CurrentDbUser,
    service: ProgressServiceDep,
) -> MarkCompleteResponse:
    try:
        service.mark_lesson_complete(user_id=current_user.id, lesson_id=lesson_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return MarkCompleteResponse()
