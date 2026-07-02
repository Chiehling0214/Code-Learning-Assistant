"""In-course chat (Sprint 12).

A learner chats inside a course — "teach me decorators" — and the AI appends a
matching lesson (with exercises + a quiz) to the course, then replies with a
short summary of what it added. The exchange is persisted so the conversation
survives reloads. Content generation reuses the Sprint 11 pipeline via
:class:`~app.application.services.curriculum_service.CurriculumService`.
"""

from __future__ import annotations

import uuid

from app.application.services.ai_usage import AIUsageGuard
from app.application.services.curriculum_service import CurriculumService
from app.core.logging import get_logger
from app.domain.entities import CourseChatMessage, Lesson
from app.domain.repositories import CourseChatRepository

logger = get_logger(__name__)


class CourseChatService:
    def __init__(
        self,
        chats: CourseChatRepository,
        curriculum: CurriculumService,
        usage: AIUsageGuard,
    ) -> None:
        self._chats = chats
        self._curriculum = curriculum
        self._usage = usage

    def list_messages(
        self, *, course_id: uuid.UUID, user_id: uuid.UUID
    ) -> list[CourseChatMessage]:
        # Ownership check (raises LookupError when not the learner's course).
        self._curriculum.get_owned_course(course_id=course_id, user_id=user_id)
        return self._chats.list_by_course_and_user(course_id, user_id)

    def send(
        self,
        *,
        course_id: uuid.UUID,
        user_id: uuid.UUID,
        message: str,
        count: int | None = None,
    ) -> tuple[CourseChatMessage, list[Lesson]]:
        """Record the learner's message, generate targeted content, and reply.

        The recent conversation is passed to the generator as context, so a vague
        follow-up ("I need more") continues the most recent topic rather than
        producing generic lessons. Returns ``(assistant_message, added_lessons)``.
        """
        self._curriculum.get_owned_course(course_id=course_id, user_id=user_id)
        text = (message or "").strip()
        if not text:
            raise ValueError("Message cannot be empty")
        # Enforce the per-user AI budget before spending a generation call.
        self._usage.check(user_id)

        # Build a short transcript (recent turns + this message) as the focus so
        # the model can resolve the concrete subject from context.
        history = self._chats.list_by_course_and_user(course_id, user_id)[-6:]
        lines = [
            f"{'Learner' if m.role == 'user' else 'Assistant'}: {m.content}" for m in history
        ]
        lines.append(f"Learner: {text}")
        focus = "\n".join(lines)

        self._chats.create(course_id=course_id, user_id=user_id, role="user", content=text)
        added = self._curriculum.extend_course(
            course_id=course_id, user_id=user_id, focus=focus, count=count
        )

        if added:
            titles = ", ".join(f"“{ln.title}”" for ln in added)
            reply = (
                f"I added {len(added)} new lesson{'s' if len(added) != 1 else ''} to your "
                f"course: {titles}. Each comes with exercises and a quiz — happy learning!"
            )
        else:
            reply = (
                "I couldn't generate that right now — please try rephrasing your "
                "request in a moment."
            )
        assistant = self._chats.create(
            course_id=course_id, user_id=user_id, role="assistant", content=reply
        )
        return assistant, added
