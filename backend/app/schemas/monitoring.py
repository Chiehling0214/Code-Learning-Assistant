from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class FrontendErrorCreate(BaseModel):
    kind: str = Field(default="frontend_error", pattern="^(frontend_error|unhandled_rejection)$")
    message: str = Field(min_length=1, max_length=2000)
    stack: str = Field(default="", max_length=6000)
    path: str = Field(default="", max_length=500)


class OperationalEventResponse(BaseModel):
    id: uuid.UUID
    category: str
    level: str
    message: str
    details: dict[str, Any]
    created_at: datetime


class MonitoringSummaryResponse(BaseModel):
    window_hours: int
    counts: dict[str, int]
    recent: list[OperationalEventResponse]
