"""Pydantic schemas for AI curriculum generation."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class GenerationJobResponse(BaseModel):
    id: uuid.UUID
    track_id: uuid.UUID
    status: str  # "pending" | "running" | "done" | "error"
    total: int
    completed: int
    course_id: uuid.UUID | None = None
    error: str | None = None


# ----- Continuous learning: extend + in-course chat (Sprint 12) -----


class AddedLesson(BaseModel):
    id: uuid.UUID
    title: str
    slug: str
    order_index: int


class ExtensionStatusResponse(BaseModel):
    course_id: uuid.UUID
    lesson_count: int
    completion_percent: int
    can_extend: bool


class ExtendRequest(BaseModel):
    # Optional focus topic; when omitted the syllabus is simply continued.
    topic: str | None = Field(default=None, max_length=500)
    # How many lessons to add (bounded server-side to curriculum_extend_max).
    count: int | None = Field(default=None, ge=1, le=20)


class ExtendResponse(BaseModel):
    added: list[AddedLesson]
    lesson_count: int


class ChatMessageResponse(BaseModel):
    id: uuid.UUID
    role: str  # "user" | "assistant"
    content: str
    created_at: datetime


class ChatListResponse(BaseModel):
    messages: list[ChatMessageResponse]


class ChatSendRequest(BaseModel):
    message: str = Field(min_length=1, max_length=500)
    # Optional number of lessons to generate for this request.
    count: int | None = Field(default=None, ge=1, le=20)


class ChatSendResponse(BaseModel):
    reply: ChatMessageResponse
    added: list[AddedLesson]
