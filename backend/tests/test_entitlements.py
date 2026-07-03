"""API tests for plan entitlements (Sprint 13)."""

from types import SimpleNamespace

from fastapi.testclient import TestClient


def test_entitlements_free_defaults(client: TestClient) -> None:
    body = client.get("/api/v1/me/entitlements").json()
    assert body["plan"] == "free"
    assert body["max_languages"] == 2
    assert body["tutor_daily"] == 5
    assert body["generations_daily"] == 10
    assert body["languages_used"] == 0
    assert body["tutor_used_today"] == 0
    assert body["generations_used_today"] == 0


def test_entitlements_reflect_usage_and_plan(client: TestClient, fakes: SimpleNamespace) -> None:
    user = fakes.users.create(firebase_uid="stub-uid", email="dev@codepath.local")
    lang = fakes.languages.create(name="Python", slug="python")
    fakes.tracks.create(user_id=user.id, language_id=lang.id)
    fakes.interactions.create(user_id=user.id, kind="tutor", model="m", total_tokens=1)
    fakes.interactions.create(user_id=user.id, kind="generate", model="m", total_tokens=1)

    # Free plan reflects current usage.
    body = client.get("/api/v1/me/entitlements").json()
    assert body["plan"] == "free"
    assert body["languages_used"] == 1
    assert body["tutor_used_today"] == 1
    assert body["generations_used_today"] == 1

    # Activating a subscription raises the limits.
    fakes.subscriptions.upsert(user_id=user.id, plan="pro", status="active")
    upgraded = client.get("/api/v1/me/entitlements").json()
    assert upgraded["plan"] == "pro"
    assert upgraded["max_languages"] == 20
    assert upgraded["tutor_daily"] == 100
    assert upgraded["generations_daily"] == 100
