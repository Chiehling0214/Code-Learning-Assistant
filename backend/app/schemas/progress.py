"""Pydantic schemas for progress analytics."""

from __future__ import annotations

import uuid

from pydantic import BaseModel


class CourseProgress(BaseModel):
    course_id: uuid.UUID
    title: str
    slug: str
    total: int
    completed: int
    percent: int


class ProgressResponse(BaseModel):
    courses: list[CourseProgress]
    total: int
    completed: int
    percent: int
    streak: int


class MarkCompleteResponse(BaseModel):
    status: str = "completed"
