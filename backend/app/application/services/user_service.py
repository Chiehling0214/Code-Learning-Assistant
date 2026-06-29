"""User provisioning and profile use cases.

Orchestrates the user and student-profile repositories. Depends only on the
domain repository interfaces, not on SQLAlchemy.
"""

from __future__ import annotations

import uuid

from app.core.security import Identity
from app.domain.entities import StudentProfile, User
from app.domain.repositories import StudentProfileRepository, UserRepository


class UserService:
    def __init__(self, users: UserRepository, profiles: StudentProfileRepository) -> None:
        self._users = users
        self._profiles = profiles

    def get_or_create_from_identity(self, identity: Identity) -> User:
        """Return the persisted user for an authenticated identity.

        On first sign-in, creates the ``User`` and an empty ``StudentProfile``.
        """
        existing = self._users.get_by_firebase_uid(identity.uid)
        if existing is not None:
            return existing

        user = self._users.create(
            firebase_uid=identity.uid,
            email=identity.email or f"{identity.uid}@unknown.local",
            display_name=None,
            is_admin=identity.is_admin,
        )
        self._profiles.create(user_id=user.id)
        return user

    def get_profile(self, user_id: uuid.UUID) -> StudentProfile:
        """Return the user's profile, creating a default one if absent."""
        profile = self._profiles.get_by_user_id(user_id)
        if profile is None:
            profile = self._profiles.create(user_id=user_id)
        return profile

    def update_profile(
        self,
        user_id: uuid.UUID,
        *,
        display_name: str | None,
        skill_level: str | None,
    ) -> tuple[User, StudentProfile]:
        """Update display name and/or skill level; returns the fresh records."""
        user = self._users.get_by_id(user_id)
        if user is None:
            raise LookupError(f"User {user_id} not found")

        if display_name is not None:
            user = self._users.update_display_name(user_id, display_name)

        profile = self.get_profile(user_id)
        if skill_level is not None:
            profile = self._profiles.update_skill_level(user_id, skill_level)

        return user, profile
