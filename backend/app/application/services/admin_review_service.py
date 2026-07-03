"""Admin review of AI-generated content (Sprint 13).

Replaces the retired content-CRUD admin surface with a review console over the
``source="ai"`` lessons: list them (with their course + exercise/quiz counts),
approve or hide them (hidden lessons are excluded from learner serving), and a
small usage summary.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any

from app.domain.repositories import (
    CourseRepository,
    ExerciseRepository,
    LessonRepository,
    QuizRepository,
)

_VALID_STATUSES = {"approved", "pending", "hidden"}


@dataclass(frozen=True)
class ReviewItem:
    lesson_id: uuid.UUID
    title: str
    course_id: uuid.UUID
    course_title: str
    source: str
    review_status: str
    exercise_count: int
    quiz_count: int


class AdminReviewService:
    def __init__(
        self,
        lessons: LessonRepository,
        exercises: ExerciseRepository,
        quizzes: QuizRepository,
        courses: CourseRepository,
    ) -> None:
        self._lessons = lessons
        self._exercises = exercises
        self._quizzes = quizzes
        self._courses = courses

    def list_content(self, *, source: str = "ai") -> list[ReviewItem]:
        course_titles: dict[uuid.UUID, str] = {}
        items: list[ReviewItem] = []
        for lesson in self._lessons.list_by_source(source):
            if lesson.course_id not in course_titles:
                course = self._courses.get_by_id(lesson.course_id)
                course_titles[lesson.course_id] = course.title if course else ""
            items.append(
                ReviewItem(
                    lesson_id=lesson.id,
                    title=lesson.title,
                    course_id=lesson.course_id,
                    course_title=course_titles[lesson.course_id],
                    source=lesson.source,
                    review_status=lesson.review_status,
                    exercise_count=len(self._exercises.list_by_lesson(lesson.id)),
                    quiz_count=len(self._quizzes.list_by_lesson(lesson.id)),
                )
            )
        return items

    def set_status(self, *, lesson_id: uuid.UUID, review_status: str) -> ReviewItem:
        if review_status not in _VALID_STATUSES:
            raise ValueError(f"Invalid review_status: {review_status!r}")
        lesson = self._lessons.set_review_status(lesson_id, review_status)
        course = self._courses.get_by_id(lesson.course_id)
        return ReviewItem(
            lesson_id=lesson.id,
            title=lesson.title,
            course_id=lesson.course_id,
            course_title=course.title if course else "",
            source=lesson.source,
            review_status=lesson.review_status,
            exercise_count=len(self._exercises.list_by_lesson(lesson.id)),
            quiz_count=len(self._quizzes.list_by_lesson(lesson.id)),
        )

    def usage(self) -> dict[str, Any]:
        ai_lessons = self._lessons.list_by_source("ai")
        by_status = {"approved": 0, "pending": 0, "hidden": 0}
        exercises = 0
        quizzes = 0
        for lesson in ai_lessons:
            by_status[lesson.review_status] = by_status.get(lesson.review_status, 0) + 1
            exercises += len(self._exercises.list_by_lesson(lesson.id))
            quizzes += len(self._quizzes.list_by_lesson(lesson.id))
        return {
            "ai_lessons": len(ai_lessons),
            "pending": by_status["pending"],
            "approved": by_status["approved"],
            "hidden": by_status["hidden"],
            "ai_exercises": exercises,
            "ai_quizzes": quizzes,
        }
