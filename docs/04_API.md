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

## Implemented in Sprint 0

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/health` | none | Liveness + version. |
| GET | `/api/v1/health` | none | Versioned health (db check). |
| GET | `/api/v1/me` | bearer | Returns the current (stub) identity. |

### `GET /health`

```json
{ "status": "ok", "service": "codepath-api", "version": "0.1.0" }
```

### `GET /api/v1/health`

```json
{ "status": "ok", "database": "ok" }
```

### `GET /api/v1/me`

Requires `Authorization: Bearer <token>`. In Sprint 0 the auth middleware runs
in stub mode and returns a fixed development identity.

```json
{ "uid": "stub-uid", "email": "dev@codepath.local", "is_admin": false }
```

## Planned endpoints (later sprints — not implemented)

These are documented for design alignment only.

| Sprint | Resource | Endpoints (sketch) |
|--------|----------|--------------------|
| 1 | Courses | `GET /courses`, `GET /courses/{slug}` |
| 1 | Languages | `GET /languages` |
| 1 | Profile | `GET/PUT /me/profile` |
| 2 | Exercises | `GET /exercises/{id}`, `POST /exercises/{id}/submit` |
| 3 | Quizzes | `GET /quizzes/{id}`, `POST /quizzes/{id}/submit` |
| 4 | AI | `POST /ai/teacher`, `POST /ai/tutor` |
| 5 | Today | `GET /today` |
| 5 | Progress | `GET /progress` |
| 6 | Subscription | `GET /subscription`, `POST /subscription/checkout` |

## Versioning

The API is namespaced under `/api/v1`. Breaking changes introduce `/api/v2`
rather than mutating v1.
