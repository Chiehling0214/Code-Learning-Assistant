"""API tests for /me and /me/profile (service backed by in-memory fakes).

Auth runs in stub mode by default, so the stub identity is provisioned.
"""

from app.core.config import Settings, get_settings
from app.main import app
from fastapi.testclient import TestClient


def test_me_requires_token_when_stub_disabled(client: TestClient) -> None:
    # With real auth enabled and no Authorization header, /me must reject.
    app.dependency_overrides[get_settings] = lambda: Settings(auth_stub_enabled=False)
    try:
        response = client.get("/api/v1/me")
    finally:
        del app.dependency_overrides[get_settings]
    assert response.status_code == 401


def test_me_provisions_and_returns_db_user(client: TestClient) -> None:
    response = client.get("/api/v1/me")
    assert response.status_code == 200
    body = response.json()
    assert body["uid"] == "stub-uid"
    assert body["email"] == "dev@codepath.local"
    assert "id" in body


def test_get_profile_returns_default_skill_level(client: TestClient) -> None:
    response = client.get("/api/v1/me/profile")
    assert response.status_code == 200
    assert response.json()["skill_level"] == "beginner"


def test_update_profile_persists_changes(client: TestClient) -> None:
    client.get("/api/v1/me")  # provision first

    update = client.put(
        "/api/v1/me/profile",
        json={"display_name": "Grace", "skill_level": "advanced"},
    )
    assert update.status_code == 200
    assert update.json() == {
        "display_name": "Grace",
        "email": "dev@codepath.local",
        "skill_level": "advanced",
        "is_admin": False,
    }

    # Change is reflected on a subsequent read.
    after = client.get("/api/v1/me/profile")
    assert after.json()["display_name"] == "Grace"
    assert after.json()["skill_level"] == "advanced"
