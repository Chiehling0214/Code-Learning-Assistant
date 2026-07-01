"""Shared pytest fixtures.

Overrides service dependencies with ones backed by in-memory fakes (shared via
the ``fakes`` namespace so multi-step flows persist state) — the suite runs
without a real database.
"""

import uuid
from collections.abc import Iterator
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest
from app.api.deps import (
    get_ai_teacher_service,
    get_ai_tutor_service,
    get_content_service,
    get_current_db_user,
    get_execution_service,
    get_exercise_service,
    get_generate_content_service,
    get_progress_service,
    get_quiz_service,
    get_recommendation_service,
    get_submission_service,
    get_user_service,
)
from app.application.services.ai_teacher_service import AITeacherService
from app.application.services.ai_tutor_service import AITutorService
from app.application.services.ai_usage import AIUsageGuard
from app.application.services.content_service import ContentService
from app.application.services.execution_service import ExecutionService
from app.application.services.exercise_service import ExerciseService
from app.application.services.generate_content_service import GenerateContentService
from app.application.services.progress_service import ProgressService
from app.application.services.quiz_service import QuizService
from app.application.services.recommendation_service import RecommendationService
from app.application.services.submission_service import SubmissionService
from app.application.services.user_service import UserService
from app.core.config import Settings
from app.domain.entities import User
from app.main import app
from fastapi.testclient import TestClient

from tests.fakes import (
    FakeAIInteractionRepository,
    FakeAIProvider,
    FakeCodeRunner,
    FakeCourseRepository,
    FakeExerciseRepository,
    FakeLanguageRepository,
    FakeLessonRepository,
    FakeProgressRepository,
    FakeQuizAttemptRepository,
    FakeQuizRepository,
    FakeStudentProfileRepository,
    FakeSubmissionRepository,
    FakeUserRepository,
)

# Small per-user AI limits so the rate-limit test stays fast and deterministic.
_AI_SETTINGS = Settings(ai_rate_limit_per_minute=5, ai_daily_limit=100)


@pytest.fixture
def fakes() -> SimpleNamespace:
    """One shared set of in-memory repositories for a test."""
    return SimpleNamespace(
        users=FakeUserRepository(),
        profiles=FakeStudentProfileRepository(),
        languages=FakeLanguageRepository(),
        courses=FakeCourseRepository(),
        lessons=FakeLessonRepository(),
        exercises=FakeExerciseRepository(),
        submissions=FakeSubmissionRepository(),
        runner=FakeCodeRunner(),
        quizzes=FakeQuizRepository(),
        attempts=FakeQuizAttemptRepository(),
        ai=FakeAIProvider(),
        interactions=FakeAIInteractionRepository(),
        progress=FakeProgressRepository(),
    )


@pytest.fixture
def client(fakes: SimpleNamespace) -> Iterator[TestClient]:
    app.dependency_overrides[get_user_service] = lambda: UserService(
        fakes.users, fakes.profiles
    )
    app.dependency_overrides[get_content_service] = lambda: ContentService(
        fakes.languages, fakes.courses, fakes.lessons
    )
    app.dependency_overrides[get_exercise_service] = lambda: ExerciseService(
        fakes.exercises, fakes.lessons
    )
    app.dependency_overrides[get_submission_service] = lambda: SubmissionService(
        fakes.submissions, fakes.exercises
    )
    app.dependency_overrides[get_execution_service] = lambda: ExecutionService(fakes.runner)
    app.dependency_overrides[get_quiz_service] = lambda: QuizService(
        fakes.quizzes, fakes.attempts, fakes.lessons, fakes.progress
    )
    app.dependency_overrides[get_progress_service] = lambda: ProgressService(
        fakes.courses, fakes.lessons, fakes.exercises, fakes.quizzes, fakes.progress
    )
    app.dependency_overrides[get_recommendation_service] = lambda: RecommendationService(
        fakes.courses, fakes.lessons, fakes.exercises, fakes.quizzes, fakes.progress
    )

    def _guard() -> AIUsageGuard:
        return AIUsageGuard(fakes.interactions, _AI_SETTINGS)

    app.dependency_overrides[get_ai_teacher_service] = lambda: AITeacherService(
        fakes.ai, fakes.lessons, _guard()
    )
    app.dependency_overrides[get_ai_tutor_service] = lambda: AITutorService(
        fakes.ai, fakes.exercises, _guard()
    )
    app.dependency_overrides[get_generate_content_service] = lambda: GenerateContentService(
        fakes.ai,
        ContentService(fakes.languages, fakes.courses, fakes.lessons),
        ExerciseService(fakes.exercises, fakes.lessons),
        ExecutionService(fakes.runner),
        _guard(),
    )
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def admin_client(client: TestClient) -> TestClient:
    """A client whose current user is an admin (passes the require_admin guard)."""
    now = datetime.now(UTC)
    admin = User(
        id=uuid.uuid4(),
        firebase_uid="admin-uid",
        email="admin@codepath.local",
        display_name="Admin",
        is_admin=True,
        created_at=now,
        updated_at=now,
    )
    app.dependency_overrides[get_current_db_user] = lambda: admin
    return client
