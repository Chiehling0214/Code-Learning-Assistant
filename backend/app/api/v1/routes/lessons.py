"""Public read endpoint for a single lesson."""

import uuid

from fastapi import APIRouter, HTTPException, status

from app.api.deps import ContentServiceDep, CurrentDbUser, LessonAdjustmentServiceDep
from app.application.ports.ai_provider import AIProviderError
from app.application.services.ai_usage import RateLimitError
from app.application.services.entitlement_service import UpgradeRequiredError
from app.application.services.lesson_adjustment_service import StaleLessonAdjustmentError
from app.schemas.content import LessonResponse
from app.schemas.lesson_adjustments import (
    LessonAdjustmentCreate,
    LessonAdjustmentPreviewResponse,
)

router = APIRouter(tags=["content"])


def _lesson_response(lesson) -> LessonResponse:  # noqa: ANN001
    return LessonResponse(
        id=lesson.id,
        course_id=lesson.course_id,
        title=lesson.title,
        slug=lesson.slug,
        order_index=lesson.order_index,
        content=lesson.content,
    )


@router.get("/lessons/{lesson_id}", response_model=LessonResponse)
def get_lesson(lesson_id: uuid.UUID, service: ContentServiceDep) -> LessonResponse:
    try:
        lesson = service.get_lesson(lesson_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return _lesson_response(lesson)


@router.post(
    "/lessons/{lesson_id}/adjustments/preview",
    response_model=LessonAdjustmentPreviewResponse,
)
def preview_lesson_adjustment(
    lesson_id: uuid.UUID,
    body: LessonAdjustmentCreate,
    current_user: CurrentDbUser,
    service: LessonAdjustmentServiceDep,
) -> LessonAdjustmentPreviewResponse:
    try:
        preview = service.preview(
            user_id=current_user.id,
            lesson_id=lesson_id,
            preset=body.preset,
            instructions=body.instructions,
        )
        return LessonAdjustmentPreviewResponse(
            adjustment_id=preview.adjustment_id,
            lesson_id=preview.lesson_id,
            title=preview.title,
            content=preview.content,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except UpgradeRequiredError as exc:
        raise HTTPException(status_code=402, detail=str(exc)) from exc
    except RateLimitError as exc:
        raise HTTPException(status_code=429, detail=str(exc)) from exc
    except AIProviderError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post(
    "/lessons/{lesson_id}/adjustments/{adjustment_id}/apply",
    response_model=LessonResponse,
)
def apply_lesson_adjustment(
    lesson_id: uuid.UUID,
    adjustment_id: uuid.UUID,
    current_user: CurrentDbUser,
    service: LessonAdjustmentServiceDep,
) -> LessonResponse:
    try:
        return _lesson_response(
            service.apply(
                user_id=current_user.id,
                lesson_id=lesson_id,
                adjustment_id=adjustment_id,
            )
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except StaleLessonAdjustmentError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
