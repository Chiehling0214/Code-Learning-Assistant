"""Background grading orchestration.

Runs after the HTTP response (FastAPI ``BackgroundTasks``), so it opens its own
session, grades the submission via Judge0, and persists the verdict. Any
unexpected failure marks the submission ``error`` rather than crashing.
"""

from __future__ import annotations

import uuid

from app.application.services.execution_service import ExecutionService
from app.core.config import get_settings
from app.core.logging import get_logger
from app.domain.repositories import ProgressRepository
from app.infrastructure.db.session import SessionLocal
from app.infrastructure.judge0.client import Judge0Client
from app.infrastructure.repositories.sqlalchemy_repositories import (
    SqlAlchemyExerciseRepository,
    SqlAlchemyProgressRepository,
    SqlAlchemySubmissionRepository,
)

logger = get_logger(__name__)

# Verdicts worth recording as progress (an infrastructure "error" is not).
_RECORDED_VERDICTS = {"passed", "failed"}


def record_exercise_progress(
    progress: ProgressRepository,
    *,
    user_id: uuid.UUID,
    exercise_id: uuid.UUID,
    verdict: str,
) -> bool:
    """Record an exercise grading verdict as a progress event.

    Returns whether an event was written (skips infrastructure ``error``s).
    """
    if verdict not in _RECORDED_VERDICTS:
        return False
    progress.record(
        user_id=user_id, item_type="exercise", item_id=exercise_id, status=verdict
    )
    return True


def grade_submission(submission_id: uuid.UUID) -> None:
    """Grade a stored submission and persist its verdict/result."""
    settings = get_settings()
    session = SessionLocal()
    submissions = SqlAlchemySubmissionRepository(session)
    exercises = SqlAlchemyExerciseRepository(session)
    try:
        submission = submissions.get_by_id(submission_id)
        if submission is None:
            return
        exercise = exercises.get_by_id(submission.exercise_id)
        if exercise is None:
            submissions.update_result(
                submission_id, status="error", result={"error": "Exercise not found"}
            )
            session.commit()
            return

        service = ExecutionService(Judge0Client(settings))
        status, result = service.grade(
            code=submission.code, language=exercise.language, test_spec=exercise.test_spec
        )
        submissions.update_result(submission_id, status=status, result=result)
        record_exercise_progress(
            SqlAlchemyProgressRepository(session),
            user_id=submission.user_id,
            exercise_id=submission.exercise_id,
            verdict=status,
        )
        session.commit()
    except Exception as exc:  # noqa: BLE001 - never let a background task crash silently
        logger.exception("Grading failed for submission %s: %s", submission_id, exc)
        session.rollback()
        try:
            submissions.update_result(
                submission_id, status="error", result={"error": "Grading failed"}
            )
            session.commit()
        except Exception:  # noqa: BLE001
            session.rollback()
    finally:
        session.close()
