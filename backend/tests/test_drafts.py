"""API tests for cross-device coding drafts."""

import uuid
from types import SimpleNamespace

from fastapi.testclient import TestClient


def _exercise(fakes: SimpleNamespace):
    lesson = fakes.lessons.create(
        course_id=uuid.uuid4(),
        title="Drafts",
        slug="drafts",
        order_index=0,
        content="",
    )
    return fakes.exercises.create(
        lesson_id=lesson.id,
        language="python",
        title="Keep working",
        slug="keep-working",
        prompt="Solve it",
        starter_code="def solution():\n    pass\n",
        test_spec={},
    )


def test_draft_round_trip_and_reset(client: TestClient, fakes: SimpleNamespace) -> None:
    exercise = _exercise(fakes)
    path = f"/api/v1/exercises/{exercise.id}/draft"

    assert client.get(path).status_code == 204
    saved = client.put(path, json={"code": "def solution():\n    return 42\n"})
    assert saved.status_code == 200
    assert saved.json()["code"].endswith("return 42\n")
    assert client.get(path).json()["code"] == saved.json()["code"]

    assert client.delete(path).status_code == 204
    assert client.get(path).status_code == 204


def test_draft_rejects_unknown_exercise(client: TestClient) -> None:
    missing = client.put(
        f"/api/v1/exercises/{uuid.uuid4()}/draft",
        json={"code": "print('no')"},
    )
    assert missing.status_code == 404
