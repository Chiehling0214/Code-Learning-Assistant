"""API tests for the AI endpoints (provider mocked — no network).

Covers Teacher/Tutor responses, per-user rate limiting, the admin generation
guard, AI content landing in the normal tables with ``source="ai"`` (and served
by the existing endpoints), and the self-verification gate on generated
exercises.
"""

import uuid
from types import SimpleNamespace

from fastapi.testclient import TestClient


def _seed_course_lesson(fakes: SimpleNamespace):
    lang = fakes.languages.create(name="Python", slug="python")
    course = fakes.courses.create(
        language_id=lang.id, title="Basics", slug="basics", description=None
    )
    lesson = fakes.lessons.create(
        course_id=course.id, title="Loops", slug="loops", order_index=1, content="# Loops"
    )
    return course, lesson


# ----- teacher / tutor -----


def test_teacher_returns_explanation(client: TestClient) -> None:
    res = client.post("/api/v1/ai/teacher", json={"topic": "recursion"})
    assert res.status_code == 200, res.text
    body = res.json()
    assert "recursion" in body["answer"]
    assert body["model"] == "fake-model"


def test_teacher_uses_lesson_content(client: TestClient, fakes: SimpleNamespace) -> None:
    _, lesson = _seed_course_lesson(fakes)
    res = client.post("/api/v1/ai/teacher", json={"lesson_id": str(lesson.id)})
    assert res.status_code == 200, res.text
    # Topic falls back to the lesson title.
    assert "Loops" in res.json()["answer"]


def test_tutor_references_submitted_code(client: TestClient, fakes: SimpleNamespace) -> None:
    exercise = fakes.exercises.create(
        lesson_id=uuid.uuid4(),
        language="python",
        title="Sum",
        slug="sum",
        prompt="Add",
        starter_code="",
        test_spec={},
    )
    res = client.post(
        "/api/v1/ai/tutor",
        json={"exercise_id": str(exercise.id), "code": "total = a + b"},
    )
    assert res.status_code == 200, res.text
    answer = res.json()["answer"]
    assert "total = a + b" in answer  # feedback references their actual code


def test_tutor_unknown_exercise_404(client: TestClient) -> None:
    res = client.post(
        "/api/v1/ai/tutor", json={"exercise_id": str(uuid.uuid4()), "code": "x"}
    )
    assert res.status_code == 404


def test_rate_limit_returns_429(client: TestClient) -> None:
    # _AI_SETTINGS caps at 5 requests/minute; the 6th should be rejected.
    for _ in range(5):
        assert client.post("/api/v1/ai/teacher", json={"topic": "x"}).status_code == 200
    res = client.post("/api/v1/ai/teacher", json={"topic": "x"})
    assert res.status_code == 429


# ----- admin content generation -----


def test_non_admin_cannot_generate(client: TestClient, fakes: SimpleNamespace) -> None:
    _, lesson = _seed_course_lesson(fakes)
    res = client.post(
        "/api/v1/admin/ai/generate",
        json={"kind": "exercise", "lesson_id": str(lesson.id), "topic": "loops"},
    )
    assert res.status_code == 403


def test_generate_lesson_writes_ai_sourced_row(
    admin_client: TestClient, fakes: SimpleNamespace
) -> None:
    course, _ = _seed_course_lesson(fakes)
    res = admin_client.post(
        "/api/v1/admin/ai/generate",
        json={"kind": "lesson", "course_id": str(course.id), "topic": "dictionaries"},
    )
    assert res.status_code == 201, res.text
    body = res.json()
    assert body["source"] == "ai"
    # Landed in the lessons table and is served by the normal course endpoint.
    detail = admin_client.get(f"/api/v1/courses/{course.slug}").json()
    assert any(ln["id"] == body["id"] for ln in detail["lessons"])


def test_generate_exercise_self_verifies_then_persists(
    admin_client: TestClient, fakes: SimpleNamespace
) -> None:
    _, lesson = _seed_course_lesson(fakes)
    # Default FakeCodeRunner returns Accepted with stdout "" == expected "" -> passes.
    res = admin_client.post(
        "/api/v1/admin/ai/generate",
        json={"kind": "exercise", "lesson_id": str(lesson.id), "topic": "loops"},
    )
    assert res.status_code == 201, res.text
    body = res.json()
    assert body["source"] == "ai"
    # Served by the normal exercise endpoint.
    assert admin_client.get(f"/api/v1/exercises/{body['id']}").status_code == 200


def test_generate_exercise_rejected_when_self_verify_fails(
    admin_client: TestClient, fakes: SimpleNamespace
) -> None:
    _, lesson = _seed_course_lesson(fakes)
    # Make the reference solution fail its own tests (runtime error verdict).
    fakes.runner.set(status_id=11, status="Runtime Error")
    res = admin_client.post(
        "/api/v1/admin/ai/generate",
        json={"kind": "exercise", "lesson_id": str(lesson.id), "topic": "loops"},
    )
    assert res.status_code == 400
    assert "self-verification" in res.json()["detail"]
