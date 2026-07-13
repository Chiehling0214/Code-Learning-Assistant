"""Pydantic schemas for the personalized daily plan."""

from __future__ import annotations

import uuid

from pydantic import BaseModel


class TodayItem(BaseModel):
    type: str  # "lesson" | "exercise" | "quiz"
    id: uuid.UUID
    title: str
    course_slug: str


class TodayResponse(BaseModel):
    items: list[TodayItem]
    # Spaced reviews due right now (Sprint 15) — surfaced before new content.
    reviews_due: int = 0
