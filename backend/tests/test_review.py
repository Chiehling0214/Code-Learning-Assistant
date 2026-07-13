"""API + service tests for spaced review of mistakes (Sprint 15)."""

import uuid
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

from app.application.services.review_service import ReviewService
from app.infrastructure.grading import sync_exercise_review
from fastapi.testclient import TestClient

from tests.fakes import FakeReviewItemRepository


def _seed_quiz(fakes: SimpleNamespace):
    quiz = fakes.quizzes.create(
        lesson_id=uuid.uuid4(), title="Basics", slug="basics", description=None
    )
    question = fakes.quizzes.add_question(
        quiz_id=quiz.id,
        prompt="2 + 2 = ?",
        type="single",
        order_index=0,
        choices=[{"text": "4", "is_correct": True}, {"text": "5", "is_correct": False}],
        explanation="2 + 2 equals 4.",
    )
    return quiz, question


def _make_due(fakes: SimpleNamespace) -> None:
    """Backdate every active item so it shows up as due right now."""
    past = datetime.now(UTC) - timedelta(minutes=1)
    for item in list(fakes.reviews._items.values()):
        if not item.retired:
            fakes.reviews.update(item.id, due_at=past)


# ----- capture -----


def test_wrong_quiz_answer_lands_in_notebook(client: TestClient, fakes: SimpleNamespace) -> None:
    quiz, question = _seed_quiz(fakes)
    wrong = next(c for c in question.choices if not c.is_correct)
    client.post(
        f"/api/v1/quizzes/{quiz.id}/submit",
        json={"answers": {str(question.id): str(wrong.id)}},
    )

    notebook = client.get("/api/v1/me/review/all").json()["items"]
    assert len(notebook) == 1
    assert notebook[0]["source"] == "quiz"
    assert notebook[0]["payload"]["prompt"] == "2 + 2 = ?"
    assert notebook[0]["payload"]["explanation"] == "2 + 2 equals 4."


def test_correct_quiz_answer_is_not_captured(client: TestClient, fakes: SimpleNamespace) -> None:
    quiz, question = _seed_quiz(fakes)
    correct = next(c for c in question.choices if c.is_correct)
    client.post(
        f"/api/v1/quizzes/{quiz.id}/submit",
        json={"answers": {str(question.id): str(correct.id)}},
    )
    assert client.get("/api/v1/me/review/all").json()["items"] == []


def test_placement_wrong_mcq_is_captured(client: TestClient, fakes: SimpleNamespace) -> None:
    lang = fakes.languages.create(name="Python", slug="python")
    track = client.post("/api/v1/me/tracks", json={"language_id": str(lang.id)}).json()
    placement = client.post(f"/api/v1/me/tracks/{track['id']}/placement").json()
    # Answer every MCQ wrong (the fake provider marks the first choice correct).
    answers = {m["id"]: m["choices"][1]["id"] for m in placement["mcqs"]}
    client.post(
        f"/api/v1/me/tracks/{track['id']}/placement/submit",
        json={"mcq_answers": answers, "code": {}},
    )
    items = client.get("/api/v1/me/review/all").json()["items"]
    assert len(items) == len(placement["mcqs"])
    assert all(i["source"] == "placement" for i in items)


def test_failed_exercise_captures_and_pass_advances() -> None:
    repo = FakeReviewItemRepository()
    service = ReviewService(repo)
    uid = uuid.uuid4()
    exercise = SimpleNamespace(
        id=uuid.uuid4(), title="Sum", language="python", prompt="Add the numbers."
    )

    sync_exercise_review(service, user_id=uid, exercise=exercise, verdict="failed")
    item = repo.get_by_user_and_ref(uid, exercise.id)
    assert item is not None and item.payload["kind"] == "exercise"

    # Solving it later (outside the review flow) records a pass automatically.
    sync_exercise_review(service, user_id=uid, exercise=exercise, verdict="passed")
    assert repo.get_by_user_and_ref(uid, exercise.id).passes == 1

    # Infrastructure errors change nothing.
    sync_exercise_review(service, user_id=uid, exercise=exercise, verdict="error")
    assert repo.get_by_user_and_ref(uid, exercise.id).passes == 1


# ----- the schedule -----


def test_schedule_doubles_then_retires_and_wrong_resets() -> None:
    repo = FakeReviewItemRepository()
    service = ReviewService(repo)
    uid, ref = uuid.uuid4(), uuid.uuid4()
    item = service.capture_miss(user_id=uid, source="quiz", item_ref=ref, payload={})
    assert item.interval_days == 1

    one = service.answer(user_id=uid, item_id=item.id, correct=True)
    assert (one.interval_days, one.passes, one.retired) == (2, 1, False)
    two = service.answer(user_id=uid, item_id=item.id, correct=True)
    assert (two.interval_days, two.passes, two.retired) == (4, 2, False)

    # A miss resets the schedule and counts a lapse.
    missed = service.answer(user_id=uid, item_id=item.id, correct=False)
    assert (missed.interval_days, missed.passes, missed.lapses) == (1, 0, 1)

    # Three consecutive passes retire the item.
    service.answer(user_id=uid, item_id=item.id, correct=True)
    service.answer(user_id=uid, item_id=item.id, correct=True)
    final = service.answer(user_id=uid, item_id=item.id, correct=True)
    assert final.retired is True


def test_recapture_reactivates_a_retired_item() -> None:
    repo = FakeReviewItemRepository()
    service = ReviewService(repo)
    uid, ref = uuid.uuid4(), uuid.uuid4()
    item = service.capture_miss(user_id=uid, source="quiz", item_ref=ref, payload={})
    for _ in range(3):
        service.answer(user_id=uid, item_id=item.id, correct=True)
    assert repo.get_by_id(item.id).retired is True

    again = service.capture_miss(user_id=uid, source="quiz", item_ref=ref, payload={})
    assert again.id == item.id  # same row, reactivated
    assert (again.retired, again.passes, again.interval_days) == (False, 0, 1)


# ----- the review flow (API) -----


def test_due_queue_answer_and_ownership(client: TestClient, fakes: SimpleNamespace) -> None:
    quiz, question = _seed_quiz(fakes)
    wrong = next(c for c in question.choices if not c.is_correct)
    client.post(
        f"/api/v1/quizzes/{quiz.id}/submit",
        json={"answers": {str(question.id): str(wrong.id)}},
    )

    # Not due yet (scheduled for tomorrow).
    assert client.get("/api/v1/me/review").json()["due_count"] == 0
    _make_due(fakes)
    due = client.get("/api/v1/me/review").json()
    assert due["due_count"] == 1

    item_id = due["items"][0]["id"]
    answered = client.post(f"/api/v1/me/review/{item_id}/answer", json={"correct": True})
    assert answered.status_code == 200, answered.text
    assert answered.json()["passes"] == 1
    assert client.get("/api/v1/me/review").json()["due_count"] == 0

    # Unknown / foreign item → 404.
    assert (
        client.post(f"/api/v1/me/review/{uuid.uuid4()}/answer", json={"correct": True}).status_code
        == 404
    )


def test_today_surfaces_due_reviews(client: TestClient, fakes: SimpleNamespace) -> None:
    quiz, question = _seed_quiz(fakes)
    wrong = next(c for c in question.choices if not c.is_correct)
    client.post(
        f"/api/v1/quizzes/{quiz.id}/submit",
        json={"answers": {str(question.id): str(wrong.id)}},
    )
    assert client.get("/api/v1/today").json()["reviews_due"] == 0
    _make_due(fakes)
    assert client.get("/api/v1/today").json()["reviews_due"] == 1
