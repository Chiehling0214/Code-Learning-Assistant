"""Repository interfaces (ports) for the domain layer.

The application layer depends on these abstractions; concrete implementations
live in ``app/infrastructure/repositories``. This keeps persistence details out
of the inner layers (dependency-inversion principle).
"""

from __future__ import annotations

import uuid
from typing import Protocol

from app.domain.entities import Course, Lesson, ProgrammingLanguage, StudentProfile, User


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

    def get_by_id(self, course_id: uuid.UUID) -> Course | None: ...

    def get_by_slug(self, slug: str) -> Course | None: ...

    def create(
        self, *, language_id: uuid.UUID, title: str, slug: str, description: str | None
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

    def create(
        self,
        *,
        course_id: uuid.UUID,
        title: str,
        slug: str,
        order_index: int,
        content: str,
    ) -> Lesson: ...

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
