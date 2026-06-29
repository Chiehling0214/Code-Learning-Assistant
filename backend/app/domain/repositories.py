"""Repository interfaces (ports) for the domain layer.

The application layer depends on these abstractions; concrete implementations
live in ``app/infrastructure/repositories``. This keeps persistence details out
of the inner layers (dependency-inversion principle).
"""

from __future__ import annotations

import uuid
from typing import Protocol

from app.domain.entities import User


class UserRepository(Protocol):
    """Persistence operations for :class:`~app.domain.entities.User`.

    Only read access needed in Sprint 0; write operations are added in Sprint 1.
    """

    def get_by_id(self, user_id: uuid.UUID) -> User | None: ...

    def get_by_firebase_uid(self, firebase_uid: str) -> User | None: ...
