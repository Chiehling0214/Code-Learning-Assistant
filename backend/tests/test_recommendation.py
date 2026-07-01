"""API tests for the Today plan and Progress analytics (in-memory fakes)."""

import uuid
from types import SimpleNamespace

from app.infrastructure.grading import record_exercise_progress
from fastapi.testclient import TestClient

from tests.fakes import FakeProgressRepository


def _seed(fakes: SimpleNamespace):
    lang = fakes.languages.create(name="Python", slug="python")
    course = fakes.courses.create(
        language_id=lang.id, title="Basics", slug="basics", description=None
    )
    lesson = fakes.lessons.create(
        course_id=course.id, title="Loops", slug="loops", order_index=1, content="# Loops"
    )
    exercise = fakes.exercises.create(
        lesson_id=lesson.id,
        language="python",
        title="Ex1",
        slug="ex1",
        prompt="",
        starter_code="",
        test_spec={},
    )
    quiz = fakes.quizzes.create(
        lesson_id=lesson.id, title="Quiz1", slug="quiz1", description=None
    )
    return course, lesson, exercise, quiz


# ----- Today -----


def test_today_lists_incomplete_items(client: TestClient, fakes: SimpleNamespace) -> None:
    _seed(fakes)
    res = client.get("/api/v1/today")
    assert res.status_code == 200, res.text
    types = {item["type"] for item in res.json()["items"]}
    assert types == {"lesson", "exercise", "quiz"}


def test_mark_lesson_complete_removes_it_from_today(
    client: TestClient, fakes: SimpleNamespace
) -> None:
    _, lesson, _, _ = _seed(fakes)
    assert client.post(f"/api/v1/lessons/{lesson.id}/complete").status_code == 200

    items = client.get("/api/v1/today").json()["items"]
    lesson_ids = [i["id"] for i in items if i["type"] == "lesson"]
    assert str(lesson.id) not in lesson_ids


def test_mark_complete_unknown_lesson_404(client: TestClient) -> None:
    assert client.post(f"/api/v1/lessons/{uuid.uuid4()}/complete").status_code == 404


def test_other_users_progress_does_not_affect_plan(
    client: TestClient, fakes: SimpleNamespace
) -> None:
    _, _, exercise, _ = _seed(fakes)
    # Another user's completion must not remove the item from this learner's plan.
    fakes.progress.record(
        user_id=uuid.uuid4(), item_type="exercise", item_id=exercise.id, status="passed"
    )
    ids = {i["id"] for i in client.get("/api/v1/today").json()["items"]}
    assert str(exercise.id) in ids


def _add_question(fakes: SimpleNamespace, quiz_id: uuid.UUID):
    return fakes.quizzes.add_question(
        quiz_id=quiz_id,
        prompt="2+2?",
        type="single",
        order_index=0,
        choices=[{"text": "4", "is_correct": True}, {"text": "5", "is_correct": False}],
    )


def test_quiz_submission_records_progress(client: TestClient, fakes: SimpleNamespace) -> None:
    _, _, _, quiz = _seed(fakes)
    question = _add_question(fakes, quiz.id)
    correct = next(c for c in question.choices if c.is_correct)

    submit = client.post(
        f"/api/v1/quizzes/{quiz.id}/submit",
        json={"answers": {str(question.id): str(correct.id)}},
    )
    assert submit.status_code == 200, submit.text

    # The quiz is now completed: excluded from Today and counted in Progress.
    today_ids = {i["id"] for i in client.get("/api/v1/today").json()["items"]}
    assert str(quiz.id) not in today_ids
    assert client.get("/api/v1/progress").json()["completed"] >= 1


# ----- Progress -----


def test_progress_aggregates(client: TestClient, fakes: SimpleNamespace) -> None:
    course, lesson, _, quiz = _seed(fakes)  # 3 items total (lesson+exercise+quiz)
    question = _add_question(fakes, quiz.id)
    correct = next(c for c in question.choices if c.is_correct)

    # Complete the lesson and the quiz (both via current-user endpoints).
    client.post(f"/api/v1/lessons/{lesson.id}/complete")
    client.post(
        f"/api/v1/quizzes/{quiz.id}/submit",
        json={"answers": {str(question.id): str(correct.id)}},
    )

    body = client.get("/api/v1/progress").json()
    assert body["total"] == 3
    assert body["completed"] == 2
    assert body["streak"] == 1
    course_row = next(c for c in body["courses"] if c["slug"] == course.slug)
    assert course_row["percent"] == 67  # round(2/3 * 100)


# ----- grading -> progress helper -----


def test_record_exercise_progress_records_terminal_verdicts() -> None:
    repo = FakeProgressRepository()
    uid, eid = uuid.uuid4(), uuid.uuid4()
    assert record_exercise_progress(repo, user_id=uid, exercise_id=eid, verdict="passed") is True
    assert record_exercise_progress(repo, user_id=uid, exercise_id=eid, verdict="error") is False
    assert len(repo.list_for_user(uid)) == 1
