"""Learner-controlled, preview-first lesson adjustments."""

from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass

from app.application.ports.ai_provider import (
    AIProvider,
    AIProviderError,
    GenerateLessonRequest,
)
from app.application.services.ai_usage import AIUsageGuard
from app.application.services.entitlement_service import EntitlementService
from app.domain.entities import LanguageTrack, Lesson
from app.domain.repositories import (
    ContentVersionRepository,
    CourseRepository,
    LanguageTrackRepository,
    LessonRepository,
)

_PRESET_INSTRUCTIONS = {
    "simpler": "Explain the same topic more simply, with shorter steps and less jargon.",
    "examples": "Keep the same topic but add clearer, practical examples.",
    "challenge": "Keep the same topic but make the explanation more challenging and nuanced.",
    "practical": "Keep the same topic but focus more on practical, real-world use.",
}


class StaleLessonAdjustmentError(RuntimeError):
    """Raised when the original lesson changed after a preview was generated."""


@dataclass(frozen=True)
class LessonAdjustmentPreview:
    adjustment_id: uuid.UUID
    lesson_id: uuid.UUID
    title: str
    content: str


class LessonAdjustmentService:
    def __init__(
        self,
        provider: AIProvider,
        lessons: LessonRepository,
        courses: CourseRepository,
        tracks: LanguageTrackRepository,
        versions: ContentVersionRepository,
        usage: AIUsageGuard,
        entitlements: EntitlementService,
        version_limit: int = 20,
    ) -> None:
        self._provider = provider
        self._lessons = lessons
        self._courses = courses
        self._tracks = tracks
        self._versions = versions
        self._usage = usage
        self._entitlements = entitlements
        self._version_limit = max(1, version_limit)

    @staticmethod
    def _content_digest(content: str) -> str:
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def _owned_lesson(
        self, user_id: uuid.UUID, lesson_id: uuid.UUID
    ) -> tuple[Lesson, LanguageTrack]:
        lesson = self._lessons.get_by_id(lesson_id)
        course = self._courses.get_by_id(lesson.course_id) if lesson else None
        track = self._tracks.get_by_id(course.track_id) if course and course.track_id else None
        if lesson is None or course is None or track is None or track.user_id != user_id:
            raise LookupError("Lesson not found")
        if lesson.review_status == "hidden":
            raise LookupError("Lesson not found")
        return lesson, track

    def preview(
        self,
        *,
        user_id: uuid.UUID,
        lesson_id: uuid.UUID,
        preset: str,
        instructions: str = "",
    ) -> LessonAdjustmentPreview:
        lesson, track = self._owned_lesson(user_id, lesson_id)
        preset_instruction = _PRESET_INSTRUCTIONS.get(preset)
        if preset_instruction is None:
            raise ValueError("Unsupported adjustment type")

        self._entitlements.check_generation(user_id)
        self._usage.check(user_id)
        guidance = preset_instruction
        if instructions.strip():
            guidance += " Additional detail requested by the learner: " + instructions.strip()
        generated = self._provider.generate_lesson(
            GenerateLessonRequest(
                topic=lesson.title,
                level=track.level or "beginner",
                instructions=guidance,
            )
        )
        if not generated.content.strip():
            raise AIProviderError("AI returned an empty lesson adjustment")

        draft = self._versions.create(
            item_type="lesson_draft",
            item_id=lesson.id,
            snapshot={
                "title": lesson.title,
                "content": generated.content,
                "base_digest": self._content_digest(lesson.content),
            },
            created_by=user_id,
        )
        self._versions.prune("lesson_draft", lesson.id, 3)
        self._usage.record(
            user_id,
            kind="generate",
            model=generated.model,
            total_tokens=generated.total_tokens,
        )
        return LessonAdjustmentPreview(
            adjustment_id=draft.id,
            lesson_id=lesson.id,
            title=lesson.title,
            content=generated.content,
        )

    def apply(
        self,
        *,
        user_id: uuid.UUID,
        lesson_id: uuid.UUID,
        adjustment_id: uuid.UUID,
    ) -> Lesson:
        lesson, _ = self._owned_lesson(user_id, lesson_id)
        draft = self._versions.get_by_id(adjustment_id)
        if (
            draft is None
            or draft.item_type != "lesson_draft"
            or draft.item_id != lesson.id
            or draft.created_by != user_id
        ):
            raise LookupError("Lesson adjustment not found")
        if draft.snapshot.get("base_digest") != self._content_digest(lesson.content):
            raise StaleLessonAdjustmentError(
                "This lesson changed after the preview was generated. Create a new preview."
            )
        content = str(draft.snapshot.get("content", "")).strip()
        if not content:
            raise ValueError("Lesson adjustment is empty")

        self._versions.create(
            item_type="lesson",
            item_id=lesson.id,
            snapshot={"title": lesson.title, "content": lesson.content},
            created_by=user_id,
        )
        self._versions.prune("lesson", lesson.id, self._version_limit)
        self._lessons.update(
            lesson.id,
            title=None,
            slug=None,
            order_index=None,
            content=content,
        )
        return self._lessons.set_review_status(lesson.id, "pending")
