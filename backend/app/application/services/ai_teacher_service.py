"""AI Teacher use case: explain/expand lesson content for a learner's level."""

from __future__ import annotations

import uuid

from app.application.ports.ai_provider import AIProvider, AIResponse, TeachRequest
from app.application.services.ai_usage import AIUsageGuard
from app.domain.repositories import LessonRepository


class AITeacherService:
    def __init__(
        self, provider: AIProvider, lessons: LessonRepository, usage: AIUsageGuard
    ) -> None:
        self._provider = provider
        self._lessons = lessons
        self._usage = usage

    def teach(
        self,
        *,
        user_id: uuid.UUID,
        lesson_id: uuid.UUID | None,
        topic: str,
        question: str,
        level: str,
    ) -> AIResponse:
        lesson_content = ""
        resolved_topic = topic
        if lesson_id is not None:
            lesson = self._lessons.get_by_id(lesson_id)
            if lesson is None:
                raise LookupError(f"Lesson {lesson_id} not found")
            lesson_content = lesson.content
            resolved_topic = topic or lesson.title

        if not resolved_topic and not question:
            raise ValueError("Provide a topic, a lesson, or a question")

        self._usage.check(user_id)
        response = self._provider.teach(
            TeachRequest(
                topic=resolved_topic,
                level=level,
                lesson_content=lesson_content,
                question=question,
            )
        )
        self._usage.record(
            user_id, kind="teacher", model=response.model, total_tokens=response.total_tokens
        )
        return response
