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
