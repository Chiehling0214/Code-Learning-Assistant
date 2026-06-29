"""SQLAlchemy ORM models.

Importing this package registers every model on the shared metadata, which
Alembic relies on for autogeneration.
"""

from app.infrastructure.models.models import (
    Course,
    ProgrammingLanguage,
    StudentProfile,
    User,
)

__all__ = ["User", "StudentProfile", "ProgrammingLanguage", "Course"]
