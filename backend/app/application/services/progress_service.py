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
    LanguageTrackRepository,
    LessonRepository,
    ProgressRepository,
    QuizRepository,
    StudentProfileRepository,
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
        tracks: LanguageTrackRepository,
        profiles: StudentProfileRepository,
    ) -> None:
        self._courses = courses
        self._lessons = lessons
        self._exercises = exercises
        self._quizzes = quizzes
        self._progress = progress
        self._tracks = tracks
        self._profiles = profiles

    def _resolve_item(self, item_type: str, item_id: uuid.UUID) -> tuple[Any, dict[str, Any]]:
        if item_type == "course":
            course = self._courses.get_by_id(item_id)
            if course is None:
                raise LookupError("Course not found")
            return course, {
                "item_type": "course",
                "item_id": course.id,
                "title": course.title,
                "path": f"/courses/{course.slug}",
            }

        if item_type == "lesson":
            item = self._lessons.get_by_id(item_id)
            if item is None:
                raise LookupError("Lesson not found")
            course = self._courses.get_by_id(item.course_id)
            path = f"/lessons/{item.id}"
        elif item_type == "exercise":
            item = self._exercises.get_by_id(item_id)
            if item is None:
                raise LookupError("Exercise not found")
            lesson = self._lessons.get_by_id(item.lesson_id)
            course = self._courses.get_by_id(lesson.course_id) if lesson else None
            path = f"/exercises/{item.id}"
        elif item_type == "quiz":
            item = self._quizzes.get_by_id(item_id)
            if item is None:
                raise LookupError("Quiz not found")
            lesson = self._lessons.get_by_id(item.lesson_id)
            course = self._courses.get_by_id(lesson.course_id) if lesson else None
            path = f"/quizzes/{item.id}"
        else:
            raise ValueError("Unsupported learning item type")

        if course is None:
            raise LookupError("Course not found")
        return course, {
            "item_type": item_type,
            "item_id": item.id,
            "title": item.title,
            "path": path,
        }

    def _owned_course_ids(self, user_id: uuid.UUID) -> set[uuid.UUID]:
        track_ids = {track.id for track in self._tracks.list_by_user(user_id)}
        return {
            course.id
            for course in self._courses.list_by_track_ids(list(track_ids))
            if course.kind != "practice"
        }

    def record_activity(
        self, *, user_id: uuid.UUID, item_type: str, item_id: uuid.UUID
    ) -> dict[str, Any]:
        course, item = self._resolve_item(item_type, item_id)
        if course.id not in self._owned_course_ids(user_id):
            raise LookupError("Learning item not found")
        profile = self._profiles.update_resume(
            user_id,
            course_id=course.id,
            item_type=item_type,
            item_id=item_id,
        )
        return {
            **item,
            "course_id": course.id,
            "course_title": course.title,
            "course_slug": course.slug,
            "updated_at": profile.last_learning_at,
        }

    def _get_resume(self, user_id: uuid.UUID) -> dict[str, Any] | None:
        profile = self._profiles.get_by_user_id(user_id)
        if (
            profile is None
            or profile.last_course_id is None
            or profile.last_item_type is None
            or profile.last_item_id is None
        ):
            return None
        try:
            course, item = self._resolve_item(profile.last_item_type, profile.last_item_id)
        except (LookupError, ValueError):
            return None
        if course.id != profile.last_course_id or course.id not in self._owned_course_ids(user_id):
            return None
        return {
            **item,
            "course_id": course.id,
            "course_title": course.title,
            "course_slug": course.slug,
            "updated_at": profile.last_learning_at,
        }

    def get_progress(self, user_id: uuid.UUID) -> dict[str, Any]:
        events = self._progress.list_for_user(user_id)
        done = completed_item_ids(events)

        courses_out: list[dict[str, Any]] = []
        total_all = 0
        completed_all = 0

        # Only the learner's own (track-scoped) courses — never global content,
        # and practice drill containers don't count toward course progress.
        track_ids = [t.id for t in self._tracks.list_by_user(user_id)]
        for course in self._courses.list_by_track_ids(track_ids):
            if course.kind == "practice":
                continue
            total = 0
            completed = 0
            next_item: dict[str, Any] | None = None
            completed_items: list[dict[str, Any]] = []
            for lesson in self._lessons.list_by_course(course.id):
                if lesson.review_status == "hidden":
                    continue
                total += 1
                completed += 1 if lesson.id in done["lesson"] else 0
                if lesson.id in done["lesson"]:
                    completed_items.append({"item_type": "lesson", "item_id": lesson.id})
                if next_item is None and lesson.id not in done["lesson"]:
                    next_item = {
                        "item_type": "lesson",
                        "item_id": lesson.id,
                        "title": lesson.title,
                        "path": f"/lessons/{lesson.id}",
                    }
                for ex in self._exercises.list_by_lesson(lesson.id):
                    total += 1
                    completed += 1 if ex.id in done["exercise"] else 0
                    if ex.id in done["exercise"]:
                        completed_items.append({"item_type": "exercise", "item_id": ex.id})
                    if next_item is None and ex.id not in done["exercise"]:
                        next_item = {
                            "item_type": "exercise",
                            "item_id": ex.id,
                            "title": ex.title,
                            "path": f"/exercises/{ex.id}",
                        }
                for qz in self._quizzes.list_by_lesson(lesson.id):
                    total += 1
                    completed += 1 if qz.id in done["quiz"] else 0
                    if qz.id in done["quiz"]:
                        completed_items.append({"item_type": "quiz", "item_id": qz.id})
                    if next_item is None and qz.id not in done["quiz"]:
                        next_item = {
                            "item_type": "quiz",
                            "item_id": qz.id,
                            "title": qz.title,
                            "path": f"/quizzes/{qz.id}",
                        }

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
                    "next_item": next_item,
                    "completed_items": completed_items,
                }
            )

        return {
            "courses": courses_out,
            "total": total_all,
            "completed": completed_all,
            "percent": round(completed_all / total_all * 100) if total_all else 0,
            "streak": compute_streak(events),
            "resume": self._get_resume(user_id),
        }

    def mark_lesson_complete(self, *, user_id: uuid.UUID, lesson_id: uuid.UUID) -> ProgressEvent:
        if self._lessons.get_by_id(lesson_id) is None:
            raise LookupError(f"Lesson {lesson_id} not found")
        return self._progress.record(
            user_id=user_id, item_type="lesson", item_id=lesson_id, status="completed"
        )
