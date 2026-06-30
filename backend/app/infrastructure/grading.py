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
from app.infrastructure.db.session import SessionLocal
from app.infrastructure.judge0.client import Judge0Client
from app.infrastructure.repositories.sqlalchemy_repositories import (
    SqlAlchemyExerciseRepository,
    SqlAlchemySubmissionRepository,
)

logger = get_logger(__name__)


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
