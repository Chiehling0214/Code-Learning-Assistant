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
        context: str = "",
    ) -> AIResponse:
        """Explain a topic/lesson/question.

        ``context`` is optional caller-supplied material (e.g. the placement or
        quiz questions under review, plus the learner's answers/code) so the
        teacher can reference the exact items the learner asks about. The
        provider fences it like lesson content.
        """
        lesson_content = ""
        resolved_topic = topic
        if lesson_id is not None:
            lesson = self._lessons.get_by_id(lesson_id)
            if lesson is None:
                raise LookupError(f"Lesson {lesson_id} not found")
            lesson_content = lesson.content
            resolved_topic = topic or lesson.title
        if context.strip():
            lesson_content = f"{lesson_content}\n\n{context}" if lesson_content else context

        if not resolved_topic and not question and not context.strip():
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

    def teach_stream(
        self,
        *,
        user_id: uuid.UUID,
        lesson_id: uuid.UUID | None,
        topic: str,
        question: str,
        level: str,
        context: str = "",
    ):
        """Streaming variant of :meth:`teach` — yields text chunks.

        Lookups and rate-limit checks run eagerly (so callers can map them to
        HTTP errors before streaming starts); usage is recorded once the stream
        finishes (token count unavailable mid-stream, recorded as 0).
        """
        lesson_content = ""
        resolved_topic = topic
        if lesson_id is not None:
            lesson = self._lessons.get_by_id(lesson_id)
            if lesson is None:
                raise LookupError(f"Lesson {lesson_id} not found")
            lesson_content = lesson.content
            resolved_topic = topic or lesson.title
        if context.strip():
            lesson_content = f"{lesson_content}\n\n{context}" if lesson_content else context
        if not resolved_topic and not question and not context.strip():
            raise ValueError("Provide a topic, a lesson, or a question")
        self._usage.check(user_id)

        request = TeachRequest(
            topic=resolved_topic, level=level, lesson_content=lesson_content, question=question
        )

        def stream():
            yield from self._provider.teach_stream(request)
            self._usage.record(user_id, kind="teacher", model="stream", total_tokens=0)

        return stream()
