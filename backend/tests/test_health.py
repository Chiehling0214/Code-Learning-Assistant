"""Smoke test for the liveness endpoint (no database required)."""

from app.main import app
from fastapi.testclient import TestClient


def test_liveness_returns_ok() -> None:
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "codepath-api"
    assert "version" in body
