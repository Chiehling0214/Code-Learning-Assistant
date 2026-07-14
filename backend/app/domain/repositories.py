"""Repository interfaces (ports) for the domain layer.

The application layer depends on these abstractions; concrete implementations
live in ``app/infrastructure/repositories``. This keeps persistence details out
of the inner layers (dependency-inversion principle).
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Protocol

from app.domain.entities import (
    AIInteraction,
    Course,
    CourseChatMessage,
    Exercise,
    GenerationJob,
    LanguageTrack,
    Lesson,
    PlacementAssessment,
    ProgrammingLanguage,
    ProgressEvent,
    Question,
    Quiz,
    QuizAttempt,
    ReviewItem,
    StudentProfile,
    Submission,
    Subscription,
    User,
)


class UserRepository(Protocol):
    """Persistence operations for :class:`~app.domain.entities.User`."""

    def get_by_id(self, user_id: uuid.UUID) -> User | None: ...

    def get_by_firebase_uid(self, firebase_uid: str) -> User | None: ...

    def create(
        self,
        *,
        firebase_uid: str,
        email: str,
        display_name: str | None = None,
        is_admin: bool = False,
    ) -> User: ...

    def update_display_name(self, user_id: uuid.UUID, display_name: str | None) -> User: ...


class StudentProfileRepository(Protocol):
    """Persistence operations for :class:`~app.domain.entities.StudentProfile`."""

    def get_by_user_id(self, user_id: uuid.UUID) -> StudentProfile | None: ...

    def create(self, *, user_id: uuid.UUID, skill_level: str = "beginner") -> StudentProfile: ...

    def update_skill_level(self, user_id: uuid.UUID, skill_level: str) -> StudentProfile: ...


class LanguageRepository(Protocol):
    """Persistence operations for :class:`~app.domain.entities.ProgrammingLanguage`."""

    def list_all(self) -> list[ProgrammingLanguage]: ...

    def get_by_id(self, language_id: uuid.UUID) -> ProgrammingLanguage | None: ...

    def get_by_slug(self, slug: str) -> ProgrammingLanguage | None: ...

    def create(self, *, name: str, slug: str) -> ProgrammingLanguage: ...

    def update(
        self, language_id: uuid.UUID, *, name: str | None, slug: str | None
    ) -> ProgrammingLanguage: ...

    def delete(self, language_id: uuid.UUID) -> None: ...


class CourseRepository(Protocol):
    """Persistence operations for :class:`~app.domain.entities.Course`."""

    def list_all(self) -> list[Course]: ...

    def list_by_track_ids(self, track_ids: list[uuid.UUID]) -> list[Course]: ...

    def get_by_id(self, course_id: uuid.UUID) -> Course | None: ...

    def get_by_slug(self, slug: str) -> Course | None: ...

    def create(
        self,
        *,
        language_id: uuid.UUID,
        title: str,
        slug: str,
        description: str | None,
        track_id: uuid.UUID | None = None,
        kind: str = "course",
    ) -> Course: ...

    def update(
        self,
        course_id: uuid.UUID,
        *,
        title: str | None,
        slug: str | None,
        description: str | None,
    ) -> Course: ...

    def delete(self, course_id: uuid.UUID) -> None: ...


class LessonRepository(Protocol):
    """Persistence operations for :class:`~app.domain.entities.Lesson`."""

    def get_by_id(self, lesson_id: uuid.UUID) -> Lesson | None: ...

    def list_by_course(self, course_id: uuid.UUID) -> list[Lesson]: ...

    def list_by_source(self, source: str) -> list[Lesson]: ...

    def create(
        self,
        *,
        course_id: uuid.UUID,
        title: str,
        slug: str,
        order_index: int,
        content: str,
        source: str = "human",
        review_status: str = "approved",
    ) -> Lesson: ...

    def set_review_status(self, lesson_id: uuid.UUID, review_status: str) -> Lesson: ...

    def update(
        self,
        lesson_id: uuid.UUID,
        *,
        title: str | None,
        slug: str | None,
        order_index: int | None,
        content: str | None,
    ) -> Lesson: ...

    def delete(self, lesson_id: uuid.UUID) -> None: ...


class ExerciseRepository(Protocol):
    """Persistence operations for :class:`~app.domain.entities.Exercise`."""

    def get_by_id(self, exercise_id: uuid.UUID) -> Exercise | None: ...

    def list_by_lesson(self, lesson_id: uuid.UUID) -> list[Exercise]: ...

    def create(
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
    ) -> Exercise: ...

    def delete(self, exercise_id: uuid.UUID) -> None: ...


class SubmissionRepository(Protocol):
    """Persistence operations for :class:`~app.domain.entities.Submission`."""

    def get_by_id(self, submission_id: uuid.UUID) -> Submission | None: ...

    def list_for_user_and_exercise(
        self, user_id: uuid.UUID, exercise_id: uuid.UUID
    ) -> list[Submission]: ...

    def create(
        self,
        *,
        user_id: uuid.UUID,
        exercise_id: uuid.UUID,
        code: str,
        status: str = "pending",
    ) -> Submission: ...

    def update_result(
        self, submission_id: uuid.UUID, *, status: str, result: dict | None
    ) -> Submission: ...


class QuizRepository(Protocol):
    """Persistence operations for quizzes (with nested questions/choices)."""

    def get_by_id(self, quiz_id: uuid.UUID) -> Quiz | None: ...

    def list_by_lesson(self, lesson_id: uuid.UUID) -> list[Quiz]: ...

    def create(
        self, *, lesson_id: uuid.UUID, title: str, slug: str, description: str | None
    ) -> Quiz: ...

    def add_question(
        self,
        *,
        quiz_id: uuid.UUID,
        prompt: str,
        type: str,
        order_index: int,
        choices: list[dict],
        explanation: str = "",
    ) -> Question: ...

    def delete(self, quiz_id: uuid.UUID) -> None: ...


class QuizAttemptRepository(Protocol):
    """Persistence operations for :class:`~app.domain.entities.QuizAttempt`."""

    def create(
        self, *, user_id: uuid.UUID, quiz_id: uuid.UUID, score: int, answers: dict
    ) -> QuizAttempt: ...

    def list_for_user_and_quiz(
        self, user_id: uuid.UUID, quiz_id: uuid.UUID
    ) -> list[QuizAttempt]: ...


class AIInteractionRepository(Protocol):
    """Records of AI calls, used for usage logging and per-user rate limiting."""

    def create(
        self, *, user_id: uuid.UUID, kind: str, model: str, total_tokens: int
    ) -> AIInteraction: ...

    def count_since(
        self, user_id: uuid.UUID, since: datetime, *, kind: str | None = None
    ) -> int: ...


class ProgressRepository(Protocol):
    """Completion events across lessons, exercises, and quizzes."""

    def record(
        self,
        *,
        user_id: uuid.UUID,
        item_type: str,
        item_id: uuid.UUID,
        status: str,
        score: int | None = None,
    ) -> ProgressEvent: ...

    def list_for_user(self, user_id: uuid.UUID) -> list[ProgressEvent]: ...


class SubscriptionRepository(Protocol):
    """Persistence operations for :class:`~app.domain.entities.Subscription`."""

    def get_by_user_id(self, user_id: uuid.UUID) -> Subscription | None: ...

    def upsert(
        self,
        *,
        user_id: uuid.UUID,
        plan: str,
        status: str,
        stripe_customer_id: str | None = None,
        stripe_subscription_id: str | None = None,
        current_period_end: datetime | None = None,
    ) -> Subscription: ...


class LanguageTrackRepository(Protocol):
    """A learner's chosen language tracks (Sprint 9)."""

    def get_by_id(self, track_id: uuid.UUID) -> LanguageTrack | None: ...

    def list_by_user(self, user_id: uuid.UUID) -> list[LanguageTrack]: ...

    def get_by_user_and_language(
        self, user_id: uuid.UUID, language_id: uuid.UUID
    ) -> LanguageTrack | None: ...

    def count_by_user(self, user_id: uuid.UUID) -> int: ...

    def create(
        self, *, user_id: uuid.UUID, language_id: uuid.UUID, status: str = "active"
    ) -> LanguageTrack: ...

    def set_level(self, track_id: uuid.UUID, level: str) -> LanguageTrack: ...

    def delete(self, track_id: uuid.UUID) -> None: ...


class GenerationJobRepository(Protocol):
    """Tracks an async AI curriculum-generation job (Sprint 11)."""

    def get_by_id(self, job_id: uuid.UUID) -> GenerationJob | None: ...

    def get_latest_for_track(self, track_id: uuid.UUID) -> GenerationJob | None: ...

    def create(
        self, *, track_id: uuid.UUID, user_id: uuid.UUID, total: int
    ) -> GenerationJob: ...

    def update(
        self,
        job_id: uuid.UUID,
        *,
        status: str | None = None,
        completed: int | None = None,
        course_id: uuid.UUID | None = None,
        error: str | None = None,
    ) -> GenerationJob: ...


class ReviewItemRepository(Protocol):
    """Captured mistakes scheduled for spaced review (Sprint 15)."""

    def get_by_id(self, item_id: uuid.UUID) -> ReviewItem | None: ...

    def get_by_user_and_ref(
        self, user_id: uuid.UUID, item_ref: uuid.UUID
    ) -> ReviewItem | None: ...

    def list_due(self, user_id: uuid.UUID, now: datetime) -> list[ReviewItem]: ...

    def count_due(self, user_id: uuid.UUID, now: datetime) -> int: ...

    def list_all(self, user_id: uuid.UUID) -> list[ReviewItem]: ...

    def create(
        self,
        *,
        user_id: uuid.UUID,
        source: str,
        item_ref: uuid.UUID,
        payload: dict,
        interval_days: int,
        due_at: datetime,
    ) -> ReviewItem: ...

    def update(
        self,
        item_id: uuid.UUID,
        *,
        payload: dict | None = None,
        interval_days: int | None = None,
        due_at: datetime | None = None,
        lapses: int | None = None,
        passes: int | None = None,
        retired: bool | None = None,
    ) -> ReviewItem: ...


class CourseChatRepository(Protocol):
    """In-course chat messages between a learner and the AI (Sprint 12)."""

    def list_by_course_and_user(
        self, course_id: uuid.UUID, user_id: uuid.UUID
    ) -> list[CourseChatMessage]: ...

    def create(
        self, *, course_id: uuid.UUID, user_id: uuid.UUID, role: str, content: str
    ) -> CourseChatMessage: ...


class PlacementRepository(Protocol):
    """Persistence for the placement assessment (one per track)."""

    def get_by_track(self, track_id: uuid.UUID) -> PlacementAssessment | None: ...

    def create(
        self, *, track_id: uuid.UUID, user_id: uuid.UUID, items: dict
    ) -> PlacementAssessment: ...

    def save_result(
        self,
        assessment_id: uuid.UUID,
        *,
        result: dict,
        score: int,
        level: str,
    ) -> PlacementAssessment: ...
