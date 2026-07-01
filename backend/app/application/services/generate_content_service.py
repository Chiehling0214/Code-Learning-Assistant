"""AI content generation.

Generation is just another author: it asks the :class:`AIProvider` for content
and writes it through the existing ``ContentService`` / ``ExerciseService`` into
the ``lessons`` / ``exercises`` tables (marked ``source="ai"``), so serving and
grading are unchanged. Generated exercises are self-verified — the reference
solution must pass the generated ``test_spec`` via the Sprint 4 Judge0 path —
before they are published.
"""

from __future__ import annotations

import re
import uuid

from app.application.ports.ai_provider import (
    AIProvider,
    GenerateExerciseRequest,
    GenerateLessonRequest,
)
from app.application.services.ai_usage import AIUsageGuard
from app.application.services.content_service import ContentService
from app.application.services.execution_service import ExecutionService
from app.application.services.exercise_service import ExerciseService
from app.domain.entities import Exercise, Lesson


def _slugify(title: str) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-") or "generated"
    # Short suffix keeps slugs unique without a DB round-trip.
    return f"{base[:48]}-{uuid.uuid4().hex[:6]}"


class GenerateContentService:
    def __init__(
        self,
        provider: AIProvider,
        content: ContentService,
        exercises: ExerciseService,
        execution: ExecutionService,
        usage: AIUsageGuard,
    ) -> None:
        self._provider = provider
        self._content = content
        self._exercises = exercises
        self._execution = execution
        self._usage = usage

    def generate_lesson(
        self,
        *,
        user_id: uuid.UUID,
        course_id: uuid.UUID,
        topic: str,
        level: str,
        order_index: int = 0,
    ) -> Lesson:
        self._usage.check(user_id)
        generated = self._provider.generate_lesson(
            GenerateLessonRequest(topic=topic, level=level)
        )
        lesson = self._content.create_lesson(
            course_id=course_id,
            title=generated.title,
            slug=_slugify(generated.title),
            order_index=order_index,
            content=generated.content,
            source="ai",
        )
        self._usage.record(
            user_id, kind="generate", model=generated.model, total_tokens=generated.total_tokens
        )
        return lesson

    def generate_exercise(
        self,
        *,
        user_id: uuid.UUID,
        lesson_id: uuid.UUID,
        topic: str,
        language: str,
        level: str,
    ) -> Exercise:
        self._usage.check(user_id)
        generated = self._provider.generate_exercise(
            GenerateExerciseRequest(topic=topic, language=language, level=level)
        )

        # Quality gate: the exercise must ship runnable tests, and its reference
        # solution must pass them, before we persist it.
        if not (generated.test_spec or {}).get("cases"):
            raise ValueError("Generated exercise has no test cases")
        verdict, _ = self._execution.grade(
            code=generated.reference_solution,
            language=language,
            test_spec=generated.test_spec,
        )
        if verdict != "passed":
            raise ValueError(
                f"Generated exercise failed self-verification (verdict: {verdict})"
            )

        exercise = self._exercises.create_exercise(
            lesson_id=lesson_id,
            language=language,
            title=generated.title,
            slug=_slugify(generated.title),
            prompt=generated.prompt,
            starter_code=generated.starter_code,
            test_spec=generated.test_spec,
            source="ai",
        )
        self._usage.record(
            user_id, kind="generate", model=generated.model, total_tokens=generated.total_tokens
        )
        return exercise
