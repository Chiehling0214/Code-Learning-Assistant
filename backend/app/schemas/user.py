"""Pydantic schemas for the current-user and profile endpoints."""

from __future__ import annotations

import uuid

from pydantic import BaseModel, Field


class CurrentUserResponse(BaseModel):
    """DB-backed identity of the authenticated user."""

    id: uuid.UUID
    uid: str
    email: str | None = None
    display_name: str | None = None
    is_admin: bool = False
    # True once the learner has chosen at least one language track (Sprint 9).
    onboarded: bool = False


class ProfileResponse(BaseModel):
    display_name: str | None = None
    email: str | None = None
    skill_level: str
    is_admin: bool = False


class UpdateProfileRequest(BaseModel):
    display_name: str | None = Field(default=None, max_length=255)
    skill_level: str | None = Field(default=None, max_length=32)
