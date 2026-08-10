"""Cross-device persistence for coding-exercise drafts."""

from __future__ import annotations

import uuid

from app.domain.entities import CodeDraft
from app.domain.repositories import CodeDraftRepository, ExerciseRepository


class DraftService:
    def __init__(self, drafts: CodeDraftRepository, exercises: ExerciseRepository) -> None:
        self._drafts = drafts
        self._exercises = exercises

    def get(self, *, user_id: uuid.UUID, exercise_id: uuid.UUID) -> CodeDraft | None:
        if self._exercises.get_by_id(exercise_id) is None:
            raise LookupError("Exercise not found")
        return self._drafts.get(user_id, exercise_id)

    def save(self, *, user_id: uuid.UUID, exercise_id: uuid.UUID, code: str) -> CodeDraft:
        if self._exercises.get_by_id(exercise_id) is None:
            raise LookupError("Exercise not found")
        return self._drafts.upsert(user_id=user_id, exercise_id=exercise_id, code=code)

    def delete(self, *, user_id: uuid.UUID, exercise_id: uuid.UUID) -> None:
        self._drafts.delete(user_id, exercise_id)
