"""Coding-exercise use cases.

Read access for learners and create/delete for admins. Depends only on the
domain repository interfaces. Raises :class:`LookupError` when an exercise (or
its lesson) is missing; the API layer maps that to ``404``.
"""

from __future__ import annotations

import uuid

from app.domain.entities import Exercise
from app.domain.repositories import ExerciseRepository, LessonRepository


class ExerciseService:
    def __init__(self, exercises: ExerciseRepository, lessons: LessonRepository) -> None:
        self._exercises = exercises
        self._lessons = lessons

    def get_exercise(self, exercise_id: uuid.UUID) -> Exercise:
        exercise = self._exercises.get_by_id(exercise_id)
        if exercise is None:
            raise LookupError(f"Exercise {exercise_id} not found")
        return exercise

    def list_for_lesson(self, lesson_id: uuid.UUID) -> list[Exercise]:
        return self._exercises.list_by_lesson(lesson_id)

    def create_exercise(
        self,
        *,
        lesson_id: uuid.UUID,
        language: str,
        title: str,
        slug: str,
        prompt: str,
        starter_code: str,
        test_spec: dict,
        source: str = "human",
    ) -> Exercise:
        if self._lessons.get_by_id(lesson_id) is None:
            raise LookupError(f"Lesson {lesson_id} not found")
        return self._exercises.create(
            lesson_id=lesson_id,
            language=language,
            title=title,
            slug=slug,
            prompt=prompt,
            starter_code=starter_code,
            test_spec=test_spec,
            source=source,
        )

    def delete_exercise(self, exercise_id: uuid.UUID) -> None:
        self._exercises.delete(exercise_id)
