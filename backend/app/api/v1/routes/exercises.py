"""Coding-exercise endpoints.

- Public: read an exercise, list a lesson's exercises.
- Authenticated learner: submit code (stored ``pending``), list own submissions.
- Admin: create / delete exercises.

Code execution and grading arrive in Sprint 4; submissions start as ``pending``.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import (
    CurrentDbUser,
    ExerciseServiceDep,
    SubmissionServiceDep,
    require_admin,
)
from app.schemas.exercise import (
    ExerciseCreate,
    ExerciseResponse,
    ExerciseSummary,
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
) -> SubmissionResponse:
    try:
        submission = service.create_submission(
            user_id=current_user.id, exercise_id=exercise_id, code=payload.code
        )
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return _submission_response(submission)


@router.get("/exercises/{exercise_id}/submissions", response_model=list[SubmissionResponse])
def list_submissions(
    exercise_id: uuid.UUID,
    current_user: CurrentDbUser,
    service: SubmissionServiceDep,
) -> list[SubmissionResponse]:
    submissions = service.list_submissions(user_id=current_user.id, exercise_id=exercise_id)
    return [_submission_response(s) for s in submissions]


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
