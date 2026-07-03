"""API tests for the admin AI-content review console (Sprint 13)."""

from types import SimpleNamespace

from fastapi.testclient import TestClient


def _ai_lesson(fakes: SimpleNamespace):
    lang = fakes.languages.create(name="Python", slug="python")
    course = fakes.courses.create(
        language_id=lang.id, title="Basics", slug="basics", description=None
    )
    lesson = fakes.lessons.create(
        course_id=course.id,
        title="Decorators",
        slug="decorators",
        order_index=0,
        content="# Decorators",
        source="ai",
        review_status="pending",
    )
    return course, lesson


def test_review_requires_admin(client: TestClient) -> None:
    # The plain client's stub user is not an admin.
    assert client.get("/api/v1/admin/content").status_code == 403


def test_admin_lists_ai_content(admin_client: TestClient, fakes: SimpleNamespace) -> None:
    _, lesson = _ai_lesson(fakes)
    res = admin_client.get("/api/v1/admin/content?source=ai")
    assert res.status_code == 200, res.text
    ids = [row["lesson_id"] for row in res.json()]
    assert str(lesson.id) in ids


def test_hide_excludes_from_serving_then_approve_restores(
    admin_client: TestClient, fakes: SimpleNamespace
) -> None:
    _, lesson = _ai_lesson(fakes)
    # Served while visible.
    assert admin_client.get(f"/api/v1/lessons/{lesson.id}").status_code == 200

    hide = admin_client.post(f"/api/v1/admin/content/lessons/{lesson.id}/hide")
    assert hide.status_code == 200, hide.text
    assert hide.json()["review_status"] == "hidden"
    # Hidden content is no longer served to learners.
    assert admin_client.get(f"/api/v1/lessons/{lesson.id}").status_code == 404

    approve = admin_client.post(f"/api/v1/admin/content/lessons/{lesson.id}/approve")
    assert approve.status_code == 200
    assert approve.json()["review_status"] == "approved"
    assert admin_client.get(f"/api/v1/lessons/{lesson.id}").status_code == 200


def test_hide_unknown_lesson_404(admin_client: TestClient) -> None:
    import uuid

    assert (
        admin_client.post(f"/api/v1/admin/content/lessons/{uuid.uuid4()}/hide").status_code
        == 404
    )


def test_admin_usage_counts(admin_client: TestClient, fakes: SimpleNamespace) -> None:
    _ai_lesson(fakes)
    usage = admin_client.get("/api/v1/admin/usage").json()
    assert usage["ai_lessons"] >= 1
    assert usage["pending"] >= 1
