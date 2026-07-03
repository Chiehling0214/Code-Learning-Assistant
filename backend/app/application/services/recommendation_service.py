"""Recommendation ("Today") use case.

Rule-based: walk courses in order, then lessons by ``order_index``, and within a
lesson surface the lesson, its exercises, then its quizzes — skipping anything
already completed. The daily list size is capped by the learner's skill level.
"""

from __future__ import annotations

import uuid
from typing import Any

from app.application.services.progress_service import completed_item_ids
from app.domain.repositories import (
    CourseRepository,
    ExerciseRepository,
    LanguageTrackRepository,
    LessonRepository,
    ProgressRepository,
    QuizRepository,
)

# Daily plan size by skill level (beginners get a shorter, focused list).
_CAP_BY_LEVEL = {"beginner": 3, "intermediate": 5, "advanced": 8}
_DEFAULT_CAP = 5


class RecommendationService:
    def __init__(
        self,
        courses: CourseRepository,
        lessons: LessonRepository,
        exercises: ExerciseRepository,
        quizzes: QuizRepository,
        progress: ProgressRepository,
        tracks: LanguageTrackRepository,
    ) -> None:
        self._courses = courses
        self._lessons = lessons
        self._exercises = exercises
        self._quizzes = quizzes
        self._progress = progress
        self._tracks = tracks

    def get_today(self, *, user_id: uuid.UUID, skill_level: str) -> list[dict[str, Any]]:
        cap = _CAP_BY_LEVEL.get(skill_level, _DEFAULT_CAP)
        done = completed_item_ids(self._progress.list_for_user(user_id))

        items: list[dict[str, Any]] = []

        def add(item_type: str, item_id: uuid.UUID, title: str, course_slug: str) -> None:
            items.append(
                {"type": item_type, "id": item_id, "title": title, "course_slug": course_slug}
            )

        # Only the learner's own (track-scoped) courses — never global content.
        track_ids = [t.id for t in self._tracks.list_by_user(user_id)]
        for course in self._courses.list_by_track_ids(track_ids):
            for lesson in self._lessons.list_by_course(course.id):
                if lesson.review_status == "hidden":
                    continue
                if lesson.id not in done["lesson"]:
                    add("lesson", lesson.id, lesson.title, course.slug)
                for ex in self._exercises.list_by_lesson(lesson.id):
                    if ex.id not in done["exercise"]:
                        add("exercise", ex.id, ex.title, course.slug)
                for qz in self._quizzes.list_by_lesson(lesson.id):
                    if qz.id not in done["quiz"]:
                        add("quiz", qz.id, qz.title, course.slug)
                if len(items) >= cap:
                    return items[:cap]

        return items[:cap]
