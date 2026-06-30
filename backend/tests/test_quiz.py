"""API tests for quizzes (in-memory fakes, no database).

Covers: answer keys never leak on read, auto-grading correctness, attempt
persistence, and the admin authoring guard.
"""

import uuid
from types import SimpleNamespace

from fastapi.testclient import TestClient


def _seed_quiz(fakes: SimpleNamespace, *, two_questions: bool = False):
    """Author a quiz directly through the fakes so the test knows the answer key."""
    quiz = fakes.quizzes.create(
        lesson_id=uuid.uuid4(), title="Basics", slug="basics", description="Intro quiz"
    )
    fakes.quizzes.add_question(
        quiz_id=quiz.id,
        prompt="2 + 2 = ?",
        type="single",
        order_index=0,
        choices=[{"text": "4", "is_correct": True}, {"text": "5", "is_correct": False}],
    )
    if two_questions:
        fakes.quizzes.add_question(
            quiz_id=quiz.id,
            prompt="Capital of France?",
            type="single",
            order_index=1,
            choices=[
                {"text": "Paris", "is_correct": True},
                {"text": "Rome", "is_correct": False},
            ],
        )
    return fakes.quizzes.get_by_id(quiz.id)


def test_get_quiz_never_leaks_answer_key(client: TestClient, fakes: SimpleNamespace) -> None:
    quiz = _seed_quiz(fakes)
    res = client.get(f"/api/v1/quizzes/{quiz.id}")
    assert res.status_code == 200
    body = res.json()
    assert body["title"] == "Basics"
    assert len(body["questions"]) == 1
    # No choice (or anywhere in the payload) exposes correctness.
    for choice in body["questions"][0]["choices"]:
        assert "is_correct" not in choice
    assert "is_correct" not in res.text


def test_get_quiz_404_when_missing(client: TestClient) -> None:
    assert client.get(f"/api/v1/quizzes/{uuid.uuid4()}").status_code == 404


def test_submit_grades_correct_answer(client: TestClient, fakes: SimpleNamespace) -> None:
    quiz = _seed_quiz(fakes)
    question = quiz.questions[0]
    correct = next(c for c in question.choices if c.is_correct)

    res = client.post(
        f"/api/v1/quizzes/{quiz.id}/submit",
        json={"answers": {str(question.id): str(correct.id)}},
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["score"] == 1
    assert body["total"] == 1
    assert body["results"][0]["correct"] is True
    assert body["results"][0]["correct_choice_id"] == str(correct.id)


def test_submit_partial_score(client: TestClient, fakes: SimpleNamespace) -> None:
    quiz = _seed_quiz(fakes, two_questions=True)
    q1, q2 = quiz.questions
    right = next(c for c in q1.choices if c.is_correct)
    wrong = next(c for c in q2.choices if not c.is_correct)

    res = client.post(
        f"/api/v1/quizzes/{quiz.id}/submit",
        json={"answers": {str(q1.id): str(right.id), str(q2.id): str(wrong.id)}},
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["score"] == 1
    assert body["total"] == 2


def test_submit_persists_attempt(client: TestClient, fakes: SimpleNamespace) -> None:
    quiz = _seed_quiz(fakes)
    question = quiz.questions[0]
    correct = next(c for c in question.choices if c.is_correct)
    client.post(
        f"/api/v1/quizzes/{quiz.id}/submit",
        json={"answers": {str(question.id): str(correct.id)}},
    )

    res = client.get(f"/api/v1/quizzes/{quiz.id}/attempts")
    assert res.status_code == 200
    attempts = res.json()
    assert len(attempts) == 1
    assert attempts[0]["score"] == 1
    assert attempts[0]["total"] == 1


def test_submit_unknown_quiz_404(client: TestClient) -> None:
    res = client.post(
        f"/api/v1/quizzes/{uuid.uuid4()}/submit",
        json={"answers": {str(uuid.uuid4()): str(uuid.uuid4())}},
    )
    assert res.status_code == 404


def test_non_admin_cannot_create_quiz(client: TestClient, fakes: SimpleNamespace) -> None:
    lesson = fakes.lessons.create(
        course_id=uuid.uuid4(), title="L", slug="l", order_index=1, content=""
    )
    res = client.post(
        "/api/v1/admin/quizzes",
        json={"lesson_id": str(lesson.id), "title": "Q", "slug": "q"},
    )
    assert res.status_code == 403


def test_admin_can_author_quiz_and_question(
    admin_client: TestClient, fakes: SimpleNamespace
) -> None:
    lesson = fakes.lessons.create(
        course_id=uuid.uuid4(), title="L", slug="l", order_index=1, content=""
    )
    created = admin_client.post(
        "/api/v1/admin/quizzes",
        json={"lesson_id": str(lesson.id), "title": "Quiz", "slug": "quiz"},
    )
    assert created.status_code == 201, created.text
    quiz_id = created.json()["id"]

    res = admin_client.post(
        f"/api/v1/admin/quizzes/{quiz_id}/questions",
        json={
            "prompt": "Pick the right one",
            "choices": [
                {"text": "Right", "is_correct": True},
                {"text": "Wrong", "is_correct": False},
            ],
        },
    )
    assert res.status_code == 201, res.text
    body = res.json()
    assert body["prompt"] == "Pick the right one"
    # Even the admin authoring response strips the answer key from choices.
    assert all("is_correct" not in c for c in body["choices"])


def test_add_question_requires_a_correct_choice(
    admin_client: TestClient, fakes: SimpleNamespace
) -> None:
    lesson = fakes.lessons.create(
        course_id=uuid.uuid4(), title="L", slug="l", order_index=1, content=""
    )
    quiz_id = admin_client.post(
        "/api/v1/admin/quizzes",
        json={"lesson_id": str(lesson.id), "title": "Quiz", "slug": "quiz"},
    ).json()["id"]

    res = admin_client.post(
        f"/api/v1/admin/quizzes/{quiz_id}/questions",
        json={
            "prompt": "No correct choice",
            "choices": [
                {"text": "A", "is_correct": False},
                {"text": "B", "is_correct": False},
            ],
        },
    )
    assert res.status_code == 400
