"""API + service tests for course extension and in-course chat (Sprint 12).

AI and Judge0 are mocked via the in-memory fakes, so no network is used.
"""

import uuid
from types import SimpleNamespace

import pytest
from app.application.services.ai_usage import AIUsageGuard, RateLimitError
from app.application.services.curriculum_service import CurriculumService
from app.application.services.execution_service import ExecutionService
from app.core.config import Settings
from fastapi.testclient import TestClient


def _seed_course(fakes: SimpleNamespace):
    """A course owned by the current (stub) user, with one lesson."""
    user = fakes.users.get_by_firebase_uid("stub-uid") or fakes.users.create(
        firebase_uid="stub-uid", email="dev@codepath.local"
    )
    lang = fakes.languages.create(name="Python", slug="python")
    track = fakes.tracks.create(user_id=user.id, language_id=lang.id)
    fakes.tracks.set_level(track.id, "beginner")
    course = fakes.courses.create(
        language_id=lang.id, title="Basics", slug="basics", description=None, track_id=track.id
    )
    lesson = fakes.lessons.create(
        course_id=course.id, title="Loops", slug="loops", order_index=0, content="# Loops"
    )
    return user, course, lesson


# ----- extend -----


def test_extend_appends_lessons_in_order(client: TestClient, fakes: SimpleNamespace) -> None:
    _, course, _ = _seed_course(fakes)
    res = client.post(f"/api/v1/courses/{course.id}/extend", json={})
    assert res.status_code == 200, res.text
    body = res.json()
    assert len(body["added"]) >= 1
    orders = [a["order_index"] for a in body["added"]]
    # Appended after the existing lesson (order_index 0), preserving order.
    assert orders == sorted(orders)
    assert min(orders) == 1
    assert body["lesson_count"] == 1 + len(body["added"])


def test_extend_respects_requested_count(client: TestClient, fakes: SimpleNamespace) -> None:
    _, course, _ = _seed_course(fakes)
    res = client.post(f"/api/v1/courses/{course.id}/extend", json={"count": 3})
    assert res.status_code == 200, res.text
    assert len(res.json()["added"]) == 3


def test_extend_count_is_bounded(client: TestClient, fakes: SimpleNamespace) -> None:
    _, course, _ = _seed_course(fakes)
    # Far above curriculum_extend_max (5) → clamped.
    res = client.post(f"/api/v1/courses/{course.id}/extend", json={"count": 20})
    assert res.status_code == 200, res.text
    assert len(res.json()["added"]) == 5


def test_onboarding_build_not_counted_but_extend_is(
    client: TestClient, fakes: SimpleNamespace
) -> None:
    user, course, _ = _seed_course(fakes)
    # The one-time onboarding build + placement do NOT consume the daily quota.
    fakes.interactions.create(user_id=user.id, kind="generate_course", model="m", total_tokens=1)
    fakes.interactions.create(user_id=user.id, kind="placement", model="m", total_tokens=1)
    assert client.get("/api/v1/me/entitlements").json()["generations_used_today"] == 0

    # An on-demand "Learn more" extend does count.
    client.post(f"/api/v1/courses/{course.id}/extend", json={"count": 1})
    assert client.get("/api/v1/me/entitlements").json()["generations_used_today"] == 1


def test_extend_unknown_course_404(client: TestClient) -> None:
    assert client.post(f"/api/v1/courses/{uuid.uuid4()}/extend", json={}).status_code == 404


def test_extend_other_users_course_404(client: TestClient, fakes: SimpleNamespace) -> None:
    _seed_course(fakes)  # the current user's course
    other = fakes.users.create(firebase_uid="other-uid", email="other@codepath.local")
    lang = fakes.languages.create(name="C++", slug="cpp")
    other_track = fakes.tracks.create(user_id=other.id, language_id=lang.id)
    other_course = fakes.courses.create(
        language_id=lang.id, title="C++", slug="cpp", description=None, track_id=other_track.id
    )
    assert client.post(f"/api/v1/courses/{other_course.id}/extend", json={}).status_code == 404
    assert client.get(f"/api/v1/courses/{other_course.id}/chat").status_code == 404


# ----- chat -----


def test_chat_generates_targeted_content_and_persists(
    client: TestClient, fakes: SimpleNamespace
) -> None:
    _, course, _ = _seed_course(fakes)
    res = client.post(
        f"/api/v1/courses/{course.id}/chat", json={"message": "teach me decorators"}
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["reply"]["role"] == "assistant"
    assert len(body["added"]) >= 1
    # The fake provider titles the pack after the requested topic.
    assert "decorators" in body["added"][0]["title"].lower()

    # The exchange is stored and returned in order (user then assistant).
    msgs = client.get(f"/api/v1/courses/{course.id}/chat").json()["messages"]
    assert [m["role"] for m in msgs] == ["user", "assistant"]
    assert msgs[0]["content"] == "teach me decorators"


def test_chat_followup_keeps_context(client: TestClient, fakes: SimpleNamespace) -> None:
    _, course, _ = _seed_course(fakes)
    client.post(f"/api/v1/courses/{course.id}/chat", json={"message": "lessons about pygame"})
    # A vague follow-up must carry the earlier topic forward (the recent
    # conversation is passed to the generator as focus), not reset to generic.
    res = client.post(f"/api/v1/courses/{course.id}/chat", json={"message": "I need more"})
    assert res.status_code == 200, res.text
    added = res.json()["added"]
    assert added
    assert "pygame" in added[0]["title"].lower()


def test_chat_rejects_empty_message(client: TestClient, fakes: SimpleNamespace) -> None:
    _, course, _ = _seed_course(fakes)
    # Pydantic min_length=1 rejects an empty message with 422.
    assert client.post(f"/api/v1/courses/{course.id}/chat", json={"message": ""}).status_code == 422


# ----- extension status -----


def test_extension_status_tracks_completion(
    client: TestClient, fakes: SimpleNamespace
) -> None:
    _, course, lesson = _seed_course(fakes)
    before = client.get(f"/api/v1/courses/{course.id}/extension").json()
    assert before["lesson_count"] == 1
    assert before["can_extend"] is False

    # Completing the only item pushes completion to 100% (>= threshold).
    client.post(f"/api/v1/lessons/{lesson.id}/complete")
    after = client.get(f"/api/v1/courses/{course.id}/extension").json()
    assert after["completion_percent"] == 100
    assert after["can_extend"] is True


# ----- quota (service level) -----


def test_extend_enforces_quota(fakes: SimpleNamespace) -> None:
    user, course, _ = _seed_course(fakes)
    # per-minute budget of 0 → any request is over budget.
    settings = Settings(ai_rate_limit_per_minute=0)
    service = CurriculumService(
        fakes.ai,
        fakes.jobs,
        fakes.courses,
        fakes.lessons,
        fakes.exercises,
        fakes.quizzes,
        fakes.languages,
        fakes.tracks,
        ExecutionService(fakes.runner),
        AIUsageGuard(fakes.interactions, settings),
        settings,
        fakes.progress,
    )
    with pytest.raises(RateLimitError):
        service.extend_course(course_id=course.id, user_id=user.id)
