"""Pydantic schemas for practice drills + topic mastery (Sprint 16)."""

from __future__ import annotations

import uuid

from pydantic import BaseModel, Field


class PracticeGenerateRequest(BaseModel):
    language: str = Field(min_length=1, max_length=64)  # language slug
    # Omit to train the learner's weakest topic.
    topic: str | None = Field(default=None, max_length=200)
    difficulty: str | None = Field(default=None, pattern="^(beginner|intermediate|advanced)$")


class PracticeExerciseResponse(BaseModel):
    exercise_id: uuid.UUID
    title: str
    topic: str
    language: str


class PracticeHistoryEntry(BaseModel):
    exercise_id: uuid.UUID
    title: str
    topic: str
    language: str
    last_verdict: str | None = None


class TopicMasteryResponse(BaseModel):
    topic: str
    attempts: int
    correct: int
    correct_rate: float
    level: str  # "weak" | "ok" | "strong"


class MasteryResponse(BaseModel):
    language: str
    topics: list[TopicMasteryResponse]
