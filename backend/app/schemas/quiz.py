"""Pydantic schemas for quizzes.

The learner-facing ``QuizResponse`` deliberately omits ``is_correct`` so answer
keys never leak; the admin authoring schemas carry it.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

# --------------------------------------------------------------------------- #
# Learner-facing responses (no answer keys)
# --------------------------------------------------------------------------- #


class ChoiceResponse(BaseModel):
    """A choice as shown to learners — note the absence of ``is_correct``."""

    id: uuid.UUID
    text: str
    order_index: int


class QuestionResponse(BaseModel):
    id: uuid.UUID
    prompt: str
    type: str
    order_index: int
    choices: list[ChoiceResponse]


class QuizResponse(BaseModel):
    id: uuid.UUID
    lesson_id: uuid.UUID
    title: str
    slug: str
    description: str | None = None
    questions: list[QuestionResponse]


class QuizSummary(BaseModel):
    id: uuid.UUID
    title: str
    slug: str


# --------------------------------------------------------------------------- #
# Submission / grading
# --------------------------------------------------------------------------- #


class QuizSubmitRequest(BaseModel):
    """Maps each ``question_id`` to the learner's selected ``choice_id``."""

    answers: dict[uuid.UUID, uuid.UUID]


class QuestionResult(BaseModel):
    question_id: uuid.UUID
    correct: bool
    selected_choice_id: uuid.UUID | None = None
    correct_choice_id: uuid.UUID | None = None
    explanation: str = ""


class QuizSubmitResponse(BaseModel):
    attempt_id: uuid.UUID
    score: int
    total: int
    results: list[QuestionResult]


class AttemptResponse(BaseModel):
    id: uuid.UUID
    quiz_id: uuid.UUID
    score: int
    total: int
    created_at: datetime


# --------------------------------------------------------------------------- #
# Admin authoring requests
# --------------------------------------------------------------------------- #


class QuizCreate(BaseModel):
    lesson_id: uuid.UUID
    title: str = Field(min_length=1, max_length=255)
    slug: str = Field(min_length=1, max_length=255)
    description: str | None = None


class ChoiceCreate(BaseModel):
    text: str = Field(min_length=1)
    is_correct: bool = False


class QuestionCreate(BaseModel):
    prompt: str = Field(min_length=1)
    type: str = Field(default="single", max_length=16)
    order_index: int = 0
    choices: list[ChoiceCreate] = Field(min_length=2)
    explanation: str = ""
