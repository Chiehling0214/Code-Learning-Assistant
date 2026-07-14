"""Per-topic mastery (Sprint 16).

Aggregates the learner's history — exercise verdicts (progress events) and quiz
attempts — into a per-topic strength picture for a language. The topic key is
the **lesson title** the item belongs to (practice drills are created under a
lesson named after the requested topic, so they feed the same buckets).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from app.domain.repositories import (
    CourseRepository,
    ExerciseRepository,
    LanguageRepository,
    LanguageTrackRepository,
    LessonRepository,
    ProgressRepository,
    QuizAttemptRepository,
    QuizRepository,
)

_WEAK_BELOW = 0.5
_STRONG_FROM = 0.8


@dataclass(frozen=True)
class TopicMastery:
    topic: str
    attempts: int
    correct: int
    correct_rate: float
    level: str  # "weak" | "ok" | "strong"
    # The course lesson this topic lives in (None when it only exists as
    # practice drills) — lets the UI link back to the lesson for revision.
    lesson_id: uuid.UUID | None = None


def _level_for(rate: float) -> str:
    if rate < _WEAK_BELOW:
        return "weak"
    if rate >= _STRONG_FROM:
        return "strong"
    return "ok"


class MasteryService:
    def __init__(
        self,
        courses: CourseRepository,
        lessons: LessonRepository,
        exercises: ExerciseRepository,
        quizzes: QuizRepository,
        progress: ProgressRepository,
        attempts: QuizAttemptRepository,
        tracks: LanguageTrackRepository,
        languages: LanguageRepository,
    ) -> None:
        self._courses = courses
        self._lessons = lessons
        self._exercises = exercises
        self._quizzes = quizzes
        self._progress = progress
        self._attempts = attempts
        self._tracks = tracks
        self._languages = languages

    def snapshot(self, *, user_id: uuid.UUID, language_slug: str) -> list[TopicMastery]:
        """Per-topic mastery for one of the learner's languages, weakest first."""
        language = self._languages.get_by_slug(language_slug)
        if language is None:
            raise LookupError(f"Language '{language_slug}' not found")
        track_ids = [t.id for t in self._tracks.list_by_user(user_id)]

        # Exercise verdicts from the progress event log (latest event per item
        # counts every attempt; we tally passed vs failed occurrences).
        exercise_events: dict[uuid.UUID, list[str]] = {}
        for event in self._progress.list_for_user(user_id):
            if event.item_type == "exercise":
                exercise_events.setdefault(event.item_id, []).append(event.status)

        buckets: dict[str, dict[str, int]] = {}
        lesson_ids: dict[str, uuid.UUID] = {}

        def bucket(topic: str) -> dict[str, int]:
            return buckets.setdefault(topic, {"attempts": 0, "correct": 0})

        for course in self._courses.list_by_track_ids(track_ids):
            if course.language_id != language.id:
                continue
            for lesson in self._lessons.list_by_course(course.id):
                topic = lesson.title
                # Remember where the topic is taught (real courses only —
                # practice containers are empty shells not worth linking to).
                if course.kind != "practice" and topic not in lesson_ids:
                    lesson_ids[topic] = lesson.id
                for ex in self._exercises.list_by_lesson(lesson.id):
                    for status in exercise_events.get(ex.id, []):
                        b = bucket(topic)
                        b["attempts"] += 1
                        b["correct"] += 1 if status == "passed" else 0
                for quiz in self._quizzes.list_by_lesson(lesson.id):
                    for attempt in self._attempts.list_for_user_and_quiz(user_id, quiz.id):
                        total = int((attempt.answers or {}).get("total", 0))
                        if total <= 0:
                            continue
                        b = bucket(topic)
                        b["attempts"] += total
                        b["correct"] += attempt.score

        result = [
            TopicMastery(
                topic=topic,
                attempts=b["attempts"],
                correct=b["correct"],
                correct_rate=round(b["correct"] / b["attempts"], 2),
                level=_level_for(b["correct"] / b["attempts"]),
                lesson_id=lesson_ids.get(topic),
            )
            for topic, b in buckets.items()
            if b["attempts"] > 0
        ]
        return sorted(result, key=lambda t: (t.correct_rate, -t.attempts))

    def weakest_topic(self, *, user_id: uuid.UUID, language_slug: str) -> str | None:
        """The learner's weakest topic with real history, or None."""
        snapshot = self.snapshot(user_id=user_id, language_slug=language_slug)
        for entry in snapshot:
            if entry.level != "strong":
                return entry.topic
        return snapshot[0].topic if snapshot else None
