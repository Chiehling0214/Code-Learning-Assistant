"""Public read endpoint for a single lesson."""

import uuid

from fastapi import APIRouter, HTTPException, status

from app.api.deps import ContentServiceDep
from app.schemas.content import LessonResponse

router = APIRouter(tags=["content"])


@router.get("/lessons/{lesson_id}", response_model=LessonResponse)
def get_lesson(lesson_id: uuid.UUID, service: ContentServiceDep) -> LessonResponse:
    try:
        lesson = service.get_lesson(lesson_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return LessonResponse(
        id=lesson.id,
        course_id=lesson.course_id,
        title=lesson.title,
        slug=lesson.slug,
        order_index=lesson.order_index,
        content=lesson.content,
    )
