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

## Planned endpoints (later sprints — not implemented)

These are documented for design alignment only. Sprint numbers follow the
[Sprint_02…08](Sprint_02.md) plan.

| Sprint | Resource | Endpoints (sketch) |
|--------|----------|--------------------|
| 2 | Languages | `GET /languages` |
| 2 | Courses | `GET /courses`, `GET /courses/{slug}` |
| 2 | Lessons | `GET /lessons/{id}` |
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
