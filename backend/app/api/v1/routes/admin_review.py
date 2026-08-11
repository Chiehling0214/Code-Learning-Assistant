"""Admin AI-content review console (Sprint 13).

Replaces the retired content-CRUD admin surface. Every endpoint requires an admin
user via ``require_admin`` (non-admins get 403).
"""

import math
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import AdminReviewServiceDep, DbSession, require_admin
from app.infrastructure.repositories.sqlalchemy_repositories import (
    SqlAlchemyGenerationJobRepository,
    SqlAlchemyLanguageRepository,
    SqlAlchemyLanguageTrackRepository,
    SqlAlchemyUserRepository,
)
from app.schemas.admin_review import (
    AdminGenerationJobResponse,
    BulkReviewResponse,
    ReviewChoicePreview,
    ReviewContentPageResponse,
    ReviewCourseOptionResponse,
    ReviewExercisePreview,
    ReviewItemResponse,
    ReviewPreviewResponse,
    ReviewQuestionPreview,
    ReviewQuizPreview,
    ReviewUserOptionResponse,
    UsageResponse,
)

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


@router.get("/content", response_model=ReviewContentPageResponse)
def list_content(
    service: AdminReviewServiceDep,
    source: str = "ai",
    review_status: str | None = None,
    query: str = "",
    course_id: uuid.UUID | None = None,
    user_id: uuid.UUID | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> ReviewContentPageResponse:
    try:
        result = service.search_content(
            source=source,
            review_status=review_status,
            query=query,
            course_id=course_id,
            user_id=user_id,
            page=page,
            page_size=page_size,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return ReviewContentPageResponse(
        items=[_item(item) for item in result.items],
        total=result.total,
        page=result.page,
        page_size=result.page_size,
        total_pages=max(1, math.ceil(result.total / result.page_size)),
    )


@router.get("/content/courses", response_model=list[ReviewCourseOptionResponse])
def list_content_courses(
    service: AdminReviewServiceDep,
    source: str = "ai",
    user_id: uuid.UUID | None = None,
) -> list[ReviewCourseOptionResponse]:
    return [
        ReviewCourseOptionResponse(
            course_id=course.course_id,
            title=course.title,
            total=course.total,
            pending=course.pending,
        )
        for course in service.list_course_options(source=source, user_id=user_id)
    ]


@router.get("/content/users", response_model=list[ReviewUserOptionResponse])
def list_content_users(
    service: AdminReviewServiceDep, source: str = "ai"
) -> list[ReviewUserOptionResponse]:
    return [
        ReviewUserOptionResponse(
            user_id=user.user_id,
            email=user.email,
            display_name=user.display_name,
            course_count=user.course_count,
            lesson_count=user.lesson_count,
            pending=user.pending,
        )
        for user in service.list_user_options(source=source)
    ]


@router.get(
    "/content/lessons/{lesson_id}/preview",
    response_model=ReviewPreviewResponse,
)
def preview_lesson(
    lesson_id: uuid.UUID, service: AdminReviewServiceDep
) -> ReviewPreviewResponse:
    try:
        preview = service.get_preview(lesson_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return ReviewPreviewResponse(
        lesson_id=preview.lesson.id,
        title=preview.lesson.title,
        content=preview.lesson.content,
        exercises=[
            ReviewExercisePreview(
                id=exercise.id,
                title=exercise.title,
                language=exercise.language,
                prompt=exercise.prompt,
                starter_code=exercise.starter_code,
                test_spec=exercise.test_spec,
            )
            for exercise in preview.exercises
        ],
        quizzes=[
            ReviewQuizPreview(
                id=quiz.id,
                title=quiz.title,
                questions=[
                    ReviewQuestionPreview(
                        prompt=question.prompt,
                        explanation=question.explanation,
                        choices=[
                            ReviewChoicePreview(
                                text=choice.text,
                                is_correct=choice.is_correct,
                            )
                            for choice in question.choices
                        ],
                    )
                    for question in quiz.questions
                ],
            )
            for quiz in preview.quizzes
        ],
    )


@router.post(
    "/content/courses/{course_id}/approve",
    response_model=BulkReviewResponse,
)
def approve_course(
    course_id: uuid.UUID, service: AdminReviewServiceDep
) -> BulkReviewResponse:
    try:
        reviewed = service.mark_course_reviewed(course_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return BulkReviewResponse(course_id=course_id, reviewed=reviewed)


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


def _admin_job(job, session: DbSession) -> AdminGenerationJobResponse:  # noqa: ANN001
    track = SqlAlchemyLanguageTrackRepository(session).get_by_id(job.track_id)
    language = (
        SqlAlchemyLanguageRepository(session).get_by_id(track.language_id) if track else None
    )
    user = SqlAlchemyUserRepository(session).get_by_id(job.user_id)
    return AdminGenerationJobResponse(
        id=job.id,
        user_email=user.email if user else "Unknown user",
        language=language.name if language else "Unknown language",
        kind=job.kind,
        status=job.status,
        completed=job.completed,
        total=job.total,
        attempt_count=job.attempt_count,
        max_attempts=job.max_attempts,
        error=job.error,
        cancel_requested=job.cancel_requested,
        created_at=job.created_at,
        updated_at=job.updated_at,
    )


@router.get("/generation-jobs", response_model=list[AdminGenerationJobResponse])
def list_generation_jobs(session: DbSession) -> list[AdminGenerationJobResponse]:
    return [
        _admin_job(job, session)
        for job in SqlAlchemyGenerationJobRepository(session).list_all()[:100]
    ]


@router.post(
    "/generation-jobs/{job_id}/retry", response_model=AdminGenerationJobResponse
)
def retry_generation_job(
    job_id: uuid.UUID, session: DbSession
) -> AdminGenerationJobResponse:
    try:
        job = SqlAlchemyGenerationJobRepository(session).retry(job_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return _admin_job(job, session)


@router.post(
    "/generation-jobs/{job_id}/cancel", response_model=AdminGenerationJobResponse
)
def cancel_generation_job(
    job_id: uuid.UUID, session: DbSession
) -> AdminGenerationJobResponse:
    try:
        job = SqlAlchemyGenerationJobRepository(session).cancel(job_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _admin_job(job, session)
