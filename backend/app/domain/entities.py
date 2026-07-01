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


@dataclass(frozen=True)
class Lesson:
    id: uuid.UUID
    course_id: uuid.UUID
    title: str
    slug: str
    order_index: int
    content: str
    created_at: datetime
    updated_at: datetime
    source: str = "human"


@dataclass(frozen=True)
class Exercise:
    id: uuid.UUID
    lesson_id: uuid.UUID
    language: str
    title: str
    slug: str
    prompt: str
    starter_code: str
    test_spec: dict
    created_at: datetime
    updated_at: datetime
    source: str = "human"


@dataclass(frozen=True)
class Submission:
    id: uuid.UUID
    user_id: uuid.UUID
    exercise_id: uuid.UUID
    code: str
    status: str
    result: dict | None
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class Choice:
    id: uuid.UUID
    question_id: uuid.UUID
    text: str
    is_correct: bool
    order_index: int


@dataclass(frozen=True)
class Question:
    id: uuid.UUID
    quiz_id: uuid.UUID
    prompt: str
    type: str
    order_index: int
    choices: list[Choice]


@dataclass(frozen=True)
class Quiz:
    id: uuid.UUID
    lesson_id: uuid.UUID
    title: str
    slug: str
    description: str | None
    questions: list[Question]
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class QuizAttempt:
    id: uuid.UUID
    user_id: uuid.UUID
    quiz_id: uuid.UUID
    score: int
    answers: dict
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class AIInteraction:
    id: uuid.UUID
    user_id: uuid.UUID
    kind: str
    model: str
    total_tokens: int
    created_at: datetime
