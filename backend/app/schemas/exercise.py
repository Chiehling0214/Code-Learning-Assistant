"""Pydantic schemas for coding exercises and submissions."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

# --------------------------------------------------------------------------- #
# Responses
# --------------------------------------------------------------------------- #


class ExerciseResponse(BaseModel):
    """Learner-facing exercise. Excludes ``test_spec`` (hidden test cases)."""

    id: uuid.UUID
    lesson_id: uuid.UUID
    language: str
    title: str
    slug: str
    prompt: str
    starter_code: str


class ExerciseSummary(BaseModel):
    id: uuid.UUID
    title: str
    slug: str
    language: str


class SubmissionResponse(BaseModel):
    id: uuid.UUID
    exercise_id: uuid.UUID
    code: str
    status: str
    result: dict[str, Any] | None = None
    created_at: datetime


# --------------------------------------------------------------------------- #
# Requests
# --------------------------------------------------------------------------- #


class SubmitRequest(BaseModel):
    code: str = Field(min_length=1)


class ExerciseCreate(BaseModel):
    lesson_id: uuid.UUID
    language: str = Field(default="python", max_length=32)
    title: str = Field(min_length=1, max_length=255)
    slug: str = Field(min_length=1, max_length=255)
    prompt: str = ""
    starter_code: str = ""
    test_spec: dict[str, Any] = Field(default_factory=dict)
