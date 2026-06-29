"""Repository interfaces (ports) for the domain layer.

The application layer depends on these abstractions; concrete implementations
live in ``app/infrastructure/repositories``. This keeps persistence details out
of the inner layers (dependency-inversion principle).
"""

from __future__ import annotations

import uuid
from typing import Protocol

from app.domain.entities import StudentProfile, User


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
