"""AI provider port (application layer).

The rest of the system depends on this abstraction, never on a provider SDK, so
the model — or the whole provider — can be swapped via configuration. The
concrete implementation lives in ``app/infrastructure/ai``.

All requests are constructed server-side; learner-supplied text (code, a
question) is carried in dedicated fields so the provider can fence it against
prompt injection.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

# --------------------------------------------------------------------------- #
# Errors
# --------------------------------------------------------------------------- #


class AIProviderError(RuntimeError):
    """Base error for any AI provider failure."""


class AINotConfiguredError(AIProviderError):
    """Raised when the provider has no API key configured."""


class AIQuotaError(AIProviderError):
    """Raised when the provider rejects the request for quota reasons (429).

    ``retry_after`` carries the provider's suggested wait (seconds), when known.
    """

    def __init__(self, message: str, retry_after: float | None = None) -> None:
        super().__init__(message)
        self.retry_after = retry_after


# --------------------------------------------------------------------------- #
# Requests / responses
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class TeachRequest:
    topic: str
    level: str = "beginner"
    lesson_content: str = ""
    question: str = ""


@dataclass(frozen=True)
class TutorRequest:
    language: str
    code: str
    prompt: str = ""
    question: str = ""
    level: str = "beginner"


@dataclass(frozen=True)
class GenerateLessonRequest:
    topic: str
    level: str = "beginner"


@dataclass(frozen=True)
class GenerateExerciseRequest:
    topic: str
    language: str = "python"
    level: str = "beginner"


@dataclass(frozen=True)
class GeneratePlacementRequest:
    language: str
    mcq_count: int = 5


@dataclass(frozen=True)
class GenerateSyllabusRequest:
    language: str
    level: str = "beginner"
    lesson_count: int = 8


@dataclass(frozen=True)
class GenerateLessonPackRequest:
    topic: str
    language: str = "python"
    level: str = "beginner"
    exercise_count: int = 2
    quiz_question_count: int = 3


@dataclass(frozen=True)
class GenerateLessonBatchRequest:
    """Generate several complete lessons in a single request (saves API calls)."""

    language: str
    level: str = "beginner"
    count: int = 3
    exercise_count: int = 2
    quiz_question_count: int = 3
    # Titles of lessons already generated, so the batch continues coherently.
    prior_titles: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class AIResponse:
    """Free-form text answer (teacher explanation / tutor feedback)."""

    text: str
    model: str
    total_tokens: int = 0


@dataclass(frozen=True)
class GeneratedLesson:
    title: str
    content: str
    model: str
    total_tokens: int = 0


@dataclass(frozen=True)
class GeneratedExercise:
    title: str
    prompt: str
    starter_code: str
    reference_solution: str
    test_spec: dict[str, Any] = field(default_factory=dict)
    model: str = ""
    total_tokens: int = 0


@dataclass(frozen=True)
class GeneratedSyllabus:
    topics: list[str] = field(default_factory=list)
    model: str = ""
    total_tokens: int = 0


@dataclass(frozen=True)
class GeneratedLessonPack:
    """A full lesson: Markdown content, exercises, and a quiz.

    ``exercises`` items: ``{"title", "prompt", "starter_code", "reference_solution",
    "test_spec"}``. ``quiz``: ``{"title", "questions": [{"prompt", "choices":
    [{"text", "is_correct"}]}]}``.
    """

    title: str = ""
    content: str = ""
    exercises: list[dict[str, Any]] = field(default_factory=list)
    quiz: dict[str, Any] = field(default_factory=dict)
    model: str = ""
    total_tokens: int = 0


@dataclass(frozen=True)
class GeneratedLessonBatch:
    """Several lessons from one call. Each item has the shape of a lesson pack:
    ``{"title", "content", "exercises": [...], "quiz": {...}}``."""

    lessons: list[dict[str, Any]] = field(default_factory=list)
    model: str = ""
    total_tokens: int = 0


@dataclass(frozen=True)
class GeneratedPlacement:
    """A placement assessment: multiple-choice questions + coding tasks.

    ``mcqs`` items: ``{"prompt", "choices": [{"text", "is_correct"}]}``.
    ``coding`` items: ``{"prompt", "language", "starter_code", "test_spec",
    "reference_solution"}``.
    """

    mcqs: list[dict[str, Any]] = field(default_factory=list)
    coding: list[dict[str, Any]] = field(default_factory=list)
    model: str = ""
    total_tokens: int = 0


# --------------------------------------------------------------------------- #
# Port
# --------------------------------------------------------------------------- #


class AIProvider(Protocol):
    def teach(self, request: TeachRequest) -> AIResponse: ...

    def tutor(self, request: TutorRequest) -> AIResponse: ...

    def generate_lesson(self, request: GenerateLessonRequest) -> GeneratedLesson: ...

    def generate_exercise(self, request: GenerateExerciseRequest) -> GeneratedExercise: ...

    def generate_placement(self, request: GeneratePlacementRequest) -> GeneratedPlacement: ...

    def generate_syllabus(self, request: GenerateSyllabusRequest) -> GeneratedSyllabus: ...

    def generate_lesson_pack(
        self, request: GenerateLessonPackRequest
    ) -> GeneratedLessonPack: ...

    def generate_lesson_batch(
        self, request: GenerateLessonBatchRequest
    ) -> GeneratedLessonBatch: ...
