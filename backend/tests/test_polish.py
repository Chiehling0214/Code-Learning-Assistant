"""Tests for Sprint 17 polish: SSE streaming AI + account deletion."""

import json
import uuid
from types import SimpleNamespace

from fastapi.testclient import TestClient


def _sse_texts(body: str) -> tuple[str, bool]:
    """Concatenate SSE text chunks; returns (text, saw_done)."""
    text, done = "", False
    for line in body.splitlines():
        if not line.startswith("data: "):
            continue
        data = line[len("data: ") :]
        if data == "[DONE]":
            done = True
        else:
            payload = json.loads(data)
            text += payload.get("text", "")
    return text, done


# ----- streaming -----


def test_teacher_stream_sends_chunks_then_done(client: TestClient) -> None:
    res = client.post(
        "/api/v1/ai/teacher/stream", json={"topic": "loops", "question": "why?"}
    )
    assert res.status_code == 200, res.text
    assert res.headers["content-type"].startswith("text/event-stream")
    text, done = _sse_texts(res.text)
    assert "Explanation of loops" in text and "why?" in text
    assert done


def test_tutor_stream_sends_chunks(client: TestClient, fakes: SimpleNamespace) -> None:
    exercise = fakes.exercises.create(
        lesson_id=uuid.uuid4(), language="python", title="Sum", slug="sum",
        prompt="Add", starter_code="", test_spec={},
    )
    res = client.post(
        "/api/v1/ai/tutor/stream", json={"exercise_id": str(exercise.id), "code": "x = 1"}
    )
    assert res.status_code == 200, res.text
    text, done = _sse_texts(res.text)
    assert "x = 1" in text
    assert done


def test_tutor_stream_maps_prestream_errors(client: TestClient) -> None:
    # Unknown exercise fails BEFORE streaming with a normal HTTP error.
    res = client.post(
        "/api/v1/ai/tutor/stream", json={"exercise_id": str(uuid.uuid4()), "code": "x"}
    )
    assert res.status_code == 404


def test_stream_records_usage_for_rate_limiting(
    client: TestClient, fakes: SimpleNamespace
) -> None:
    client.post("/api/v1/ai/teacher/stream", json={"topic": "loops"})
    user = fakes.users.get_by_firebase_uid("stub-uid")
    assert fakes.interactions.count_since(
        user.id, __import__("datetime").datetime.now(__import__("datetime").UTC)
        - __import__("datetime").timedelta(minutes=1),
        kind="teacher",
    ) == 1


# ----- account deletion -----


def test_delete_me_removes_the_account(client: TestClient, fakes: SimpleNamespace) -> None:
    before = client.get("/api/v1/me").json()

    res = client.delete("/api/v1/me")
    assert res.status_code == 204

    # The old user row is gone; the next authed call provisions a fresh account.
    assert fakes.users.get_by_id(uuid.UUID(before["id"])) is None
    after = client.get("/api/v1/me").json()
    assert after["id"] != before["id"]
