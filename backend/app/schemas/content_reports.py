from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ContentReportCreate(BaseModel):
    item_type: str = Field(pattern="^(lesson|exercise|quiz)$")
    item_id: uuid.UUID
    reason: str = Field(min_length=1, max_length=40)
    details: str = Field(default="", max_length=1000)


class ContentReportResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    item_type: str
    item_id: uuid.UUID
    reason: str
    details: str
    status: str
    created_at: datetime
    updated_at: datetime


class ContentReportStatus(BaseModel):
    status: str = Field(pattern="^(open|resolved|dismissed)$")


class ContentRegenerateRequest(BaseModel):
    instructions: str = Field(default="", max_length=1000)


class ContentVersionResponse(BaseModel):
    id: uuid.UUID
    item_type: str
    item_id: uuid.UUID
    created_by: uuid.UUID | None
    created_at: datetime
    snapshot: dict[str, Any]


class ContentVersionHistoryResponse(BaseModel):
    current_snapshot: dict[str, Any]
    versions: list[ContentVersionResponse]
