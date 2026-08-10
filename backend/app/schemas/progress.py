"""Pydantic schemas for progress analytics."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class LearningItem(BaseModel):
    item_type: Literal["course", "lesson", "exercise", "quiz"]
    item_id: uuid.UUID
    title: str
    path: str


class ResumePoint(LearningItem):
    course_id: uuid.UUID
    course_title: str
    course_slug: str
    updated_at: datetime | None = None


class CompletedItem(BaseModel):
    item_type: Literal["lesson", "exercise", "quiz"]
    item_id: uuid.UUID


class CourseProgress(BaseModel):
    course_id: uuid.UUID
    title: str
    slug: str
    total: int
    completed: int
    percent: int
    next_item: LearningItem | None = None
    completed_items: list[CompletedItem] = Field(default_factory=list)


class ProgressResponse(BaseModel):
    courses: list[CourseProgress]
    total: int
    completed: int
    percent: int
    streak: int
    resume: ResumePoint | None = None


class RecordActivityRequest(BaseModel):
    item_type: Literal["course", "lesson", "exercise", "quiz"]
    item_id: uuid.UUID


class MarkCompleteResponse(BaseModel):
    status: str = "completed"
