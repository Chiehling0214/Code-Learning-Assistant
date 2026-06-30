"""Submission use cases.

In Sprint 3 a submission is simply recorded with status ``pending`` — execution
and grading via Judge0 arrive in Sprint 4.
"""

from __future__ import annotations

import uuid

from app.domain.entities import Submission
from app.domain.repositories import ExerciseRepository, SubmissionRepository


class SubmissionService:
    def __init__(
        self, submissions: SubmissionRepository, exercises: ExerciseRepository
    ) -> None:
        self._submissions = submissions
        self._exercises = exercises

    def create_submission(
        self, *, user_id: uuid.UUID, exercise_id: uuid.UUID, code: str
    ) -> Submission:
        if self._exercises.get_by_id(exercise_id) is None:
            raise LookupError(f"Exercise {exercise_id} not found")
        return self._submissions.create(
            user_id=user_id, exercise_id=exercise_id, code=code, status="pending"
        )

    def list_submissions(
        self, *, user_id: uuid.UUID, exercise_id: uuid.UUID
    ) -> list[Submission]:
        return self._submissions.list_for_user_and_exercise(user_id, exercise_id)

    def get_submission(self, *, user_id: uuid.UUID, submission_id: uuid.UUID) -> Submission:
        """Return a submission owned by ``user_id`` (for polling its verdict)."""
        submission = self._submissions.get_by_id(submission_id)
        if submission is None or submission.user_id != user_id:
            raise LookupError(f"Submission {submission_id} not found")
        return submission
