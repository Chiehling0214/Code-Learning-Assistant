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

from app.domain.entities import Exercise, Lesson, Quiz
from app.domain.repositories import (
    CourseRepository,
    ExerciseRepository,
    LanguageTrackRepository,
    LessonRepository,
    QuizRepository,
    UserRepository,
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


@dataclass(frozen=True)
class ReviewPreview:
    lesson: Lesson
    exercises: list[Exercise]
    quizzes: list[Quiz]


@dataclass(frozen=True)
class ReviewPage:
    items: list[ReviewItem]
    total: int
    page: int
    page_size: int


@dataclass(frozen=True)
class ReviewCourseOption:
    course_id: uuid.UUID
    title: str
    total: int
    pending: int


@dataclass(frozen=True)
class ReviewUserOption:
    user_id: uuid.UUID
    email: str
    display_name: str | None
    course_count: int
    lesson_count: int
    pending: int


class AdminReviewService:
    def __init__(
        self,
        lessons: LessonRepository,
        exercises: ExerciseRepository,
        quizzes: QuizRepository,
        courses: CourseRepository,
        tracks: LanguageTrackRepository,
        users: UserRepository,
    ) -> None:
        self._lessons = lessons
        self._exercises = exercises
        self._quizzes = quizzes
        self._courses = courses
        self._tracks = tracks
        self._users = users

    def _course_ids_for_user(self, user_id: uuid.UUID) -> set[uuid.UUID]:
        track_ids = {track.id for track in self._tracks.list_by_user(user_id)}
        return {
            course.id
            for course in self._courses.list_all()
            if course.track_id is not None and course.track_id in track_ids
        }

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

    def search_content(
        self,
        *,
        source: str = "ai",
        review_status: str | None = None,
        query: str = "",
        course_id: uuid.UUID | None = None,
        user_id: uuid.UUID | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> ReviewPage:
        if review_status is not None and review_status not in _VALID_STATUSES:
            raise ValueError("Invalid review status")
        page = max(1, page)
        page_size = min(100, max(1, page_size))
        lessons, total = self._lessons.list_for_review(
            source=source,
            review_status=review_status,
            query=query,
            course_id=course_id,
            course_ids=self._course_ids_for_user(user_id) if user_id else None,
            offset=(page - 1) * page_size,
            limit=page_size,
        )
        course_titles: dict[uuid.UUID, str] = {}
        items: list[ReviewItem] = []
        for lesson in lessons:
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
        return ReviewPage(items=items, total=total, page=page, page_size=page_size)

    def list_course_options(
        self, *, source: str = "ai", user_id: uuid.UUID | None = None
    ) -> list[ReviewCourseOption]:
        allowed_course_ids = self._course_ids_for_user(user_id) if user_id else None
        counts: dict[uuid.UUID, list[int]] = {}
        for lesson in self._lessons.list_by_source(source):
            if allowed_course_ids is not None and lesson.course_id not in allowed_course_ids:
                continue
            count = counts.setdefault(lesson.course_id, [0, 0])
            count[0] += 1
            if lesson.review_status == "pending":
                count[1] += 1
        options: list[ReviewCourseOption] = []
        for course_id, (total, pending) in counts.items():
            course = self._courses.get_by_id(course_id)
            options.append(
                ReviewCourseOption(
                    course_id=course_id,
                    title=course.title if course else "Unknown course",
                    total=total,
                    pending=pending,
                )
            )
        return sorted(options, key=lambda option: (option.title, str(option.course_id)))

    def list_user_options(self, *, source: str = "ai") -> list[ReviewUserOption]:
        courses = {course.id: course for course in self._courses.list_all()}
        track_owners = {track.id: track.user_id for track in self._tracks.list_all()}
        counts: dict[uuid.UUID, dict[str, Any]] = {}
        for lesson in self._lessons.list_by_source(source):
            course = courses.get(lesson.course_id)
            owner_id = track_owners.get(course.track_id) if course and course.track_id else None
            if owner_id is None:
                continue
            count = counts.setdefault(owner_id, {"courses": set(), "lessons": 0, "pending": 0})
            count["courses"].add(lesson.course_id)
            count["lessons"] += 1
            if lesson.review_status == "pending":
                count["pending"] += 1

        options: list[ReviewUserOption] = []
        for user in self._users.list_all():
            count = counts.get(
                user.id,
                {"courses": set(), "lessons": 0, "pending": 0},
            )
            options.append(
                ReviewUserOption(
                    user_id=user.id,
                    email=user.email,
                    display_name=user.display_name,
                    course_count=len(count["courses"]),
                    lesson_count=count["lessons"],
                    pending=count["pending"],
                )
            )
        return sorted(
            options,
            key=lambda option: ((option.display_name or "").casefold(), option.email),
        )

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

    def get_preview(self, lesson_id: uuid.UUID) -> ReviewPreview:
        lesson = self._lessons.get_by_id(lesson_id)
        if lesson is None:
            raise LookupError(f"Lesson {lesson_id} not found")
        return ReviewPreview(
            lesson=lesson,
            exercises=self._exercises.list_by_lesson(lesson.id),
            quizzes=self._quizzes.list_by_lesson(lesson.id),
        )

    def mark_course_reviewed(self, course_id: uuid.UUID) -> int:
        if self._courses.get_by_id(course_id) is None:
            raise LookupError(f"Course {course_id} not found")
        reviewed = 0
        for lesson in self._lessons.list_by_course(course_id):
            if lesson.source == "ai" and lesson.review_status == "pending":
                self._lessons.set_review_status(lesson.id, "approved")
                reviewed += 1
        return reviewed

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
