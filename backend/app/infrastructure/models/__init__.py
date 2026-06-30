"""SQLAlchemy ORM models.

Importing this package registers every model on the shared metadata, which
Alembic relies on for autogeneration.
"""

from app.infrastructure.models.models import (
    Choice,
    Course,
    Exercise,
    Lesson,
    ProgrammingLanguage,
    Question,
    Quiz,
    QuizAttempt,
    StudentProfile,
    Submission,
    User,
)

__all__ = [
    "User",
    "StudentProfile",
    "ProgrammingLanguage",
    "Course",
    "Lesson",
    "Exercise",
    "Submission",
    "Quiz",
    "Question",
    "Choice",
    "QuizAttempt",
]
