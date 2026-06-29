"""Pydantic response schemas for health endpoints."""

from pydantic import BaseModel


class LivenessResponse(BaseModel):
    status: str = "ok"
    service: str
    version: str


class ReadinessResponse(BaseModel):
    status: str
    database: str
