"""Unit tests for UserService using in-memory fake repositories."""

from app.application.services.user_service import UserService
from app.core.security import Identity

from tests.fakes import FakeStudentProfileRepository, FakeUserRepository


def _service() -> tuple[UserService, FakeUserRepository, FakeStudentProfileRepository]:
    users = FakeUserRepository()
    profiles = FakeStudentProfileRepository()
    return UserService(users, profiles), users, profiles


def test_provisions_user_and_profile_on_first_login() -> None:
    service, users, profiles = _service()
    identity = Identity(uid="abc123", email="learner@example.com", is_admin=False)

    user = service.get_or_create_from_identity(identity)

    assert user.firebase_uid == "abc123"
    assert user.email == "learner@example.com"
    assert users.get_by_firebase_uid("abc123") is not None
    assert profiles.get_by_user_id(user.id) is not None


def test_get_or_create_is_idempotent() -> None:
    service, _, _ = _service()
    identity = Identity(uid="abc123", email="learner@example.com")

    first = service.get_or_create_from_identity(identity)
    second = service.get_or_create_from_identity(identity)

    assert first.id == second.id


def test_update_profile_changes_name_and_skill_level() -> None:
    service, _, _ = _service()
    user = service.get_or_create_from_identity(Identity(uid="abc123", email="a@b.com"))

    updated_user, profile = service.update_profile(
        user.id, display_name="Ada", skill_level="intermediate"
    )

    assert updated_user.display_name == "Ada"
    assert profile.skill_level == "intermediate"


def test_update_profile_partial_leaves_other_field() -> None:
    service, _, _ = _service()
    user = service.get_or_create_from_identity(Identity(uid="abc123", email="a@b.com"))

    _, profile = service.update_profile(user.id, display_name="Ada", skill_level=None)

    assert profile.skill_level == "beginner"
