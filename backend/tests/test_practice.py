"""API tests for practice drills + topic mastery (Sprint 16). AI is mocked."""

import uuid
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

from app.domain.entities import AIInteraction
from fastapi.testclient import TestClient


def _study(fakes: SimpleNamespace, *, slug: str = "python", name: str = "Python"):
    """Provision the stub user with a levelled track for a language."""
    user = fakes.users.get_by_firebase_uid("stub-uid") or fakes.users.create(
        firebase_uid="stub-uid", email="dev@codepath.local"
    )
    lang = fakes.languages.create(name=name, slug=slug)
    track = fakes.tracks.create(user_id=user.id, language_id=lang.id)
    fakes.tracks.set_level(track.id, "intermediate")
    return user, lang, track


# ----- generation -----


def test_generate_drill_end_to_end(client: TestClient, fakes: SimpleNamespace) -> None:
    _study(fakes)
    res = client.post(
        "/api/v1/practice/generate", json={"language": "python", "topic": "recursion"}
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["topic"] == "recursion"

    # The drill is a real exercise: it serves, runs, and submits like any other.
    ex = client.get(f"/api/v1/exercises/{body['exercise_id']}")
    assert ex.status_code == 200
    run = client.post(f"/api/v1/exercises/{body['exercise_id']}/run", json={"code": "print(1)"})
    assert run.status_code == 200


def test_drills_stay_out_of_courses_today_and_progress(
    client: TestClient, fakes: SimpleNamespace
) -> None:
    _study(fakes)
    client.post("/api/v1/practice/generate", json={"language": "python", "topic": "loops"})

    # Hidden container: not in the dashboard course list…
    assert all(
        "Practice" not in c["title"] for c in client.get("/api/v1/me/courses").json()
    )
    # …not in the daily plan…
    assert client.get("/api/v1/today").json()["items"] == []
    # …and not in course progress.
    assert client.get("/api/v1/progress").json()["courses"] == []


def test_generate_requires_a_track(client: TestClient, fakes: SimpleNamespace) -> None:
    fakes.languages.create(name="C++", slug="cpp")
    # No track for cpp → 404 (not studying it).
    res = client.post("/api/v1/practice/generate", json={"language": "cpp"})
    assert res.status_code == 404


def test_generate_respects_daily_generation_cap(
    client: TestClient, fakes: SimpleNamespace
) -> None:
    user, *_ = _study(fakes)
    # Exhaust the free daily generation quota (10), backdated past the burst window.
    earlier = datetime.now(UTC) - timedelta(minutes=10)
    for _ in range(10):
        fakes.interactions._items.append(
            AIInteraction(
                id=uuid.uuid4(),
                user_id=user.id,
                kind="generate",
                model="m",
                total_tokens=1,
                created_at=earlier,
            )
        )
    res = client.post("/api/v1/practice/generate", json={"language": "python"})
    assert res.status_code == 402


def test_weakest_topic_is_targeted_when_no_topic_given(
    client: TestClient, fakes: SimpleNamespace
) -> None:
    user, lang, track = _study(fakes)
    course = fakes.courses.create(
        language_id=lang.id, title="Course", slug="course", description=None, track_id=track.id
    )
    strong = fakes.lessons.create(
        course_id=course.id, title="Strings", slug="strings", order_index=0, content=""
    )
    weak = fakes.lessons.create(
        course_id=course.id, title="Pointers", slug="pointers", order_index=1, content=""
    )
    ex_strong = fakes.exercises.create(
        lesson_id=strong.id, language="python", title="s", slug="s", prompt="",
        starter_code="", test_spec={},
    )
    ex_weak = fakes.exercises.create(
        lesson_id=weak.id, language="python", title="w", slug="w", prompt="",
        starter_code="", test_spec={},
    )
    # History: Strings passed twice (strong), Pointers failed twice (weak).
    for _ in range(2):
        fakes.progress.record(
            user_id=user.id, item_type="exercise", item_id=ex_strong.id, status="passed"
        )
        fakes.progress.record(
            user_id=user.id, item_type="exercise", item_id=ex_weak.id, status="failed"
        )

    res = client.post("/api/v1/practice/generate", json={"language": "python"})
    assert res.status_code == 200, res.text
    assert res.json()["topic"] == "Pointers"

    # History lists the drill with its topic.
    history = client.get("/api/v1/practice/history").json()
    assert history and history[0]["topic"] == "Pointers"


# ----- mastery -----


def test_mastery_snapshot_math(client: TestClient, fakes: SimpleNamespace) -> None:
    user, lang, track = _study(fakes)
    course = fakes.courses.create(
        language_id=lang.id, title="Course", slug="course", description=None, track_id=track.id
    )
    lesson = fakes.lessons.create(
        course_id=course.id, title="Loops", slug="loops", order_index=0, content=""
    )
    ex = fakes.exercises.create(
        lesson_id=lesson.id, language="python", title="e", slug="e", prompt="",
        starter_code="", test_spec={},
    )
    quiz = fakes.quizzes.create(lesson_id=lesson.id, title="q", slug="q", description=None)
    # 1 passed exercise + a 1/2 quiz attempt → 2 correct of 3 attempts (0.67, "ok").
    fakes.progress.record(user_id=user.id, item_type="exercise", item_id=ex.id, status="passed")
    fakes.attempts.create(
        user_id=user.id, quiz_id=quiz.id, score=1, answers={"total": 2, "results": []}
    )

    body = client.get("/api/v1/me/mastery?language=python").json()
    assert body["language"] == "python"
    topic = next(t for t in body["topics"] if t["topic"] == "Loops")
    assert (topic["attempts"], topic["correct"]) == (3, 2)
    assert topic["correct_rate"] == 0.67
    assert topic["level"] == "ok"
    # Course topics link back to the lesson that teaches them.
    assert topic["lesson_id"] == str(lesson.id)


def test_mastery_unknown_language_404(client: TestClient) -> None:
    assert client.get("/api/v1/me/mastery?language=nope").status_code == 404
