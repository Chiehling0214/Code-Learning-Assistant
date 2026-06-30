"""Coding-exercise endpoints.

- Public: read an exercise, list a lesson's exercises.
- Authenticated learner: run code, submit code (graded in the background via
  Judge0), poll a submission, list own submissions.
- Admin: create / delete exercises.
"""

import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status

from app.api.deps import (
    CurrentDbUser,
    ExecutionServiceDep,
    ExerciseServiceDep,
    SubmissionServiceDep,
    require_admin,
)
from app.infrastructure.grading import grade_submission
from app.schemas.exercise import (
    ExerciseCreate,
    ExerciseResponse,
    ExerciseSummary,
    RunRequest,
    RunResponse,
    SubmissionResponse,
    SubmitRequest,
)

router = APIRouter(tags=["exercises"])
admin_router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])


def _exercise_response(ex) -> ExerciseResponse:  # noqa: ANN001 - domain entity
    return ExerciseResponse(
        id=ex.id,
        lesson_id=ex.lesson_id,
        language=ex.language,
        title=ex.title,
        slug=ex.slug,
        prompt=ex.prompt,
        starter_code=ex.starter_code,
    )


def _submission_response(sub) -> SubmissionResponse:  # noqa: ANN001 - domain entity
    return SubmissionResponse(
        id=sub.id,
        exercise_id=sub.exercise_id,
        code=sub.code,
        status=sub.status,
        result=sub.result,
        created_at=sub.created_at,
    )


@router.get("/lessons/{lesson_id}/exercises", response_model=list[ExerciseSummary])
def list_lesson_exercises(
    lesson_id: uuid.UUID, service: ExerciseServiceDep
) -> list[ExerciseSummary]:
    return [
        ExerciseSummary(id=ex.id, title=ex.title, slug=ex.slug, language=ex.language)
        for ex in service.list_for_lesson(lesson_id)
    ]


@router.get("/exercises/{exercise_id}", response_model=ExerciseResponse)
def get_exercise(exercise_id: uuid.UUID, service: ExerciseServiceDep) -> ExerciseResponse:
    try:
        exercise = service.get_exercise(exercise_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return _exercise_response(exercise)


@router.post("/exercises/{exercise_id}/run", response_model=RunResponse)
def run_exercise(
    exercise_id: uuid.UUID,
    payload: RunRequest,
    current_user: CurrentDbUser,
    exercises: ExerciseServiceDep,
    execution: ExecutionServiceDep,
) -> RunResponse:
    """Run code once against optional stdin (no grading) for the Run button."""
    try:
        exercise = exercises.get_exercise(exercise_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    result = execution.run(code=payload.code, language=exercise.language, stdin=payload.stdin)
    return RunResponse(
        stdout=result.get("stdout", ""),
        stderr=result.get("stderr", ""),
        status=result.get("status"),
        compile_output=result.get("compile_output"),
        error=result.get("error"),
    )


@router.post(
    "/exercises/{exercise_id}/submit",
    response_model=SubmissionResponse,
    status_code=status.HTTP_201_CREATED,
)
def submit_exercise(
    exercise_id: uuid.UUID,
    payload: SubmitRequest,
    current_user: CurrentDbUser,
    service: SubmissionServiceDep,
    background: BackgroundTasks,
) -> SubmissionResponse:
    try:
        submission = service.create_submission(
            user_id=current_user.id, exercise_id=exercise_id, code=payload.code
        )
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    # Grade in the background; the client polls GET /submissions/{id}.
    background.add_task(grade_submission, submission.id)
    return _submission_response(submission)


@router.get("/exercises/{exercise_id}/submissions", response_model=list[SubmissionResponse])
def list_submissions(
    exercise_id: uuid.UUID,
    current_user: CurrentDbUser,
    service: SubmissionServiceDep,
) -> list[SubmissionResponse]:
    submissions = service.list_submissions(user_id=current_user.id, exercise_id=exercise_id)
    return [_submission_response(s) for s in submissions]


@router.get("/submissions/{submission_id}", response_model=SubmissionResponse)
def get_submission(
    submission_id: uuid.UUID,
    current_user: CurrentDbUser,
    service: SubmissionServiceDep,
) -> SubmissionResponse:
    try:
        submission = service.get_submission(
            user_id=current_user.id, submission_id=submission_id
        )
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return _submission_response(submission)


# ----- admin -----


@admin_router.post(
    "/exercises", response_model=ExerciseResponse, status_code=status.HTTP_201_CREATED
)
def create_exercise(payload: ExerciseCreate, service: ExerciseServiceDep) -> ExerciseResponse:
    try:
        exercise = service.create_exercise(
            lesson_id=payload.lesson_id,
            language=payload.language,
            title=payload.title,
            slug=payload.slug,
            prompt=payload.prompt,
            starter_code=payload.starter_code,
            test_spec=payload.test_spec,
        )
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return _exercise_response(exercise)


@admin_router.delete("/exercises/{exercise_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_exercise(exercise_id: uuid.UUID, service: ExerciseServiceDep) -> None:
    try:
        service.delete_exercise(exercise_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
