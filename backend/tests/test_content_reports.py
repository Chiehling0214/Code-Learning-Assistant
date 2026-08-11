import uuid
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

from app.application.services.ai_usage import AIUsageGuard
from app.application.services.content_report_service import ContentReportService
from app.core.config import Settings


def test_regenerate_lesson_records_usage_and_requires_review_again(
    fakes: SimpleNamespace,
) -> None:
    admin_id = uuid.uuid4()
    language = fakes.languages.create(name="Python", slug="python")
    track = fakes.tracks.create(user_id=admin_id, language_id=language.id)
    fakes.tracks.set_level(track.id, "beginner")
    course = fakes.courses.create(
        language_id=language.id,
        title="Python — Beginner",
        slug="python-beginner",
        description=None,
        track_id=track.id,
    )
    lesson = fakes.lessons.create(
        course_id=course.id,
        title="Variables",
        slug="variables",
        order_index=0,
        content="Old content",
        source="ai",
        review_status="approved",
    )
    usage = AIUsageGuard(
        fakes.interactions,
        Settings(ai_rate_limit_per_minute=10, ai_daily_limit=100),
    )
    service = ContentReportService(
        object(),
        fakes.versions,
        fakes.lessons,
        fakes.exercises,
        fakes.quizzes,
        fakes.courses,
        fakes.languages,
        fakes.tracks,
        fakes.ai,
        usage,
        version_limit=2,
    )

    service.regenerate(
        item_type="lesson",
        item_id=lesson.id,
        admin_user_id=admin_id,
        instructions="Use a visual analogy and add one practical example.",
    )

    regenerated = fakes.lessons.get_by_id(lesson.id)
    assert regenerated is not None
    assert regenerated.content == "# Variables\n\nGenerated content."
    assert regenerated.review_status == "pending"
    assert fakes.ai.last_lesson_request.topic == "Variables"
    assert (
        fakes.ai.last_lesson_request.instructions
        == "Use a visual analogy and add one practical example."
    )
    since = datetime.now(UTC) - timedelta(minutes=1)
    assert fakes.interactions.count_since(admin_id, since, kind="regenerate_content") == 1
    versions = fakes.versions.list_for_item("lesson", lesson.id)
    assert len(versions) == 1
    assert versions[0].snapshot["content"] == "Old content"

    service.restore(versions[0].id, admin_id)

    restored = fakes.lessons.get_by_id(lesson.id)
    assert restored is not None
    assert restored.content == "Old content"
    assert restored.review_status == "pending"
    assert len(fakes.versions.list_for_item("lesson", lesson.id)) == 2

    service.restore(versions[0].id, admin_id)
    assert len(fakes.versions.list_for_item("lesson", lesson.id)) == 2
