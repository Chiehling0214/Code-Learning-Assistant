"""Pydantic schemas for spaced review (Sprint 15)."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel


class ReviewItemResponse(BaseModel):
    id: uuid.UUID
    source: str  # "quiz" | "placement" | "exercise"
    payload: dict[str, Any]
    interval_days: int
    due_at: datetime
    lapses: int
    passes: int
    retired: bool


class DueReviewsResponse(BaseModel):
    due_count: int
    items: list[ReviewItemResponse]


class NotebookResponse(BaseModel):
    items: list[ReviewItemResponse]


class AnswerRequest(BaseModel):
    correct: bool
