"""Per-topic mastery (Sprint 16).

Aggregates the learner's history — exercise verdicts (progress events) and quiz
attempts — into a per-topic strength picture for a language. The topic key is
the **lesson title** the item belongs to (practice drills are created under a
lesson named after the requested topic, so they feed the same buckets).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

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


@dataclass(frozen=True)
class AbilityAssessment:
    current_level: str
    evidence_level: str
    attempts: int
    correct: int
    accuracy: int | None
    source: str
    next_evaluation: str
    weighted_accuracy: int | None = None
    confidence: str = "low"
    sample_status: str = "insufficient"
    exercise_weight: float = 0
    quiz_weight: float = 0


@dataclass(frozen=True)
class Evidence:
    item_id: uuid.UUID
    kind: str
    score: float
    occurred_at: datetime


def score_evidence(evidence: list[Evidence]) -> tuple[int | None, float, float, str, str]:
    now = datetime.now(UTC)
    per_item: dict[uuid.UUID, list[Evidence]] = {}
    for entry in evidence:
        per_item.setdefault(entry.item_id, []).append(entry)
    earned = exercise_weight = quiz_weight = 0.0
    for entries in per_item.values():
        for retry_index, entry in enumerate(sorted(entries, key=lambda x: x.occurred_at)):
            age_days = max(0, (now - entry.occurred_at).days)
            recency = max(0.55, 1 - age_days / 365)
            retry = 1 / (1 + retry_index * 0.65)
            base = 2.0 if entry.kind == "exercise" else 1.0
            weight = base * recency * retry
            earned += max(0, min(entry.score, 1)) * weight
            if entry.kind == "exercise":
                exercise_weight += weight
            else:
                quiz_weight += weight
    total = exercise_weight + quiz_weight
    accuracy = round(earned / total * 100) if total else None
    if total < 3:
        return accuracy, exercise_weight, quiz_weight, "low", "insufficient"
    if total < 12:
        return accuracy, exercise_weight, quiz_weight, "medium", "developing"
    return accuracy, exercise_weight, quiz_weight, "high", "sufficient"


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

    def ability_assessment(
        self, *, user_id: uuid.UUID, language_slug: str
    ) -> AbilityAssessment:
        """Explain the evidence behind the system-owned skill level.

        This is intentionally read-only. The official track level is updated by
        the placement flow and again when a full course cycle is completed.
        """
        language = self._languages.get_by_slug(language_slug)
        if language is None:
            raise LookupError(f"Language '{language_slug}' not found")
        track = self._tracks.get_by_user_and_language(user_id, language.id)
        if track is None:
            raise LookupError("Language track not found")

        topics = self.snapshot(user_id=user_id, language_slug=language_slug)
        attempts = sum(topic.attempts for topic in topics)
        correct = sum(topic.correct for topic in topics)
        course_ids = {
            course.id
            for course in self._courses.list_by_track_ids([track.id])
            if course.language_id == language.id
        }
        exercise_ids: set[uuid.UUID] = set()
        quiz_totals: dict[uuid.UUID, int] = {}
        for course_id in course_ids:
            for lesson in self._lessons.list_by_course(course_id):
                exercise_ids.update(ex.id for ex in self._exercises.list_by_lesson(lesson.id))
                for quiz in self._quizzes.list_by_lesson(lesson.id):
                    quiz_totals[quiz.id] = len(quiz.questions)
        evidence: list[Evidence] = []
        for event in self._progress.list_for_user(user_id):
            if event.item_type == "exercise" and event.item_id in exercise_ids:
                evidence.append(
                    Evidence(
                        event.item_id,
                        "exercise",
                        1.0 if event.status == "passed" else 0.0,
                        event.completed_at,
                    )
                )
            elif event.item_type == "quiz" and event.item_id in quiz_totals:
                total = quiz_totals[event.item_id]
                if total:
                    evidence.append(
                        Evidence(
                            event.item_id,
                            "quiz",
                            (event.score or 0) / total,
                            event.completed_at,
                        )
                    )
        weighted_accuracy, exercise_weight, quiz_weight, confidence, sample_status = (
            score_evidence(evidence)
        )
        raw_accuracy = round(correct / attempts * 100) if attempts else None
        if weighted_accuracy is None or sample_status == "insufficient":
            evidence_level = track.level or "beginner"
        elif weighted_accuracy >= 85:
            evidence_level = "advanced"
        elif weighted_accuracy >= 60:
            evidence_level = "intermediate"
        else:
            evidence_level = "beginner"

        return AbilityAssessment(
            current_level=track.level or "beginner",
            evidence_level=evidence_level,
            attempts=attempts,
            correct=correct,
            accuracy=raw_accuracy,
            source="course performance" if attempts else "placement assessment",
            next_evaluation=(
                "Your level is recalculated after every current course is completed; "
                "the next three courses use that result."
            ),
            weighted_accuracy=weighted_accuracy,
            confidence=confidence,
            sample_status=sample_status,
            exercise_weight=round(exercise_weight, 1),
            quiz_weight=round(quiz_weight, 1),
        )
