"""Schemas for the admin AI-content review console (Sprint 13)."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ReviewItemResponse(BaseModel):
    lesson_id: uuid.UUID
    title: str
    course_id: uuid.UUID
    course_title: str
    source: str
    review_status: str  # "approved" | "pending" | "hidden"
    exercise_count: int
    quiz_count: int


class ReviewContentPageResponse(BaseModel):
    items: list[ReviewItemResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class ReviewCourseOptionResponse(BaseModel):
    course_id: uuid.UUID
    title: str
    total: int
    pending: int


class ReviewUserOptionResponse(BaseModel):
    user_id: uuid.UUID
    email: str
    display_name: str | None
    course_count: int
    lesson_count: int
    pending: int


class ReviewExercisePreview(BaseModel):
    id: uuid.UUID
    title: str
    language: str
    prompt: str
    starter_code: str
    test_spec: dict[str, Any] = Field(default_factory=dict)


class ReviewChoicePreview(BaseModel):
    text: str
    is_correct: bool


class ReviewQuestionPreview(BaseModel):
    prompt: str
    explanation: str
    choices: list[ReviewChoicePreview] = Field(default_factory=list)


class ReviewQuizPreview(BaseModel):
    id: uuid.UUID
    title: str
    questions: list[ReviewQuestionPreview] = Field(default_factory=list)


class ReviewPreviewResponse(BaseModel):
    lesson_id: uuid.UUID
    title: str
    content: str
    exercises: list[ReviewExercisePreview] = Field(default_factory=list)
    quizzes: list[ReviewQuizPreview] = Field(default_factory=list)


class BulkReviewResponse(BaseModel):
    course_id: uuid.UUID
    reviewed: int


class UsageResponse(BaseModel):
    ai_lessons: int
    pending: int
    approved: int
    hidden: int
    ai_exercises: int
    ai_quizzes: int


class AdminGenerationJobResponse(BaseModel):
    id: uuid.UUID
    user_email: str
    language: str
    kind: str
    status: str
    completed: int
    total: int
    attempt_count: int
    max_attempts: int
    error: str | None
    cancel_requested: bool
    created_at: datetime
    updated_at: datetime
