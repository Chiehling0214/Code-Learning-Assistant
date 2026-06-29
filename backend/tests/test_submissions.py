"""API tests for exercises and submissions (in-memory fakes, no database).

Execution/grading is Sprint 4; here a submission is just stored as ``pending``.
"""

import uuid
from types import SimpleNamespace

from fastapi.testclient import TestClient


def _seed_exercise(fakes: SimpleNamespace):
    return fakes.exercises.create(
        lesson_id=uuid.uuid4(),
        language="python",
        title="Hello",
        slug="hello",
        prompt="Return hello",
        starter_code="def solution():\n    pass\n",
        test_spec={"cases": [{"input": "", "expected": "hi"}]},
    )


def test_get_exercise_returns_starter_code_without_test_spec(
    client: TestClient, fakes: SimpleNamespace
) -> None:
    exercise = _seed_exercise(fakes)
    res = client.get(f"/api/v1/exercises/{exercise.id}")
    assert res.status_code == 200
    body = res.json()
    assert body["starter_code"].startswith("def solution")
    assert body["language"] == "python"
    assert "test_spec" not in body  # hidden test cases never leak


def test_get_exercise_404_when_missing(client: TestClient) -> None:
    assert client.get(f"/api/v1/exercises/{uuid.uuid4()}").status_code == 404


def test_submit_creates_pending_submission(
    client: TestClient, fakes: SimpleNamespace
) -> None:
    exercise = _seed_exercise(fakes)
    res = client.post(
        f"/api/v1/exercises/{exercise.id}/submit",
        json={"code": "print('hi')"},
    )
    assert res.status_code == 201, res.text
    body = res.json()
    assert body["status"] == "pending"
    assert body["result"] is None
    assert body["code"] == "print('hi')"


def test_submit_unknown_exercise_404(client: TestClient) -> None:
    res = client.post(f"/api/v1/exercises/{uuid.uuid4()}/submit", json={"code": "x"})
    assert res.status_code == 404


def test_submissions_history_lists_attempts(
    client: TestClient, fakes: SimpleNamespace
) -> None:
    exercise = _seed_exercise(fakes)
    client.post(f"/api/v1/exercises/{exercise.id}/submit", json={"code": "a"})
    client.post(f"/api/v1/exercises/{exercise.id}/submit", json={"code": "b"})

    res = client.get(f"/api/v1/exercises/{exercise.id}/submissions")
    assert res.status_code == 200
    assert len(res.json()) == 2


def test_non_admin_cannot_create_exercise(
    client: TestClient, fakes: SimpleNamespace
) -> None:
    lesson = fakes.lessons.create(
        course_id=uuid.uuid4(), title="L", slug="l", order_index=1, content=""
    )
    res = client.post(
        "/api/v1/admin/exercises",
        json={"lesson_id": str(lesson.id), "title": "X", "slug": "x"},
    )
    assert res.status_code == 403


def test_admin_can_create_exercise(admin_client: TestClient, fakes: SimpleNamespace) -> None:
    lesson = fakes.lessons.create(
        course_id=uuid.uuid4(), title="L", slug="l", order_index=1, content=""
    )
    res = admin_client.post(
        "/api/v1/admin/exercises",
        json={
            "lesson_id": str(lesson.id),
            "title": "Hello",
            "slug": "hello",
            "language": "python",
            "starter_code": "def solution():\n    pass\n",
        },
    )
    assert res.status_code == 201, res.text
    assert res.json()["title"] == "Hello"


def test_admin_create_exercise_404_for_unknown_lesson(admin_client: TestClient) -> None:
    res = admin_client.post(
        "/api/v1/admin/exercises",
        json={"lesson_id": str(uuid.uuid4()), "title": "X", "slug": "x"},
    )
    assert res.status_code == 404
