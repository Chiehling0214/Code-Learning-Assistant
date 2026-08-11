"""Learner content reports and admin-scoped AI regeneration."""

from __future__ import annotations

import uuid

from app.application.ports.ai_provider import (
    AIProvider,
    GenerateExerciseRequest,
    GenerateLessonPackRequest,
    GenerateLessonRequest,
)
from app.application.services.ai_usage import AIUsageGuard
from app.domain.entities import ContentReport, ContentVersion
from app.domain.repositories import (
    ContentReportRepository,
    ContentVersionRepository,
    CourseRepository,
    ExerciseRepository,
    LanguageRepository,
    LanguageTrackRepository,
    LessonRepository,
    QuizRepository,
)

_ITEM_TYPES = {"lesson", "exercise", "quiz"}
_STATUSES = {"open", "resolved", "dismissed"}


class ContentReportService:
    def __init__(
        self,
        reports: ContentReportRepository,
        versions: ContentVersionRepository,
        lessons: LessonRepository,
        exercises: ExerciseRepository,
        quizzes: QuizRepository,
        courses: CourseRepository,
        languages: LanguageRepository,
        tracks: LanguageTrackRepository,
        provider: AIProvider,
        usage: AIUsageGuard,
        version_limit: int = 20,
    ) -> None:
        self._reports = reports
        self._versions = versions
        self._lessons = lessons
        self._exercises = exercises
        self._quizzes = quizzes
        self._courses = courses
        self._languages = languages
        self._tracks = tracks
        self._provider = provider
        self._usage = usage
        self._version_limit = max(1, version_limit)

    def _find(self, item_type: str, item_id: uuid.UUID):  # noqa: ANN202
        if item_type == "lesson":
            return self._lessons.get_by_id(item_id)
        if item_type == "exercise":
            return self._exercises.get_by_id(item_id)
        if item_type == "quiz":
            return self._quizzes.get_by_id(item_id)
        raise ValueError("Unsupported content type")

    @staticmethod
    def _snapshot(item_type: str, item) -> dict:  # noqa: ANN001
        if item_type == "lesson":
            return {"title": item.title, "content": item.content}
        if item_type == "exercise":
            return {
                "title": item.title,
                "prompt": item.prompt,
                "starter_code": item.starter_code,
                "test_spec": item.test_spec,
            }
        if item_type == "quiz":
            return {
                "title": item.title,
                "questions": [
                    {
                        "prompt": question.prompt,
                        "type": question.type,
                        "order_index": question.order_index,
                        "explanation": question.explanation,
                        "choices": [
                            {
                                "text": choice.text,
                                "is_correct": choice.is_correct,
                                "order_index": choice.order_index,
                            }
                            for choice in question.choices
                        ],
                    }
                    for question in item.questions
                ],
            }
        raise ValueError("Unsupported content type")

    def _apply_snapshot(self, item_type: str, item_id: uuid.UUID, snapshot: dict) -> None:
        if item_type == "lesson":
            self._lessons.update(
                item_id,
                title=str(snapshot.get("title", "")) or None,
                slug=None,
                order_index=None,
                content=str(snapshot.get("content", "")),
            )
            return
        if item_type == "exercise":
            self._exercises.update_generated(
                item_id,
                title=str(snapshot.get("title", "")),
                prompt=str(snapshot.get("prompt", "")),
                starter_code=str(snapshot.get("starter_code", "")),
                test_spec=dict(snapshot.get("test_spec") or {}),
            )
            return
        if item_type == "quiz":
            self._quizzes.replace_generated(
                item_id,
                title=str(snapshot.get("title", "")),
                questions=list(snapshot.get("questions") or []),
            )
            return
        raise ValueError("Unsupported content type")

    def _save_version(
        self,
        *,
        item_type: str,
        item_id: uuid.UUID,
        snapshot: dict,
        created_by: uuid.UUID,
    ) -> ContentVersion:
        version = self._versions.create(
            item_type=item_type,
            item_id=item_id,
            snapshot=snapshot,
            created_by=created_by,
        )
        self._versions.prune(item_type, item_id, self._version_limit)
        return version

    def report(
        self,
        *,
        user_id: uuid.UUID,
        item_type: str,
        item_id: uuid.UUID,
        reason: str,
        details: str,
    ) -> ContentReport:
        if item_type not in _ITEM_TYPES:
            raise ValueError("Unsupported content type")
        if self._find(item_type, item_id) is None:
            raise LookupError("Content not found")
        return self._reports.create(
            user_id=user_id,
            item_type=item_type,
            item_id=item_id,
            reason=reason,
            details=details.strip(),
        )

    def list_reports(self, status: str | None = None) -> list[ContentReport]:
        return self._reports.list_all(status)

    def set_status(self, report_id: uuid.UUID, status: str) -> ContentReport:
        if status not in _STATUSES:
            raise ValueError("Invalid report status")
        return self._reports.set_status(report_id, status)

    def list_versions(self, item_type: str, item_id: uuid.UUID) -> list[ContentVersion]:
        if self._find(item_type, item_id) is None:
            raise LookupError("Content not found")
        return self._versions.list_for_item(item_type, item_id)

    def current_snapshot(self, item_type: str, item_id: uuid.UUID) -> dict:
        item = self._find(item_type, item_id)
        if item is None:
            raise LookupError("Content not found")
        return self._snapshot(item_type, item)

    def restore(self, version_id: uuid.UUID, admin_user_id: uuid.UUID) -> None:
        version = self._versions.get_by_id(version_id)
        if version is None:
            raise LookupError("Content version not found")
        item = self._find(version.item_type, version.item_id)
        if item is None:
            raise LookupError("Content not found")
        lesson = (
            item
            if version.item_type == "lesson"
            else self._lessons.get_by_id(item.lesson_id)
        )
        if lesson is None:
            raise LookupError("Content context not found")
        self._save_version(
            item_type=version.item_type,
            item_id=version.item_id,
            snapshot=self._snapshot(version.item_type, item),
            created_by=admin_user_id,
        )
        self._apply_snapshot(version.item_type, version.item_id, version.snapshot)
        self._lessons.set_review_status(lesson.id, "pending")

    def regenerate(
        self,
        *,
        item_type: str,
        item_id: uuid.UUID,
        admin_user_id: uuid.UUID,
        instructions: str = "",
    ) -> None:
        item = self._find(item_type, item_id)
        if item is None:
            raise LookupError("Content not found")
        lesson = item if item_type == "lesson" else self._lessons.get_by_id(item.lesson_id)
        course = self._courses.get_by_id(lesson.course_id) if lesson else None
        language = self._languages.get_by_id(course.language_id) if course else None
        if lesson is None or course is None or language is None:
            raise LookupError("Content context not found")
        track = self._tracks.get_by_id(course.track_id) if course.track_id else None
        level = track.level if track and track.level else "beginner"
        self._usage.check(admin_user_id)
        self._save_version(
            item_type=item_type,
            item_id=item_id,
            snapshot=self._snapshot(item_type, item),
            created_by=admin_user_id,
        )
        if item_type == "lesson":
            generated = self._provider.generate_lesson(
                GenerateLessonRequest(
                    topic=lesson.title,
                    level=level,
                    instructions=instructions.strip(),
                )
            )
            self._lessons.update(
                lesson.id,
                title=None,
                slug=None,
                order_index=None,
                content=generated.content,
            )
        elif item_type == "exercise":
            generated = self._provider.generate_exercise(
                GenerateExerciseRequest(
                    topic=item.title,
                    language=language.slug,
                    level=level,
                    instructions=instructions.strip(),
                )
            )
            self._exercises.update_generated(
                item.id,
                title=generated.title,
                prompt=generated.prompt,
                starter_code=generated.starter_code,
                test_spec=generated.test_spec,
            )
        else:
            generated = self._provider.generate_lesson_pack(
                GenerateLessonPackRequest(
                    topic=f"{lesson.title} — {item.title}",
                    language=language.slug,
                    level=level,
                    exercise_count=0,
                    quiz_question_count=max(3, len(item.questions)),
                    instructions=instructions.strip(),
                )
            )
            quiz = generated.quiz or {}
            self._quizzes.replace_generated(
                item.id,
                title=str(quiz.get("title", item.title)),
                questions=list(quiz.get("questions") or []),
            )
        # Regenerated content has changed since its last admin review, so the
        # enclosing lesson must be reviewed again before it can be marked as such.
        self._lessons.set_review_status(lesson.id, "pending")
        self._usage.record(
            admin_user_id,
            kind="regenerate_content",
            model=generated.model,
            total_tokens=generated.total_tokens,
        )
