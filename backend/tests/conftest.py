"""Shared pytest fixtures.

Overrides the user-service dependency with one backed by in-memory fakes so the
API can be exercised without a real database.
"""

from collections.abc import Iterator

import pytest
from app.api.deps import get_user_service
from app.application.services.user_service import UserService
from app.main import app
from fastapi.testclient import TestClient

from tests.fakes import FakeStudentProfileRepository, FakeUserRepository


@pytest.fixture
def user_service() -> UserService:
    return UserService(FakeUserRepository(), FakeStudentProfileRepository())


@pytest.fixture
def client(user_service: UserService) -> Iterator[TestClient]:
    app.dependency_overrides[get_user_service] = lambda: user_service
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
