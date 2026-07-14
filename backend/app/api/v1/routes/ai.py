"""AI endpoints: Teacher, Tutor (plain + SSE streaming), and admin generation.

All model access happens behind ``AIProvider`` (wired in ``deps.py``); this layer
only orchestrates and maps errors to HTTP status codes. The ``/stream`` variants
send Server-Sent Events: ``data: {"text": …}`` chunks, then ``data: [DONE]``
(mid-stream failures emit ``data: {"error": …}``).
"""

import json
from collections.abc import Iterator

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse

from app.api.deps import (
    AITeacherServiceDep,
    AITutorServiceDep,
    CurrentDbUser,
    EntitlementServiceDep,
    GenerateContentServiceDep,
    UserServiceDep,
    require_admin,
)
from app.application.ports.ai_provider import (
    AINotConfiguredError,
    AIProviderError,
    AIQuotaError,
)
from app.application.services.ai_usage import RateLimitError
from app.application.services.entitlement_service import UpgradeRequiredError
from app.schemas.ai import (
    AIAnswerResponse,
    GeneratedExerciseResponse,
    GeneratedLessonResponse,
    GenerateRequest,
    TeacherRequest,
    TutorRequest,
)

router = APIRouter(prefix="/ai", tags=["ai"])
admin_router = APIRouter(prefix="/admin/ai", tags=["admin"], dependencies=[Depends(require_admin)])


def _handle_ai_error(exc: Exception) -> HTTPException:
    """Map AI/usage failures to HTTP responses, degrading gracefully."""
    if isinstance(exc, LookupError):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    if isinstance(exc, UpgradeRequiredError):
        return HTTPException(status_code=status.HTTP_402_PAYMENT_REQUIRED, detail=str(exc))
    if isinstance(exc, RateLimitError):
        return HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(exc))
    if isinstance(exc, AINotConfiguredError):
        return HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI is not configured on this server.",
        )
    if isinstance(exc, AIQuotaError):
        return HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        )
    if isinstance(exc, AIProviderError):
        return HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail="The AI service failed; try again."
        )
    if isinstance(exc, ValueError):
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    raise exc


@router.post("/teacher", response_model=AIAnswerResponse)
def ask_teacher(
    payload: TeacherRequest,
    current_user: CurrentDbUser,
    service: AITeacherServiceDep,
    users: UserServiceDep,
) -> AIAnswerResponse:
    level = users.get_profile(current_user.id).skill_level
    try:
        result = service.teach(
            user_id=current_user.id,
            lesson_id=payload.lesson_id,
            topic=payload.topic,
            question=payload.question,
            level=level,
            context=payload.context,
        )
    except Exception as exc:  # noqa: BLE001 - mapped to HTTP below
        raise _handle_ai_error(exc) from exc
    return AIAnswerResponse(
        answer=result.text, model=result.model, total_tokens=result.total_tokens
    )


def _sse(chunks: Iterator[str]):
    """Wrap text chunks as SSE events, ending with [DONE] or an error event."""
    try:
        for chunk in chunks:
            yield f"data: {json.dumps({'text': chunk})}\n\n"
        yield "data: [DONE]\n\n"
    except Exception as exc:  # noqa: BLE001 - already streaming; emit an error event
        yield f"data: {json.dumps({'error': str(exc) or 'stream failed'})}\n\n"


@router.post("/teacher/stream")
def ask_teacher_stream(
    payload: TeacherRequest,
    current_user: CurrentDbUser,
    service: AITeacherServiceDep,
    users: UserServiceDep,
) -> StreamingResponse:
    level = users.get_profile(current_user.id).skill_level
    try:
        chunks = service.teach_stream(
            user_id=current_user.id,
            lesson_id=payload.lesson_id,
            topic=payload.topic,
            question=payload.question,
            level=level,
            context=payload.context,
        )
    except Exception as exc:  # noqa: BLE001 - mapped to HTTP below
        raise _handle_ai_error(exc) from exc
    return StreamingResponse(_sse(chunks), media_type="text/event-stream")


@router.post("/tutor/stream")
def ask_tutor_stream(
    payload: TutorRequest,
    current_user: CurrentDbUser,
    service: AITutorServiceDep,
    users: UserServiceDep,
    entitlements: EntitlementServiceDep,
) -> StreamingResponse:
    level = users.get_profile(current_user.id).skill_level
    try:
        entitlements.check_tutor(current_user.id)
        chunks = service.tutor_stream(
            user_id=current_user.id,
            exercise_id=payload.exercise_id,
            code=payload.code,
            question=payload.question,
            level=level,
        )
    except Exception as exc:  # noqa: BLE001 - mapped to HTTP below
        raise _handle_ai_error(exc) from exc
    return StreamingResponse(_sse(chunks), media_type="text/event-stream")


@router.post("/tutor", response_model=AIAnswerResponse)
def ask_tutor(
    payload: TutorRequest,
    current_user: CurrentDbUser,
    service: AITutorServiceDep,
    users: UserServiceDep,
    entitlements: EntitlementServiceDep,
) -> AIAnswerResponse:
    level = users.get_profile(current_user.id).skill_level
    try:
        # Plan-aware daily cap: free users get a bounded number of hints, paid
        # users more; over-limit prompts an upgrade (402).
        entitlements.check_tutor(current_user.id)
        result = service.tutor(
            user_id=current_user.id,
            exercise_id=payload.exercise_id,
            code=payload.code,
            question=payload.question,
            level=level,
        )
    except Exception as exc:  # noqa: BLE001 - mapped to HTTP below
        raise _handle_ai_error(exc) from exc
    return AIAnswerResponse(
        answer=result.text, model=result.model, total_tokens=result.total_tokens
    )


@admin_router.post("/generate", response_model=None, status_code=status.HTTP_201_CREATED)
def generate_content(
    payload: GenerateRequest,
    current_user: CurrentDbUser,
    service: GenerateContentServiceDep,
) -> GeneratedLessonResponse | GeneratedExerciseResponse:
    try:
        if payload.kind == "lesson":
            if payload.course_id is None:
                raise ValueError("course_id is required to generate a lesson")
            lesson = service.generate_lesson(
                user_id=current_user.id,
                course_id=payload.course_id,
                topic=payload.topic,
                level=payload.level,
                order_index=payload.order_index,
            )
            return GeneratedLessonResponse(
                id=lesson.id,
                course_id=lesson.course_id,
                title=lesson.title,
                slug=lesson.slug,
                source=lesson.source,
            )

        if payload.lesson_id is None:
            raise ValueError("lesson_id is required to generate an exercise")
        exercise = service.generate_exercise(
            user_id=current_user.id,
            lesson_id=payload.lesson_id,
            topic=payload.topic,
            language=payload.language,
            level=payload.level,
        )
        return GeneratedExerciseResponse(
            id=exercise.id,
            lesson_id=exercise.lesson_id,
            title=exercise.title,
            slug=exercise.slug,
            language=exercise.language,
            source=exercise.source,
        )
    except Exception as exc:  # noqa: BLE001 - mapped to HTTP below
        raise _handle_ai_error(exc) from exc
