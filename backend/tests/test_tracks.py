"""API tests for language tracks + onboarding (in-memory fakes)."""

import uuid
from types import SimpleNamespace

from fastapi.testclient import TestClient


def _lang(fakes: SimpleNamespace, name: str, slug: str):
    return fakes.languages.create(name=name, slug=slug)


def _provisioned_user_id(fakes: SimpleNamespace) -> uuid.UUID:
    return next(iter(fakes.users._by_id.values())).id


def test_new_user_is_not_onboarded(client: TestClient) -> None:
    res = client.get("/api/v1/me")
    assert res.status_code == 200
    assert res.json()["onboarded"] is False


def test_add_track_onboards_user(client: TestClient, fakes: SimpleNamespace) -> None:
    python = _lang(fakes, "Python", "python")
    res = client.post("/api/v1/me/tracks", json={"language_id": str(python.id)})
    assert res.status_code == 201, res.text
    body = res.json()
    assert body["language_name"] == "Python"

    assert client.get("/api/v1/me").json()["onboarded"] is True
    tracks = client.get("/api/v1/me/tracks").json()
    assert len(tracks) == 1


def test_add_track_unknown_language_404(client: TestClient) -> None:
    res = client.post("/api/v1/me/tracks", json={"language_id": str(uuid.uuid4())})
    assert res.status_code == 404


def test_duplicate_track_409(client: TestClient, fakes: SimpleNamespace) -> None:
    python = _lang(fakes, "Python", "python")
    client.post("/api/v1/me/tracks", json={"language_id": str(python.id)})
    dup = client.post("/api/v1/me/tracks", json={"language_id": str(python.id)})
    assert dup.status_code == 409


def test_free_user_capped_at_two_languages(client: TestClient, fakes: SimpleNamespace) -> None:
    for name, slug in [("Python", "python"), ("Go", "go"), ("Rust", "rust")]:
        lang = _lang(fakes, name, slug)
        res = client.post("/api/v1/me/tracks", json={"language_id": str(lang.id)})
        if slug == "rust":
            assert res.status_code == 402  # third one is blocked
        else:
            assert res.status_code == 201, res.text


def test_subscriber_exceeds_language_cap(client: TestClient, fakes: SimpleNamespace) -> None:
    langs = [_lang(fakes, n, s) for n, s in [("Python", "python"), ("Go", "go"), ("Rust", "rust")]]
    # Provision the user, then give them an active subscription.
    client.get("/api/v1/me")
    fakes.subscriptions.upsert(
        user_id=_provisioned_user_id(fakes), plan="pro", status="active"
    )
    for lang in langs:
        res = client.post("/api/v1/me/tracks", json={"language_id": str(lang.id)})
        assert res.status_code == 201, res.text


def test_remove_track(client: TestClient, fakes: SimpleNamespace) -> None:
    python = _lang(fakes, "Python", "python")
    created = client.post("/api/v1/me/tracks", json={"language_id": str(python.id)}).json()
    assert client.delete(f"/api/v1/me/tracks/{created['id']}").status_code == 204
    assert client.get("/api/v1/me/tracks").json() == []
    assert client.get("/api/v1/me").json()["onboarded"] is False
