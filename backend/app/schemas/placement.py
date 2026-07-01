"""Pydantic schemas for the placement test.

The learner-facing shapes deliberately omit answer keys (`is_correct`) and the
coding `test_spec` / `reference_solution`.
"""

from __future__ import annotations

import uuid
from typing import Any

from pydantic import BaseModel


class PlacementChoice(BaseModel):
    id: str
    text: str


class PlacementMCQ(BaseModel):
    id: str
    prompt: str
    choices: list[PlacementChoice]


class PlacementCoding(BaseModel):
    id: str
    prompt: str
    language: str
    starter_code: str


class PlacementResponse(BaseModel):
    track_id: uuid.UUID
    status: str  # "ready" | "completed"
    level: str | None = None
    mcqs: list[PlacementMCQ]
    coding: list[PlacementCoding]


class PlacementSubmitRequest(BaseModel):
    # question_id -> choice_id, and coding_task_id -> source code.
    mcq_answers: dict[str, str] = {}
    code: dict[str, str] = {}


class PlacementSubmitResponse(BaseModel):
    level: str
    percent: int
    breakdown: dict[str, Any]
