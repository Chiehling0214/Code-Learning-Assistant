"""AI curriculum generation endpoints + the learner's own courses."""

import uuid

from fastapi import APIRouter, BackgroundTasks, HTTPException, status

from app.api.deps import CurrentDbUser, CurriculumServiceDep
from app.infrastructure.generation_worker import run_generation
from app.schemas.content import CourseResponse
from app.schemas.curriculum import GenerationJobResponse

router = APIRouter(tags=["curriculum"])


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
