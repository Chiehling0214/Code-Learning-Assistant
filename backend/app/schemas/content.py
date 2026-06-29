"""Pydantic schemas for the content domain (languages, courses, lessons)."""

from __future__ import annotations

import uuid

from pydantic import BaseModel, Field

# --------------------------------------------------------------------------- #
# Responses
# --------------------------------------------------------------------------- #


class LanguageResponse(BaseModel):
    id: uuid.UUID
    name: str
    slug: str


class CourseResponse(BaseModel):
    id: uuid.UUID
    language_id: uuid.UUID
    title: str
    slug: str
    description: str | None = None


class LessonSummary(BaseModel):
    id: uuid.UUID
    title: str
    slug: str
    order_index: int


class CourseDetailResponse(CourseResponse):
    lessons: list[LessonSummary] = Field(default_factory=list)


class LessonResponse(BaseModel):
    id: uuid.UUID
    course_id: uuid.UUID
    title: str
    slug: str
    order_index: int
    content: str


# --------------------------------------------------------------------------- #
# Admin requests
# --------------------------------------------------------------------------- #


class LanguageCreate(BaseModel):
    name: str = Field(min_length=1, max_length=64)
    slug: str = Field(min_length=1, max_length=64)


class LanguageUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=64)
    slug: str | None = Field(default=None, max_length=64)


class CourseCreate(BaseModel):
    language_id: uuid.UUID
    title: str = Field(min_length=1, max_length=255)
    slug: str = Field(min_length=1, max_length=255)
    description: str | None = None


class CourseUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=255)
    slug: str | None = Field(default=None, max_length=255)
    description: str | None = None


class LessonCreate(BaseModel):
    course_id: uuid.UUID
    title: str = Field(min_length=1, max_length=255)
    slug: str = Field(min_length=1, max_length=255)
    order_index: int = 0
    content: str = ""


class LessonUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=255)
    slug: str | None = Field(default=None, max_length=255)
    order_index: int | None = None
    content: str | None = None
