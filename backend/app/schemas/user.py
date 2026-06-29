"""Pydantic schemas for the current-user endpoint."""

from pydantic import BaseModel


class CurrentUserResponse(BaseModel):
    uid: str
    email: str | None = None
    is_admin: bool = False
