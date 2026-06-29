# 04 — API

## Conventions

- Base path: `/api/v1`.
- JSON request/response bodies.
- Auth: `Authorization: Bearer <firebase-id-token>` (verified server-side;
  stubbed in Sprint 0).
- Errors use a consistent envelope:

```json
{ "detail": "Human readable message" }
```

- Interactive docs: `GET /docs` (Swagger), `GET /redoc`, schema at
  `GET /api/v1/openapi.json`.

## Implemented

| Method | Path | Auth | Sprint | Description |
|--------|------|------|--------|-------------|
| GET | `/health` | none | 0 | Liveness + version. |
| GET | `/api/v1/health` | none | 0 | Versioned health (db check). |
| GET | `/api/v1/me` | bearer | 1 | DB-backed current user (provisions on first login). |
| GET | `/api/v1/me/profile` | bearer | 1 | Current user's profile. |
| PUT | `/api/v1/me/profile` | bearer | 1 | Update display name / skill level. |
| GET | `/api/v1/languages` | none | 2 | List programming languages. |
| GET | `/api/v1/courses` | none | 2 | List courses. |
| GET | `/api/v1/courses/{slug}` | none | 2 | Course detail with ordered lessons. |
| GET | `/api/v1/lessons/{id}` | none | 2 | Single lesson (markdown content). |
| POST/PUT/DELETE | `/api/v1/admin/languages[/{id}]` | admin | 2 | Manage languages. |
| POST/PUT/DELETE | `/api/v1/admin/courses[/{id}]` | admin | 2 | Manage courses. |
| POST/PUT/DELETE | `/api/v1/admin/lessons[/{id}]` | admin | 2 | Manage lessons. |

### `GET /health`

```json
{ "status": "ok", "service": "codepath-api", "version": "0.1.0" }
```

### `GET /api/v1/health`

```json
{ "status": "ok", "database": "ok" }
```

### `GET /api/v1/me`

Requires `Authorization: Bearer <token>`. Resolves the token to a persisted
user, creating the `User` (and an empty `StudentProfile`) on first sign-in. With
`AUTH_STUB_ENABLED=true` the auth middleware accepts a fixed dev identity.

```json
{
  "id": "0f9b…-uuid",
  "uid": "stub-uid",
  "email": "dev@codepath.local",
  "display_name": null,
  "is_admin": false
}
```

### `GET /api/v1/me/profile`

```json
{ "display_name": null, "email": "dev@codepath.local", "skill_level": "beginner", "is_admin": false }
```

### `PUT /api/v1/me/profile`

Body (both fields optional; only provided fields change):

```json
{ "display_name": "Ada", "skill_level": "intermediate" }
```

Returns the updated `ProfileResponse` (same shape as the `GET`).

### Content (Sprint 2)

Reads are public; writes require an **admin** user (`is_admin = true`) and
return `403` otherwise. Duplicate slugs return `409`.

```jsonc
// GET /api/v1/courses/python-basics
{
  "id": "…", "language_id": "…", "title": "Python Basics",
  "slug": "python-basics", "description": "…",
  "lessons": [
    { "id": "…", "title": "Variables & Types", "slug": "variables-and-types", "order_index": 1 }
  ]
}
```

```jsonc
// POST /api/v1/admin/lessons   (admin)
{ "course_id": "…", "title": "Functions", "slug": "functions", "order_index": 3, "content": "# Functions\n…" }
```

Promote a user to admin with `python -m scripts.set_admin <email>` in the
backend container.

## Planned endpoints (later sprints — not implemented)

These are documented for design alignment only. Sprint numbers follow the
[Sprint_03…08](Sprint_03.md) plan.

| Sprint | Resource | Endpoints (sketch) |
|--------|----------|--------------------|
| 3 | Exercises | `GET /exercises/{id}`, `POST /exercises/{id}/submit` |
| 4 | Execution | `POST /exercises/{id}/run`, `GET /submissions/{id}` |
| 5 | Quizzes | `GET /quizzes/{id}`, `POST /quizzes/{id}/submit` |
| 6 | AI | `POST /ai/teacher`, `POST /ai/tutor` |
| 7 | Today | `GET /today` |
| 7 | Progress | `GET /progress` |
| 8 | Subscription | `GET /subscription`, `POST /subscription/checkout` |

## Versioning

The API is namespaced under `/api/v1`. Breaking changes introduce `/api/v2`
rather than mutating v1.
