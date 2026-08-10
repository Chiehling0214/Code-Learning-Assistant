"""Schemas for synced exercise drafts."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class DraftSaveRequest(BaseModel):
    code: str = Field(max_length=200_000)


class DraftResponse(BaseModel):
    exercise_id: uuid.UUID
    code: str
    updated_at: datetime
