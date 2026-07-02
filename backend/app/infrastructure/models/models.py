"""ORM models for the CodePath AI domain.

Tables are introduced incrementally per sprint; see the Alembic migrations under
``alembic/versions`` for the schema history.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.db.base import Base


def _uuid_pk() -> Mapped[uuid.UUID]:
    return mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = _uuid_pk()
    firebase_uid: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    profile: Mapped[StudentProfile | None] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )


class StudentProfile(TimestampMixin, Base):
    __tablename__ = "student_profiles"

    id: Mapped[uuid.UUID] = _uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True
    )
    skill_level: Mapped[str] = mapped_column(String(32), default="beginner", nullable=False)

    user: Mapped[User] = relationship(back_populates="profile")


class ProgrammingLanguage(Base):
    __tablename__ = "programming_languages"

    id: Mapped[uuid.UUID] = _uuid_pk()
    name: Mapped[str] = mapped_column(String(64), unique=True)
    slug: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    courses: Mapped[list[Course]] = relationship(back_populates="language")


class Course(TimestampMixin, Base):
    __tablename__ = "courses"

    id: Mapped[uuid.UUID] = _uuid_pk()
    language_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("programming_languages.id", ondelete="CASCADE")
    )
    # Owning learner track for AI-generated, personalized courses (Sprint 11).
    # Null for shared/legacy courses.
    track_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("language_tracks.id", ondelete="CASCADE"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(255))
    slug: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    language: Mapped[ProgrammingLanguage] = relationship(back_populates="courses")
    lessons: Mapped[list[Lesson]] = relationship(
        back_populates="course",
        cascade="all, delete-orphan",
        order_by="Lesson.order_index",
    )


class Lesson(TimestampMixin, Base):
    __tablename__ = "lessons"
    __table_args__ = (UniqueConstraint("course_id", "slug", name="uq_lessons_course_slug"),)

    id: Mapped[uuid.UUID] = _uuid_pk()
    course_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("courses.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str] = mapped_column(String(255))
    slug: Mapped[str] = mapped_column(String(255))
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    content: Mapped[str] = mapped_column(Text, default="", nullable=False)
    # "human" | "ai" — provenance for reviewing AI-authored content (Sprint 6).
    source: Mapped[str] = mapped_column(String(16), default="human", nullable=False)

    course: Mapped[Course] = relationship(back_populates="lessons")
    exercises: Mapped[list[Exercise]] = relationship(
        back_populates="lesson",
        cascade="all, delete-orphan",
        order_by="Exercise.title",
    )


class Exercise(TimestampMixin, Base):
    __tablename__ = "exercises"
    __table_args__ = (UniqueConstraint("lesson_id", "slug", name="uq_exercises_lesson_slug"),)

    id: Mapped[uuid.UUID] = _uuid_pk()
    lesson_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("lessons.id", ondelete="CASCADE"), index=True
    )
    language: Mapped[str] = mapped_column(String(32), default="python", nullable=False)
    title: Mapped[str] = mapped_column(String(255))
    slug: Mapped[str] = mapped_column(String(255))
    prompt: Mapped[str] = mapped_column(Text, default="", nullable=False)
    starter_code: Mapped[str] = mapped_column(Text, default="", nullable=False)
    # Hidden test specification used by the Judge0 grader in Sprint 4.
    test_spec: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    # "human" | "ai" — provenance for reviewing AI-authored content (Sprint 6).
    source: Mapped[str] = mapped_column(String(16), default="human", nullable=False)

    lesson: Mapped[Lesson] = relationship(back_populates="exercises")


class Submission(TimestampMixin, Base):
    __tablename__ = "submissions"

    id: Mapped[uuid.UUID] = _uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    exercise_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("exercises.id", ondelete="CASCADE"), index=True
    )
    code: Mapped[str] = mapped_column(Text, default="", nullable=False)
    # pending | passed | failed | error — graded in Sprint 4; starts "pending".
    status: Mapped[str] = mapped_column(String(16), default="pending", nullable=False)
    result: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)


# --------------------------------------------------------------------------- #
# Quizzes (Sprint 5)
# --------------------------------------------------------------------------- #


class Quiz(TimestampMixin, Base):
    __tablename__ = "quizzes"
    __table_args__ = (UniqueConstraint("lesson_id", "slug", name="uq_quizzes_lesson_slug"),)

    id: Mapped[uuid.UUID] = _uuid_pk()
    lesson_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("lessons.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str] = mapped_column(String(255))
    slug: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    questions: Mapped[list[Question]] = relationship(
        back_populates="quiz",
        cascade="all, delete-orphan",
        order_by="Question.order_index",
    )


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[uuid.UUID] = _uuid_pk()
    quiz_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("quizzes.id", ondelete="CASCADE"), index=True
    )
    prompt: Mapped[str] = mapped_column(Text, default="", nullable=False)
    # "single" — single correct choice. Extensible to other types later.
    type: Mapped[str] = mapped_column(String(16), default="single", nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    quiz: Mapped[Quiz] = relationship(back_populates="questions")
    choices: Mapped[list[Choice]] = relationship(
        back_populates="question",
        cascade="all, delete-orphan",
        order_by="Choice.order_index",
    )


class Choice(Base):
    __tablename__ = "choices"

    id: Mapped[uuid.UUID] = _uuid_pk()
    question_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("questions.id", ondelete="CASCADE"), index=True
    )
    text: Mapped[str] = mapped_column(Text, default="", nullable=False)
    # The answer key. Never serialized to learners (see schemas/quiz.py).
    is_correct: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    question: Mapped[Question] = relationship(back_populates="choices")


class QuizAttempt(TimestampMixin, Base):
    __tablename__ = "quiz_attempts"

    id: Mapped[uuid.UUID] = _uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    quiz_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("quizzes.id", ondelete="CASCADE"), index=True
    )
    # Number of questions answered correctly.
    score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    # Graded detail: {"selected": {qid: cid}, "total": int, "results": [...]}.
    answers: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


# --------------------------------------------------------------------------- #
# AI interactions (Sprint 6)
# --------------------------------------------------------------------------- #


class AIInteraction(Base):
    __tablename__ = "ai_interactions"

    id: Mapped[uuid.UUID] = _uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    # "teacher" | "tutor" | "generate"
    kind: Mapped[str] = mapped_column(String(16), nullable=False)
    model: Mapped[str] = mapped_column(String(64), default="", nullable=False)
    total_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )


# --------------------------------------------------------------------------- #
# Progress tracking (Sprint 7)
# --------------------------------------------------------------------------- #


class ProgressEvent(Base):
    __tablename__ = "progress_events"

    id: Mapped[uuid.UUID] = _uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    # "lesson" | "exercise" | "quiz"
    item_type: Mapped[str] = mapped_column(String(16), nullable=False)
    item_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    # e.g. "completed" (lesson/quiz) or the grading verdict (exercise).
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    completed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )


# --------------------------------------------------------------------------- #
# Billing (Sprint 8)
# --------------------------------------------------------------------------- #


class Subscription(TimestampMixin, Base):
    __tablename__ = "subscriptions"

    id: Mapped[uuid.UUID] = _uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True
    )
    plan: Mapped[str] = mapped_column(String(32), default="free", nullable=False)
    # "inactive" | "active" | "canceled"
    status: Mapped[str] = mapped_column(String(16), default="inactive", nullable=False)
    stripe_customer_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    stripe_subscription_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    current_period_end: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


# --------------------------------------------------------------------------- #
# Language tracks (Sprint 9)
# --------------------------------------------------------------------------- #


class LanguageTrack(TimestampMixin, Base):
    __tablename__ = "language_tracks"
    __table_args__ = (
        UniqueConstraint("user_id", "language_id", name="uq_language_tracks_user_language"),
    )

    id: Mapped[uuid.UUID] = _uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    language_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("programming_languages.id", ondelete="CASCADE")
    )
    # Assessed level (set by the placement test in Sprint 10).
    level: Mapped[str | None] = mapped_column(String(16), nullable=True)
    # "onboarding" (awaiting placement) | "active"
    status: Mapped[str] = mapped_column(String(16), default="active", nullable=False)


class GenerationJob(TimestampMixin, Base):
    __tablename__ = "generation_jobs"

    id: Mapped[uuid.UUID] = _uuid_pk()
    track_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("language_tracks.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    # "pending" | "running" | "done" | "error"
    status: Mapped[str] = mapped_column(String(16), default="pending", nullable=False)
    total: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    completed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    course_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)


# --------------------------------------------------------------------------- #
# Placement test (Sprint 10)
# --------------------------------------------------------------------------- #


class PlacementAssessment(TimestampMixin, Base):
    __tablename__ = "placement_assessments"

    id: Mapped[uuid.UUID] = _uuid_pk()
    track_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("language_tracks.id", ondelete="CASCADE"), unique=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    # "ready" (generated, awaiting submission) | "completed"
    status: Mapped[str] = mapped_column(String(16), default="ready", nullable=False)
    # Generated items WITH answer keys: {"mcqs": [...], "coding": [...]}.
    # Sanitized before serving to the learner (see schemas/placement.py).
    items: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    # Submitted answers + per-item breakdown (populated on submit).
    result: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    level: Mapped[str | None] = mapped_column(String(16), nullable=True)
