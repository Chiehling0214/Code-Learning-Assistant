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
    """Raised when the provider rejects the request for quota reasons (429)."""


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


# --------------------------------------------------------------------------- #
# Port
# --------------------------------------------------------------------------- #


class AIProvider(Protocol):
    def teach(self, request: TeachRequest) -> AIResponse: ...

    def tutor(self, request: TutorRequest) -> AIResponse: ...

    def generate_lesson(self, request: GenerateLessonRequest) -> GeneratedLesson: ...

    def generate_exercise(self, request: GenerateExerciseRequest) -> GeneratedExercise: ...
