"""AI curriculum generation endpoints + the learner's own courses."""

import uuid

from fastapi import APIRouter, BackgroundTasks, HTTPException, status

from app.api.deps import CourseChatServiceDep, CurrentDbUser, CurriculumServiceDep
from app.application.ports.ai_provider import AINotConfiguredError, AIProviderError
from app.application.services.ai_usage import RateLimitError
from app.domain.entities import Lesson
from app.infrastructure.generation_worker import run_generation
from app.schemas.content import CourseResponse
from app.schemas.curriculum import (
    AddedLesson,
    ChatListResponse,
    ChatMessageResponse,
    ChatSendRequest,
    ChatSendResponse,
    ExtendRequest,
    ExtendResponse,
    ExtensionStatusResponse,
    GenerationJobResponse,
)

router = APIRouter(tags=["curriculum"])


def _added(lessons: list[Lesson]) -> list[AddedLesson]:
    return [
        AddedLesson(id=ln.id, title=ln.title, slug=ln.slug, order_index=ln.order_index)
        for ln in lessons
    ]


def _job_response(job) -> GenerationJobResponse:  # noqa: ANN001 - domain entity
    return GenerationJobResponse(
        id=job.id,
        track_id=job.track_id,
        status=job.status,
        total=job.total,
        completed=job.completed,
        course_id=job.course_id,
        error=job.error,
    )


@router.post(
    "/me/tracks/{track_id}/generate",
    response_model=GenerationJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def start_generation(
    track_id: uuid.UUID,
    current_user: CurrentDbUser,
    service: CurriculumServiceDep,
    background: BackgroundTasks,
) -> GenerationJobResponse:
    try:
        job = service.start_generation(user_id=current_user.id, track_id=track_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    # Only kick off a worker for a freshly-created (pending) job.
    if job.status == "pending":
        background.add_task(run_generation, job.id)
    return _job_response(job)


@router.get("/me/tracks/{track_id}/generation", response_model=GenerationJobResponse)
def get_generation(
    track_id: uuid.UUID,
    current_user: CurrentDbUser,
    service: CurriculumServiceDep,
) -> GenerationJobResponse:
    try:
        job = service.get_status(user_id=current_user.id, track_id=track_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return _job_response(job)


@router.get("/me/courses", response_model=list[CourseResponse])
def list_my_courses(
    current_user: CurrentDbUser, service: CurriculumServiceDep
) -> list[CourseResponse]:
    courses = service.list_courses(current_user.id)
    return [
        CourseResponse(
            id=c.id,
            language_id=c.language_id,
            title=c.title,
            slug=c.slug,
            description=c.description,
        )
        for c in courses
    ]


# ----- Continuous learning: extend + in-course chat (Sprint 12) -----


@router.get("/courses/{course_id}/extension", response_model=ExtensionStatusResponse)
def get_extension_status(
    course_id: uuid.UUID, current_user: CurrentDbUser, service: CurriculumServiceDep
) -> ExtensionStatusResponse:
    try:
        service.get_owned_course(course_id=course_id, user_id=current_user.id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    _, _, percent = service.course_completion(course_id=course_id, user_id=current_user.id)
    return ExtensionStatusResponse(
        course_id=course_id,
        lesson_count=service.lesson_count(course_id),
        completion_percent=percent,
        can_extend=service.can_extend(course_id=course_id, user_id=current_user.id),
    )


@router.post("/courses/{course_id}/extend", response_model=ExtendResponse)
def extend_course(
    course_id: uuid.UUID,
    body: ExtendRequest,
    current_user: CurrentDbUser,
    service: CurriculumServiceDep,
) -> ExtendResponse:
    try:
        added = service.extend_course(
            course_id=course_id, user_id=current_user.id, focus=body.topic, count=body.count
        )
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except RateLimitError as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(exc)
        ) from exc
    except AINotConfiguredError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc
    except AIProviderError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI is busy right now; please try again shortly.",
        ) from exc
    return ExtendResponse(added=_added(added), lesson_count=service.lesson_count(course_id))


@router.get("/courses/{course_id}/chat", response_model=ChatListResponse)
def get_course_chat(
    course_id: uuid.UUID, current_user: CurrentDbUser, service: CourseChatServiceDep
) -> ChatListResponse:
    try:
        messages = service.list_messages(course_id=course_id, user_id=current_user.id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return ChatListResponse(
        messages=[
            ChatMessageResponse(
                id=m.id, role=m.role, content=m.content, created_at=m.created_at
            )
            for m in messages
        ]
    )


@router.post("/courses/{course_id}/chat", response_model=ChatSendResponse)
def send_course_chat(
    course_id: uuid.UUID,
    body: ChatSendRequest,
    current_user: CurrentDbUser,
    service: CourseChatServiceDep,
) -> ChatSendResponse:
    try:
        assistant, added = service.send(
            course_id=course_id,
            user_id=current_user.id,
            message=body.message,
            count=body.count,
        )
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except RateLimitError as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(exc)
        ) from exc
    except AINotConfiguredError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc
    except AIProviderError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI is busy right now; please try again shortly.",
        ) from exc
    return ChatSendResponse(
        reply=ChatMessageResponse(
            id=assistant.id,
            role=assistant.role,
            content=assistant.content,
            created_at=assistant.created_at,
        ),
        added=_added(added),
    )
