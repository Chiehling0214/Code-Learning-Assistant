"""Pydantic schemas for language tracks."""

from __future__ import annotations

import uuid

from pydantic import BaseModel


class TrackResponse(BaseModel):
    id: uuid.UUID
    language_id: uuid.UUID
    language_name: str
    language_slug: str
    level: str | None = None
    status: str


class AddTrackRequest(BaseModel):
    language_id: uuid.UUID
