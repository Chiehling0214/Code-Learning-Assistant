"""API tests for the admin AI-content review console (Sprint 13)."""

from types import SimpleNamespace

from fastapi.testclient import TestClient


def _ai_lesson(fakes: SimpleNamespace):
    owner = fakes.users.create(
        firebase_uid=f"owner-{len(fakes.users.list_all())}",
        email=f"owner-{len(fakes.users.list_all())}@example.com",
        display_name="Course owner",
    )
    lang = fakes.languages.create(name="Python", slug="python")
    track = fakes.tracks.create(user_id=owner.id, language_id=lang.id)
    course = fakes.courses.create(
        language_id=lang.id,
        title="Basics",
        slug="basics",
        description=None,
        track_id=track.id,
    )
    lesson = fakes.lessons.create(
        course_id=course.id,
        title="Decorators",
        slug="decorators",
        order_index=0,
        content="# Decorators",
        source="ai",
        review_status="pending",
    )
    return course, lesson


def test_review_requires_admin(client: TestClient) -> None:
    # The plain client's stub user is not an admin.
    assert client.get("/api/v1/admin/content").status_code == 403


def test_admin_lists_ai_content(admin_client: TestClient, fakes: SimpleNamespace) -> None:
    _, lesson = _ai_lesson(fakes)
    res = admin_client.get("/api/v1/admin/content?source=ai")
    assert res.status_code == 200, res.text
    body = res.json()
    ids = [row["lesson_id"] for row in body["items"]]
    assert str(lesson.id) in ids
    assert body["total"] >= 1
    assert body["page"] == 1


def test_admin_content_supports_server_filters_and_pagination(
    admin_client: TestClient, fakes: SimpleNamespace
) -> None:
    course, first = _ai_lesson(fakes)
    second = fakes.lessons.create(
        course_id=course.id,
        title="Generators",
        slug="generators",
        order_index=1,
        content="# Generators",
        source="ai",
        review_status="approved",
    )

    response = admin_client.get(
        "/api/v1/admin/content",
        params={"source": "ai", "review_status": "approved", "page_size": 1},
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["lesson_id"] == str(second.id)
    assert body["items"][0]["lesson_id"] != str(first.id)

    courses = admin_client.get("/api/v1/admin/content/courses?source=ai")
    assert courses.status_code == 200, courses.text
    assert courses.json()[0]["course_id"] == str(course.id)
    assert courses.json()[0]["total"] == 2

    users = admin_client.get("/api/v1/admin/content/users?source=ai")
    assert users.status_code == 200, users.text
    assert users.json()[0]["course_count"] == 1
    assert users.json()[0]["lesson_count"] == 2

    filtered = admin_client.get(
        "/api/v1/admin/content",
        params={"source": "ai", "user_id": users.json()[0]["user_id"]},
    )
    assert filtered.status_code == 200, filtered.text
    assert filtered.json()["total"] == 2


def test_admin_user_picker_lists_users_without_ai_content(
    admin_client: TestClient, fakes: SimpleNamespace
) -> None:
    empty_user = fakes.users.create(
        firebase_uid="learner-without-content",
        email="new-learner@example.com",
        display_name="New learner",
    )

    response = admin_client.get("/api/v1/admin/content/users?source=ai")

    assert response.status_code == 200, response.text
    option = next(
        item for item in response.json() if item["user_id"] == str(empty_user.id)
    )
    assert option["course_count"] == 0
    assert option["lesson_count"] == 0
    assert option["pending"] == 0


def test_admin_previews_lesson_exercises_and_quiz_answers(
    admin_client: TestClient, fakes: SimpleNamespace
) -> None:
    _, lesson = _ai_lesson(fakes)
    exercise = fakes.exercises.create(
        lesson_id=lesson.id,
        language="python",
        title="Decorator exercise",
        slug="decorator-exercise",
        prompt="Write a decorator",
        starter_code="def decorator(fn):\n    pass\n",
        test_spec={"cases": [{"input": "", "expected": "ok"}]},
        source="ai",
    )
    quiz = fakes.quizzes.create(
        lesson_id=lesson.id,
        title="Decorator quiz",
        slug="decorator-quiz",
        description=None,
    )
    fakes.quizzes.add_question(
        quiz_id=quiz.id,
        prompt="What wraps a function?",
        type="single",
        order_index=0,
        choices=[
            {"text": "A decorator", "is_correct": True},
            {"text": "A list", "is_correct": False},
        ],
        explanation="Decorators wrap callables.",
    )

    response = admin_client.get(f"/api/v1/admin/content/lessons/{lesson.id}/preview")

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["content"] == "# Decorators"
    assert body["exercises"][0]["id"] == str(exercise.id)
    assert body["quizzes"][0]["questions"][0]["choices"][0]["is_correct"] is True


def test_admin_marks_only_pending_ai_lessons_reviewed_for_course(
    admin_client: TestClient, fakes: SimpleNamespace
) -> None:
    course, pending = _ai_lesson(fakes)
    hidden = fakes.lessons.create(
        course_id=course.id,
        title="Hidden lesson",
        slug="hidden-lesson",
        order_index=1,
        content="Hidden",
        source="ai",
        review_status="hidden",
    )
    fakes.lessons.create(
        course_id=course.id,
        title="Human lesson",
        slug="human-lesson",
        order_index=2,
        content="Human",
        source="human",
        review_status="pending",
    )

    response = admin_client.post(f"/api/v1/admin/content/courses/{course.id}/approve")

    assert response.status_code == 200, response.text
    assert response.json()["reviewed"] == 1
    assert fakes.lessons.get_by_id(pending.id).review_status == "approved"
    assert fakes.lessons.get_by_id(hidden.id).review_status == "hidden"


def test_hide_excludes_from_serving_then_approve_restores(
    admin_client: TestClient, fakes: SimpleNamespace
) -> None:
    _, lesson = _ai_lesson(fakes)
    # Served while visible.
    assert admin_client.get(f"/api/v1/lessons/{lesson.id}").status_code == 200

    hide = admin_client.post(f"/api/v1/admin/content/lessons/{lesson.id}/hide")
    assert hide.status_code == 200, hide.text
    assert hide.json()["review_status"] == "hidden"
    # Hidden content is no longer served to learners.
    assert admin_client.get(f"/api/v1/lessons/{lesson.id}").status_code == 404

    approve = admin_client.post(f"/api/v1/admin/content/lessons/{lesson.id}/approve")
    assert approve.status_code == 200
    assert approve.json()["review_status"] == "approved"
    assert admin_client.get(f"/api/v1/lessons/{lesson.id}").status_code == 200


def test_hide_unknown_lesson_404(admin_client: TestClient) -> None:
    import uuid

    assert (
        admin_client.post(f"/api/v1/admin/content/lessons/{uuid.uuid4()}/hide").status_code
        == 404
    )


def test_admin_usage_counts(admin_client: TestClient, fakes: SimpleNamespace) -> None:
    _ai_lesson(fakes)
    usage = admin_client.get("/api/v1/admin/usage").json()
    assert usage["ai_lessons"] >= 1
    assert usage["pending"] >= 1
