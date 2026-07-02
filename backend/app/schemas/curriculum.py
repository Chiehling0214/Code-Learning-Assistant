"""Pydantic schemas for AI curriculum generation."""

from __future__ import annotations

import uuid

from pydantic import BaseModel


class GenerationJobResponse(BaseModel):
    id: uuid.UUID
    track_id: uuid.UUID
    status: str  # "pending" | "running" | "done" | "error"
    total: int
    completed: int
    course_id: uuid.UUID | None = None
    error: str | None = None
