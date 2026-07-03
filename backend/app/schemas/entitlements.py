"""Schemas for plan entitlements (Sprint 13)."""

from __future__ import annotations

from pydantic import BaseModel


class EntitlementsResponse(BaseModel):
    plan: str  # "free" | "pro"
    max_languages: int
    tutor_daily: int
    generations_daily: int
    languages_used: int
    tutor_used_today: int
    generations_used_today: int
