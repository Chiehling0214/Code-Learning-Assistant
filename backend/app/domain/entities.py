"""Domain entities — pure Python, framework-free.

These mirror the persistence models but belong to the inner architecture layer.
They intentionally carry no ORM or framework dependencies so the domain stays
independent of infrastructure choices.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class User:
    id: uuid.UUID
    firebase_uid: str
    email: str
    display_name: str | None
    is_admin: bool
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class StudentProfile:
    id: uuid.UUID
    user_id: uuid.UUID
    skill_level: str
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class ProgrammingLanguage:
    id: uuid.UUID
    name: str
    slug: str
    created_at: datetime


@dataclass(frozen=True)
class Course:
    id: uuid.UUID
    language_id: uuid.UUID
    title: str
    slug: str
    description: str | None
    created_at: datetime
    updated_at: datetime
