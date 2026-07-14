"""On-demand practice drills (Sprint 16).

Generates a standalone exercise on a chosen topic — or on the learner's weakest
topic — into a hidden per-track practice container (``courses.kind="practice"``,
one lesson per topic), so the existing run/submit/tutor/grading machinery works
unchanged while the drills stay out of the dashboard, Today, and course progress.
"""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass

from app.application.ports.ai_provider import AIProvider, GenerateExerciseRequest
from app.application.services.ai_usage import AIUsageGuard
from app.application.services.mastery_service import MasteryService
from app.domain.entities import Exercise
from app.domain.repositories import (
    CourseRepository,
    ExerciseRepository,
    LanguageRepository,
    LanguageTrackRepository,
    LessonRepository,
    SubmissionRepository,
)

_LEVELS = {"beginner", "intermediate", "advanced"}


def _slug(text: str) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-") or "item"
    return f"{base[:48]}-{uuid.uuid4().hex[:6]}"


@dataclass(frozen=True)
class PracticeHistoryItem:
    exercise_id: uuid.UUID
    title: str
    topic: str
    language: str
    last_verdict: str | None  # "passed" | "failed" | "error" | None (not tried)


class PracticeService:
    def __init__(
        self,
        provider: AIProvider,
        courses: CourseRepository,
        lessons: LessonRepository,
        exercises: ExerciseRepository,
        submissions: SubmissionRepository,
        languages: LanguageRepository,
        tracks: LanguageTrackRepository,
        mastery: MasteryService,
        usage: AIUsageGuard,
    ) -> None:
        self._provider = provider
        self._courses = courses
        self._lessons = lessons
        self._exercises = exercises
        self._submissions = submissions
        self._languages = languages
        self._tracks = tracks
        self._mastery = mastery
        self._usage = usage

    # ----- helpers -----

    def _owned_track(self, user_id: uuid.UUID, language_slug: str):
        language = self._languages.get_by_slug(language_slug)
        if language is None:
            raise LookupError(f"Language '{language_slug}' not found")
        track = self._tracks.get_by_user_and_language(user_id, language.id)
        if track is None:
            raise LookupError("You are not studying this language")
        return language, track

    def _practice_course(self, language, track):  # noqa: ANN001 - domain entities
        """Get or create the hidden practice container for this track."""
        for course in self._courses.list_by_track_ids([track.id]):
            if course.kind == "practice":
                return course
        return self._courses.create(
            language_id=language.id,
            title=f"Practice — {language.name}",
            slug=_slug(f"practice-{language.slug}"),
            description="On-demand practice drills.",
            track_id=track.id,
            kind="practice",
        )

    def _topic_lesson(self, course_id: uuid.UUID, topic: str):
        """One lesson per topic inside the practice course (mastery buckets by title)."""
        existing = self._lessons.list_by_course(course_id)
        for lesson in existing:
            if lesson.title.strip().lower() == topic.strip().lower():
                return lesson
        return self._lessons.create(
            course_id=course_id,
            title=topic,
            slug=_slug(topic),
            order_index=len(existing),
            content="",
        )

    # ----- use cases -----

    def generate(
        self,
        *,
        user_id: uuid.UUID,
        language_slug: str,
        topic: str | None = None,
        difficulty: str | None = None,
    ) -> Exercise:
        """Generate one drill; with no topic, target the learner's weakest one."""
        language, track = self._owned_track(user_id, language_slug)
        self._usage.check(user_id)

        resolved_topic = (topic or "").strip()
        if not resolved_topic:
            resolved_topic = (
                self._mastery.weakest_topic(user_id=user_id, language_slug=language_slug)
                or f"{language.name} fundamentals"
            )
        level = difficulty if difficulty in _LEVELS else (track.level or "beginner")

        generated = self._provider.generate_exercise(
            GenerateExerciseRequest(topic=resolved_topic, language=language.slug, level=level)
        )
        course = self._practice_course(language, track)
        lesson = self._topic_lesson(course.id, resolved_topic)
        exercise = self._exercises.create(
            lesson_id=lesson.id,
            language=language.slug,
            title=generated.title,
            slug=_slug(generated.title),
            prompt=generated.prompt,
            starter_code=generated.starter_code,
            test_spec=generated.test_spec,
            source="ai",
        )
        self._usage.record(
            user_id, kind="generate", model=generated.model, total_tokens=generated.total_tokens
        )
        return exercise

    def topic_of(self, exercise: Exercise) -> str:
        """The topic bucket a drill belongs to (its container lesson's title)."""
        lesson = self._lessons.get_by_id(exercise.lesson_id)
        return lesson.title if lesson else ""

    def history(
        self, *, user_id: uuid.UUID, language_slug: str | None = None
    ) -> list[PracticeHistoryItem]:
        """Past drills (newest first) with the latest submission verdict."""
        track_ids = [t.id for t in self._tracks.list_by_user(user_id)]
        items: list[tuple[PracticeHistoryItem, object]] = []
        for course in self._courses.list_by_track_ids(track_ids):
            if course.kind != "practice":
                continue
            for lesson in self._lessons.list_by_course(course.id):
                for ex in self._exercises.list_by_lesson(lesson.id):
                    if language_slug and ex.language != language_slug:
                        continue
                    subs = self._submissions.list_for_user_and_exercise(user_id, ex.id)
                    last = subs[0].status if subs else None
                    items.append(
                        (
                            PracticeHistoryItem(
                                exercise_id=ex.id,
                                title=ex.title,
                                topic=lesson.title,
                                language=ex.language,
                                last_verdict=last,
                            ),
                            ex.created_at,
                        )
                    )
        items.sort(key=lambda pair: pair[1], reverse=True)
        return [item for item, _ in items]
