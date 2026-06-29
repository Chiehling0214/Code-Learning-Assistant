"""API tests for content endpoints (languages, courses, lessons) + admin guard.

Backed by in-memory fakes; no database required. Auth runs in stub mode, so the
default ``client`` is a non-admin user and ``admin_client`` is an admin.
"""

from fastapi.testclient import TestClient


def _create_language(admin_client: TestClient, name="Python", slug="python") -> dict:
    res = admin_client.post("/api/v1/admin/languages", json={"name": name, "slug": slug})
    assert res.status_code == 201, res.text
    return res.json()


def _create_course(admin_client: TestClient, language_id: str, slug="python-basics") -> dict:
    res = admin_client.post(
        "/api/v1/admin/courses",
        json={"language_id": language_id, "title": "Python Basics", "slug": slug},
    )
    assert res.status_code == 201, res.text
    return res.json()


# ----- public reads -----


def test_list_languages_empty(client: TestClient) -> None:
    res = client.get("/api/v1/languages")
    assert res.status_code == 200
    assert res.json() == []


def test_course_detail_returns_ordered_lessons(admin_client: TestClient) -> None:
    lang = _create_language(admin_client)
    course = _create_course(admin_client, lang["id"])
    # Insert lessons out of order; the API should return them sorted.
    for title, slug, order in [("Second", "second", 2), ("First", "first", 1)]:
        admin_client.post(
            "/api/v1/admin/lessons",
            json={
                "course_id": course["id"],
                "title": title,
                "slug": slug,
                "order_index": order,
                "content": f"# {title}",
            },
        )

    res = admin_client.get("/api/v1/courses/python-basics")
    assert res.status_code == 200
    body = res.json()
    assert body["slug"] == "python-basics"
    assert [ln["order_index"] for ln in body["lessons"]] == [1, 2]
    assert body["lessons"][0]["title"] == "First"


def test_course_detail_404_when_missing(client: TestClient) -> None:
    assert client.get("/api/v1/courses/nope").status_code == 404


def test_get_lesson_returns_content(admin_client: TestClient) -> None:
    lang = _create_language(admin_client)
    course = _create_course(admin_client, lang["id"])
    created = admin_client.post(
        "/api/v1/admin/lessons",
        json={
            "course_id": course["id"],
            "title": "Intro",
            "slug": "intro",
            "order_index": 1,
            "content": "# Intro\n\nhello",
        },
    ).json()

    res = admin_client.get(f"/api/v1/lessons/{created['id']}")
    assert res.status_code == 200
    assert res.json()["content"] == "# Intro\n\nhello"


# ----- admin guard -----


def test_non_admin_cannot_create_language(client: TestClient) -> None:
    # Default stub user has is_admin=False.
    res = client.post("/api/v1/admin/languages", json={"name": "Go", "slug": "go"})
    assert res.status_code == 403


def test_admin_can_create_and_delete_language(admin_client: TestClient) -> None:
    lang = _create_language(admin_client, name="Go", slug="go")
    assert lang["name"] == "Go"

    listed = admin_client.get("/api/v1/languages").json()
    assert any(x["slug"] == "go" for x in listed)

    deleted = admin_client.delete(f"/api/v1/admin/languages/{lang['id']}")
    assert deleted.status_code == 204
    assert admin_client.get("/api/v1/languages").json() == []


def test_create_course_404_for_unknown_language(admin_client: TestClient) -> None:
    res = admin_client.post(
        "/api/v1/admin/courses",
        json={
            "language_id": "00000000-0000-0000-0000-000000000000",
            "title": "X",
            "slug": "x",
        },
    )
    assert res.status_code == 404
