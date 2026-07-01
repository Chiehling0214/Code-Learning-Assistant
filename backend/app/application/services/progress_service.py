"""Progress aggregation use cases.

Derives per-course completion, overall totals, and a day streak from the raw
``ProgressEvent`` log, and records lesson completions. Completion semantics:
lessons/quizzes count once an event exists; an exercise counts only when
``passed``.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from app.domain.entities import ProgressEvent
from app.domain.repositories import (
    CourseRepository,
    ExerciseRepository,
    LessonRepository,
    ProgressRepository,
    QuizRepository,
)


def completed_item_ids(events: list[ProgressEvent]) -> dict[str, set[uuid.UUID]]:
    """Map ``item_type -> set of completed item ids`` from the event log."""
    done: dict[str, set[uuid.UUID]] = {"lesson": set(), "exercise": set(), "quiz": set()}
    for event in events:
        if event.item_type == "lesson" and event.status == "completed":
            done["lesson"].add(event.item_id)
        elif event.item_type == "exercise" and event.status == "passed":
            done["exercise"].add(event.item_id)
        elif event.item_type == "quiz":
            done["quiz"].add(event.item_id)
    return done


def compute_streak(events: list[ProgressEvent], *, today: object = None) -> int:
    """Count consecutive days (ending today or yesterday) with any completion."""
    days = {e.completed_at.date() for e in events}
    if not days:
        return 0
    current = today or datetime.now(UTC).date()
    if current not in days:
        current = current - timedelta(days=1)
        if current not in days:
            return 0
    streak = 0
    while current in days:
        streak += 1
        current = current - timedelta(days=1)
    return streak


class ProgressService:
    def __init__(
        self,
        courses: CourseRepository,
        lessons: LessonRepository,
        exercises: ExerciseRepository,
        quizzes: QuizRepository,
        progress: ProgressRepository,
    ) -> None:
        self._courses = courses
        self._lessons = lessons
        self._exercises = exercises
        self._quizzes = quizzes
        self._progress = progress

    def get_progress(self, user_id: uuid.UUID) -> dict[str, Any]:
        events = self._progress.list_for_user(user_id)
        done = completed_item_ids(events)

        courses_out: list[dict[str, Any]] = []
        total_all = 0
        completed_all = 0

        for course in self._courses.list_all():
            total = 0
            completed = 0
            for lesson in self._lessons.list_by_course(course.id):
                total += 1
                completed += 1 if lesson.id in done["lesson"] else 0
                for ex in self._exercises.list_by_lesson(lesson.id):
                    total += 1
                    completed += 1 if ex.id in done["exercise"] else 0
                for qz in self._quizzes.list_by_lesson(lesson.id):
                    total += 1
                    completed += 1 if qz.id in done["quiz"] else 0

            total_all += total
            completed_all += completed
            courses_out.append(
                {
                    "course_id": course.id,
                    "title": course.title,
                    "slug": course.slug,
                    "total": total,
                    "completed": completed,
                    "percent": round(completed / total * 100) if total else 0,
                }
            )

        return {
            "courses": courses_out,
            "total": total_all,
            "completed": completed_all,
            "percent": round(completed_all / total_all * 100) if total_all else 0,
            "streak": compute_streak(events),
        }

    def mark_lesson_complete(self, *, user_id: uuid.UUID, lesson_id: uuid.UUID) -> ProgressEvent:
        if self._lessons.get_by_id(lesson_id) is None:
            raise LookupError(f"Lesson {lesson_id} not found")
        return self._progress.record(
            user_id=user_id, item_type="lesson", item_id=lesson_id, status="completed"
        )
