"""Smoke test for the liveness endpoint (no database required)."""

from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_liveness_returns_ok() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "codepath-api"
    assert "version" in body


def test_me_returns_stub_identity() -> None:
    # Auth runs in stub mode by default, so no real token is needed.
    response = client.get("/api/v1/me")
    assert response.status_code == 200
    body = response.json()
    assert body["uid"] == "stub-uid"
