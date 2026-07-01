"""Pydantic schemas for the AI endpoints."""

from __future__ import annotations

import uuid

from pydantic import BaseModel, Field


class TeacherRequest(BaseModel):
    lesson_id: uuid.UUID | None = None
    topic: str = ""
    question: str = ""


class TutorRequest(BaseModel):
    exercise_id: uuid.UUID
    code: str = ""
    question: str = ""


class AIAnswerResponse(BaseModel):
    answer: str
    model: str
    total_tokens: int = 0


class GenerateRequest(BaseModel):
    kind: str = Field(pattern="^(lesson|exercise)$")
    topic: str = Field(min_length=1)
    level: str = "beginner"
    # For a lesson: the course it belongs to. For an exercise: the lesson.
    course_id: uuid.UUID | None = None
    lesson_id: uuid.UUID | None = None
    language: str = "python"
    order_index: int = 0


class GeneratedLessonResponse(BaseModel):
    kind: str = "lesson"
    id: uuid.UUID
    course_id: uuid.UUID
    title: str
    slug: str
    source: str


class GeneratedExerciseResponse(BaseModel):
    kind: str = "exercise"
    id: uuid.UUID
    lesson_id: uuid.UUID
    title: str
    slug: str
    language: str
    source: str
