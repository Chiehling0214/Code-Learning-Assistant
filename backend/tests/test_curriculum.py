"""Tests for AI curriculum generation (AI + Judge0 mocked, no network)."""

import uuid
from types import SimpleNamespace

from app.application.services.ai_usage import AIUsageGuard
from app.application.services.curriculum_service import CurriculumService
from app.application.services.execution_service import ExecutionService
from app.core.config import Settings
from fastapi.testclient import TestClient

_SETTINGS = Settings(
    curriculum_lesson_count=3,
    curriculum_exercises_per_lesson=2,
    curriculum_quiz_questions=2,
    curriculum_batch_pause_seconds=0,
)


def _service(fakes: SimpleNamespace) -> CurriculumService:
    return CurriculumService(
        fakes.ai,
        fakes.jobs,
        fakes.courses,
        fakes.lessons,
        fakes.exercises,
        fakes.quizzes,
        fakes.languages,
        fakes.tracks,
        ExecutionService(fakes.runner),
        AIUsageGuard(fakes.interactions, _SETTINGS),
        _SETTINGS,
    )


def _track(fakes: SimpleNamespace, user_id: uuid.UUID, level: str = "beginner"):
    lang = fakes.languages.create(name="Python", slug="python")
    track = fakes.tracks.create(user_id=user_id, language_id=lang.id)
    fakes.tracks.set_level(track.id, level)
    return lang, track


# ----- generation logic (unit, direct) -----


def test_generate_course_builds_full_curriculum(fakes: SimpleNamespace) -> None:
    user_id = uuid.uuid4()
    lang, track = _track(fakes, user_id)
    service = _service(fakes)

    job = service.start_generation(user_id=user_id, track_id=track.id)
    service.generate_course(job.id)

    # One course, scoped to the track, with the configured number of lessons.
    courses = fakes.courses.list_by_track_ids([track.id])
    assert len(courses) == 1
    course = courses[0]

    lessons = fakes.lessons.list_by_course(course.id)
    assert len(lessons) == 3
    for lesson in lessons:
        exercises = fakes.exercises.list_by_lesson(lesson.id)
        assert len(exercises) == 2
        assert all(ex.source == "ai" for ex in exercises)
        assert lesson.source == "ai"
        quizzes = fakes.quizzes.list_by_lesson(lesson.id)
        assert len(quizzes) == 1

    done = fakes.jobs.get_by_id(job.id)
    assert done.status == "done"
    assert done.completed == 3


def test_start_generation_is_idempotent_while_active(fakes: SimpleNamespace) -> None:
    user_id = uuid.uuid4()
    _, track = _track(fakes, user_id)
    service = _service(fakes)
    first = service.start_generation(user_id=user_id, track_id=track.id)
    second = service.start_generation(user_id=user_id, track_id=track.id)
    assert first.id == second.id  # a pending job is reused, not duplicated


def test_start_generation_unknown_track_raises(fakes: SimpleNamespace) -> None:
    service = _service(fakes)
    try:
        service.start_generation(user_id=uuid.uuid4(), track_id=uuid.uuid4())
        raise AssertionError("expected LookupError")
    except LookupError:
        pass


# ----- API -----


def test_generate_endpoint_returns_pending_job(
    client: TestClient, fakes: SimpleNamespace
) -> None:
    lang = fakes.languages.create(name="Python", slug="python")
    track_id = client.post("/api/v1/me/tracks", json={"language_id": str(lang.id)}).json()["id"]

    res = client.post(f"/api/v1/me/tracks/{track_id}/generate")
    assert res.status_code == 202, res.text
    assert res.json()["status"] == "pending"

    status = client.get(f"/api/v1/me/tracks/{track_id}/generation")
    assert status.status_code == 200
    assert status.json()["track_id"] == track_id


def test_generate_unknown_track_404(client: TestClient) -> None:
    assert client.post(f"/api/v1/me/tracks/{uuid.uuid4()}/generate").status_code == 404


def test_my_courses_lists_only_owned(client: TestClient, fakes: SimpleNamespace) -> None:
    lang = fakes.languages.create(name="Python", slug="python")
    track_id = client.post("/api/v1/me/tracks", json={"language_id": str(lang.id)}).json()["id"]
    # A course on my track, and one on someone else's track.
    fakes.courses.create(
        language_id=lang.id,
        title="Mine",
        slug="mine",
        description=None,
        track_id=uuid.UUID(track_id),
    )
    fakes.courses.create(
        language_id=lang.id, title="Other", slug="other", description=None, track_id=uuid.uuid4()
    )

    res = client.get("/api/v1/me/courses")
    assert res.status_code == 200
    slugs = [c["slug"] for c in res.json()]
    assert slugs == ["mine"]
