"""Shared pytest fixtures.

Overrides service dependencies with ones backed by in-memory fakes so the API
can be exercised without a real database.
"""

import uuid
from collections.abc import Iterator
from datetime import UTC, datetime

import pytest
from app.api.deps import get_content_service, get_current_db_user, get_user_service
from app.application.services.content_service import ContentService
from app.application.services.user_service import UserService
from app.domain.entities import User
from app.main import app
from fastapi.testclient import TestClient

from tests.fakes import (
    FakeCourseRepository,
    FakeLanguageRepository,
    FakeLessonRepository,
    FakeStudentProfileRepository,
    FakeUserRepository,
)


@pytest.fixture
def user_service() -> UserService:
    return UserService(FakeUserRepository(), FakeStudentProfileRepository())


@pytest.fixture
def content_service() -> ContentService:
    return ContentService(
        FakeLanguageRepository(), FakeCourseRepository(), FakeLessonRepository()
    )


@pytest.fixture
def client(user_service: UserService, content_service: ContentService) -> Iterator[TestClient]:
    app.dependency_overrides[get_user_service] = lambda: user_service
    app.dependency_overrides[get_content_service] = lambda: content_service
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
