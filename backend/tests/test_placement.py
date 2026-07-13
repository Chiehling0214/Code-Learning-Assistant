"""API tests for the placement test (AI + Judge0 mocked, no network)."""

import uuid
from types import SimpleNamespace

from fastapi.testclient import TestClient


def _make_track(client: TestClient, fakes: SimpleNamespace) -> str:
    lang = fakes.languages.create(name="Python", slug="python")
    res = client.post("/api/v1/me/tracks", json={"language_id": str(lang.id)})
    assert res.status_code == 201, res.text
    return res.json()["id"]


def test_generate_returns_sanitized_assessment(
    client: TestClient, fakes: SimpleNamespace
) -> None:
    track_id = _make_track(client, fakes)
    res = client.post(f"/api/v1/me/tracks/{track_id}/placement")
    assert res.status_code == 200, res.text
    body = res.json()
    assert len(body["mcqs"]) == 2
    assert len(body["coding"]) == 1
    # No answer keys / reference solutions leak.
    assert "is_correct" not in res.text
    assert "reference_solution" not in res.text
    assert "test_spec" not in res.text


def test_generate_is_idempotent(client: TestClient, fakes: SimpleNamespace) -> None:
    track_id = _make_track(client, fakes)
    first = client.post(f"/api/v1/me/tracks/{track_id}/placement").json()
    second = client.post(f"/api/v1/me/tracks/{track_id}/placement").json()
    assert [m["id"] for m in first["mcqs"]] == [m["id"] for m in second["mcqs"]]


def test_get_before_generate_404(client: TestClient, fakes: SimpleNamespace) -> None:
    track_id = _make_track(client, fakes)
    assert client.get(f"/api/v1/me/tracks/{track_id}/placement").status_code == 404


def test_generate_unknown_track_404(client: TestClient) -> None:
    res = client.post(f"/api/v1/me/tracks/{uuid.uuid4()}/placement")
    assert res.status_code == 404


def test_submit_all_correct_is_advanced(client: TestClient, fakes: SimpleNamespace) -> None:
    track_id = _make_track(client, fakes)
    placement = client.post(f"/api/v1/me/tracks/{track_id}/placement").json()
    # The fake provider makes the first choice correct.
    mcq_answers = {m["id"]: m["choices"][0]["id"] for m in placement["mcqs"]}
    code = {t["id"]: "print('ok')" for t in placement["coding"]}

    res = client.post(
        f"/api/v1/me/tracks/{track_id}/placement/submit",
        json={"mcq_answers": mcq_answers, "code": code},
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["percent"] == 100
    assert body["level"] == "advanced"

    # The breakdown carries review detail: correct answer, explanation, choices,
    # and the coding score.
    first_mcq = body["breakdown"]["mcqs"][0]
    assert first_mcq["correct"] is True
    assert first_mcq["explanation"]
    assert first_mcq["correct_choice_id"] == first_mcq["selected_choice_id"]
    assert any(c["is_correct"] for c in first_mcq["choices"])
    coding = body["breakdown"]["coding"][0]
    assert coding["passed_cases"] == coding["total_cases"]
    # The learner's submission, the reference solution, and per-item points are
    # revealed for the review screen.
    assert coding["code"] == "print('ok')"
    assert coding["reference_solution"]
    assert coding["points_earned"] == coding["points_possible"] == 3
    assert first_mcq["points_earned"] == first_mcq["points_possible"] == 1
    assert body["breakdown"]["earned_points"] == body["breakdown"]["total_points"]

    # Level persisted on the track and profile.
    track = next(t for t in client.get("/api/v1/me/tracks").json() if t["id"] == track_id)
    assert track["level"] == "advanced"
    assert client.get("/api/v1/me/profile").json()["skill_level"] == "advanced"


def test_submit_all_wrong_is_beginner(client: TestClient, fakes: SimpleNamespace) -> None:
    track_id = _make_track(client, fakes)
    placement = client.post(f"/api/v1/me/tracks/{track_id}/placement").json()
    # Wrong MCQ choice + no code submitted.
    mcq_answers = {m["id"]: m["choices"][1]["id"] for m in placement["mcqs"]}

    res = client.post(
        f"/api/v1/me/tracks/{track_id}/placement/submit",
        json={"mcq_answers": mcq_answers, "code": {}},
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["percent"] == 0
    assert body["level"] == "beginner"
