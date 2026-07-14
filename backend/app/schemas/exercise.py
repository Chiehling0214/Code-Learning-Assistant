"""Pydantic schemas for coding exercises and submissions."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

# --------------------------------------------------------------------------- #
# Responses
# --------------------------------------------------------------------------- #


class SampleCase(BaseModel):
    """A visible example test (input → expected stdout) shown to the learner."""

    input: str = ""
    expected: str = ""


class ExerciseResponse(BaseModel):
    """Learner-facing exercise. ``test_spec`` stays hidden; only a few
    non-hidden cases are surfaced as samples so the learner knows the I/O shape."""

    id: uuid.UUID
    lesson_id: uuid.UUID
    language: str
    title: str
    slug: str
    prompt: str
    starter_code: str
    sample_cases: list[SampleCase] = []


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


class RunRequest(BaseModel):
    code: str = Field(min_length=1)
    stdin: str = ""


class RunResponse(BaseModel):
    stdout: str = ""
    stderr: str = ""
    status: str | None = None
    compile_output: str | None = None
    error: str | None = None


class ExerciseCreate(BaseModel):
    lesson_id: uuid.UUID
    language: str = Field(default="python", max_length=32)
    title: str = Field(min_length=1, max_length=255)
    slug: str = Field(min_length=1, max_length=255)
    prompt: str = ""
    starter_code: str = ""
    test_spec: dict[str, Any] = Field(default_factory=dict)
