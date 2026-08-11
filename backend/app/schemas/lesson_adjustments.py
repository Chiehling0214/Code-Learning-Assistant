from __future__ import annotations

import uuid

from pydantic import BaseModel, Field


class LessonAdjustmentCreate(BaseModel):
    preset: str = Field(pattern="^(simpler|examples|challenge|practical)$")
    instructions: str = Field(default="", max_length=1000)


class LessonAdjustmentPreviewResponse(BaseModel):
    adjustment_id: uuid.UUID
    lesson_id: uuid.UUID
    title: str
    content: str
