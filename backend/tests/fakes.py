"""In-memory fake repositories for tests (no database required)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from app.domain.entities import StudentProfile, User


def _now() -> datetime:
    return datetime.now(UTC)


class FakeUserRepository:
    def __init__(self) -> None:
        self._by_id: dict[uuid.UUID, User] = {}

    def get_by_id(self, user_id: uuid.UUID) -> User | None:
        return self._by_id.get(user_id)

    def get_by_firebase_uid(self, firebase_uid: str) -> User | None:
        return next((u for u in self._by_id.values() if u.firebase_uid == firebase_uid), None)

    def create(
        self,
        *,
        firebase_uid: str,
        email: str,
        display_name: str | None = None,
        is_admin: bool = False,
    ) -> User:
        now = _now()
        user = User(
            id=uuid.uuid4(),
            firebase_uid=firebase_uid,
            email=email,
            display_name=display_name,
            is_admin=is_admin,
            created_at=now,
            updated_at=now,
        )
        self._by_id[user.id] = user
        return user

    def update_display_name(self, user_id: uuid.UUID, display_name: str | None) -> User:
        existing = self._by_id[user_id]
        updated = User(
            id=existing.id,
            firebase_uid=existing.firebase_uid,
            email=existing.email,
            display_name=display_name,
            is_admin=existing.is_admin,
            created_at=existing.created_at,
            updated_at=_now(),
        )
        self._by_id[user_id] = updated
        return updated


class FakeStudentProfileRepository:
    def __init__(self) -> None:
        self._by_user: dict[uuid.UUID, StudentProfile] = {}

    def get_by_user_id(self, user_id: uuid.UUID) -> StudentProfile | None:
        return self._by_user.get(user_id)

    def create(self, *, user_id: uuid.UUID, skill_level: str = "beginner") -> StudentProfile:
        now = _now()
        profile = StudentProfile(
            id=uuid.uuid4(),
            user_id=user_id,
            skill_level=skill_level,
            created_at=now,
            updated_at=now,
        )
        self._by_user[user_id] = profile
        return profile

    def update_skill_level(self, user_id: uuid.UUID, skill_level: str) -> StudentProfile:
        existing = self._by_user[user_id]
        updated = StudentProfile(
            id=existing.id,
            user_id=existing.user_id,
            skill_level=skill_level,
            created_at=existing.created_at,
            updated_at=_now(),
        )
        self._by_user[user_id] = updated
        return updated
