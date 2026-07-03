"""Schemas for the admin AI-content review console (Sprint 13)."""

from __future__ import annotations

import uuid

from pydantic import BaseModel


class ReviewItemResponse(BaseModel):
    lesson_id: uuid.UUID
    title: str
    course_id: uuid.UUID
    course_title: str
    source: str
    review_status: str  # "approved" | "pending" | "hidden"
    exercise_count: int
    quiz_count: int


class UsageResponse(BaseModel):
    ai_lessons: int
    pending: int
    approved: int
    hidden: int
    ai_exercises: int
    ai_quizzes: int
