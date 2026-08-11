import uuid
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

from fastapi.testclient import TestClient


def _owned_lesson(client: TestClient, fakes: SimpleNamespace):
    user = client.get("/api/v1/me").json()
    language = fakes.languages.create(name="Python", slug="python")
    track = fakes.tracks.create(
        user_id=uuid.UUID(user["id"]),
        language_id=language.id,
    )
    fakes.tracks.set_level(track.id, "intermediate")
    course = fakes.courses.create(
        language_id=language.id,
        title="Python — Intermediate",
        slug="python-intermediate-adjustment",
        description=None,
        track_id=track.id,
    )
    lesson = fakes.lessons.create(
        course_id=course.id,
        title="List comprehensions",
        slug="list-comprehensions-adjustment",
        order_index=0,
        content="Original lesson content",
        source="ai",
        review_status="approved",
    )
    return uuid.UUID(user["id"]), lesson


def test_learner_previews_then_applies_lesson_adjustment(
    client: TestClient, fakes: SimpleNamespace
) -> None:
    user_id, lesson = _owned_lesson(client, fakes)

    preview = client.post(
        f"/api/v1/lessons/{lesson.id}/adjustments/preview",
        json={
            "preset": "examples",
            "instructions": "Use a shopping-cart example.",
        },
    )

    assert preview.status_code == 200, preview.text
    body = preview.json()
    assert body["title"] == lesson.title
    assert "Generated content" in body["content"]
    assert fakes.lessons.get_by_id(lesson.id).content == "Original lesson content"
    assert fakes.ai.last_lesson_request.topic == lesson.title
    assert "shopping-cart" in fakes.ai.last_lesson_request.instructions
    assert fakes.interactions.count_since(
        user_id,
        datetime.now(UTC) - timedelta(minutes=1),
        kind="generate",
    ) == 1

    applied = client.post(
        f"/api/v1/lessons/{lesson.id}/adjustments/{body['adjustment_id']}/apply"
    )

    assert applied.status_code == 200, applied.text
    assert applied.json()["content"] == body["content"]
    assert fakes.lessons.get_by_id(lesson.id).review_status == "pending"
    versions = fakes.versions.list_for_item("lesson", lesson.id)
    assert versions[0].snapshot["content"] == "Original lesson content"


def test_learner_cannot_adjust_another_users_lesson(
    client: TestClient, fakes: SimpleNamespace
) -> None:
    client.get("/api/v1/me")
    other = fakes.users.create(firebase_uid="other-adjustment-user", email="other@example.com")
    language = fakes.languages.create(name="Java", slug="java")
    track = fakes.tracks.create(user_id=other.id, language_id=language.id)
    course = fakes.courses.create(
        language_id=language.id,
        title="Other course",
        slug="other-adjustment-course",
        description=None,
        track_id=track.id,
    )
    lesson = fakes.lessons.create(
        course_id=course.id,
        title="Other lesson",
        slug="other-adjustment-lesson",
        order_index=0,
        content="Private content",
    )

    response = client.post(
        f"/api/v1/lessons/{lesson.id}/adjustments/preview",
        json={"preset": "simpler"},
    )

    assert response.status_code == 404


def test_stale_lesson_adjustment_is_not_applied(
    client: TestClient, fakes: SimpleNamespace
) -> None:
    _, lesson = _owned_lesson(client, fakes)
    preview = client.post(
        f"/api/v1/lessons/{lesson.id}/adjustments/preview",
        json={"preset": "practical"},
    ).json()
    fakes.lessons.update(
        lesson.id,
        title=None,
        slug=None,
        order_index=None,
        content="Content changed elsewhere",
    )

    response = client.post(
        f"/api/v1/lessons/{lesson.id}/adjustments/{preview['adjustment_id']}/apply"
    )

    assert response.status_code == 409
    assert fakes.lessons.get_by_id(lesson.id).content == "Content changed elsewhere"
