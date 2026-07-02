"""SQLAlchemy ORM models.

Importing this package registers every model on the shared metadata, which
Alembic relies on for autogeneration.
"""

from app.infrastructure.models.models import (
    AIInteraction,
    Choice,
    Course,
    CourseChatMessage,
    Exercise,
    GenerationJob,
    LanguageTrack,
    Lesson,
    PlacementAssessment,
    ProgrammingLanguage,
    ProgressEvent,
    Question,
    Quiz,
    QuizAttempt,
    StudentProfile,
    Submission,
    Subscription,
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
    "AIInteraction",
    "ProgressEvent",
    "Subscription",
    "LanguageTrack",
    "PlacementAssessment",
    "GenerationJob",
    "CourseChatMessage",
]
