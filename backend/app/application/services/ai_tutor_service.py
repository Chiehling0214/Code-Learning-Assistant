"""AI Tutor use case: hint/feedback on a learner's current code (not the answer)."""

from __future__ import annotations

import uuid

from app.application.ports.ai_provider import AIProvider, AIResponse, TutorRequest
from app.application.services.ai_usage import AIUsageGuard
from app.domain.repositories import ExerciseRepository


class AITutorService:
    def __init__(
        self, provider: AIProvider, exercises: ExerciseRepository, usage: AIUsageGuard
    ) -> None:
        self._provider = provider
        self._exercises = exercises
        self._usage = usage

    def tutor(
        self,
        *,
        user_id: uuid.UUID,
        exercise_id: uuid.UUID,
        code: str,
        question: str,
        level: str,
    ) -> AIResponse:
        exercise = self._exercises.get_by_id(exercise_id)
        if exercise is None:
            raise LookupError(f"Exercise {exercise_id} not found")

        self._usage.check(user_id)
        response = self._provider.tutor(
            TutorRequest(
                language=exercise.language,
                code=code,
                prompt=exercise.prompt,
                question=question,
                level=level,
            )
        )
        self._usage.record(
            user_id, kind="tutor", model=response.model, total_tokens=response.total_tokens
        )
        return response

    def tutor_stream(
        self,
        *,
        user_id: uuid.UUID,
        exercise_id: uuid.UUID,
        code: str,
        question: str,
        level: str,
    ):
        """Streaming variant of :meth:`tutor` — yields text chunks.

        Checks run eagerly (mappable to HTTP errors); usage is recorded when the
        stream completes (counts toward the plan's daily tutor cap).
        """
        exercise = self._exercises.get_by_id(exercise_id)
        if exercise is None:
            raise LookupError(f"Exercise {exercise_id} not found")
        self._usage.check(user_id)

        request = TutorRequest(
            language=exercise.language,
            code=code,
            prompt=exercise.prompt,
            question=question,
            level=level,
        )

        def stream():
            yield from self._provider.tutor_stream(request)
            self._usage.record(user_id, kind="tutor", model="stream", total_tokens=0)

        return stream()
