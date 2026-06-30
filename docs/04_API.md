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
| GET | `/api/v1/lessons/{id}/exercises` | none | 3 | List a lesson's exercises. |
| GET | `/api/v1/exercises/{id}` | none | 3 | Exercise (prompt + starter code; no test spec). |
| POST | `/api/v1/exercises/{id}/submit` | bearer | 3 | Store a submission, graded in the background. |
| GET | `/api/v1/exercises/{id}/submissions` | bearer | 3 | Current user's submissions for the exercise. |
| POST | `/api/v1/admin/exercises` | admin | 3 | Create an exercise. |
| DELETE | `/api/v1/admin/exercises/{id}` | admin | 3 | Delete an exercise. |
| POST | `/api/v1/exercises/{id}/run` | bearer | 4 | Run code once against stdin (no grading). |
| GET | `/api/v1/submissions/{id}` | bearer | 4 | Poll a submission's verdict (own only). |
| GET | `/api/v1/lessons/{id}/quizzes` | none | 5 | List a lesson's quizzes. |
| GET | `/api/v1/quizzes/{id}` | none | 5 | Quiz with questions/choices (no answer key). |
| POST | `/api/v1/quizzes/{id}/submit` | bearer | 5 | Auto-grade answers; returns score + per-question result. |
| GET | `/api/v1/quizzes/{id}/attempts` | bearer | 5 | Current user's attempts for the quiz. |
| POST | `/api/v1/admin/quizzes` | admin | 5 | Create a quiz. |
| POST | `/api/v1/admin/quizzes/{id}/questions` | admin | 5 | Add a question (with choices). |
| DELETE | `/api/v1/admin/quizzes/{id}` | admin | 5 | Delete a quiz. |

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

### Exercises & submissions (Sprint 3)

Reads are public; submitting requires a signed-in learner. A submission is
stored with `status: "pending"` — execution and grading arrive in Sprint 4.
The exercise read never includes `test_spec` (hidden test cases).

```jsonc
// POST /api/v1/exercises/{id}/submit   { "code": "print('hi')" }  -> 201 (pending)
{ "id": "…", "exercise_id": "…", "code": "print('hi')", "status": "pending", "result": null, "created_at": "…" }
```

### Execution & grading (Sprint 4)

`POST /exercises/{id}/run` runs the code once (no grading) and returns
stdout/stderr. `POST …/submit` now schedules **background grading** via Judge0;
the client polls `GET /submissions/{id}` until `status` leaves `pending`
(`passed` | `failed` | `error`). Verdicts and per-test results are persisted on
the submission; hidden test cases never reveal their I/O. If Judge0 is
unreachable, run/submit degrade gracefully (an `error` result, not a `500`).

```jsonc
// GET /api/v1/submissions/{id}  (after grading)
{ "id": "…", "status": "passed",
  "result": { "verdict": "passed", "passed": 1, "total": 1, "tests": [ { "index": 0, "passed": true } ] } }
```

Judge0 is opt-in: `docker compose --profile judge0 up`.

### Quizzes (Sprint 5)

`GET /quizzes/{id}` returns the quiz with its questions and choices but **never**
the `is_correct` answer key. `POST /quizzes/{id}/submit` takes a map of
`question_id → choice_id`, auto-grades it, stores a `QuizAttempt`, and returns
the score plus per-question correctness (revealing the correct choice for
feedback). Admins author quizzes via the admin endpoints.

```jsonc
// GET /api/v1/quizzes/{id}
{ "id": "…", "title": "Basics", "questions": [
  { "id": "q1", "prompt": "2 + 2 = ?", "type": "single",
    "choices": [ { "id": "c1", "text": "4" }, { "id": "c2", "text": "5" } ] } ] }

// POST /api/v1/quizzes/{id}/submit   { "answers": { "q1": "c1" } }
{ "attempt_id": "…", "score": 1, "total": 1,
  "results": [ { "question_id": "q1", "correct": true,
                 "selected_choice_id": "c1", "correct_choice_id": "c1" } ] }
```

## Planned endpoints (later sprints — not implemented)

These are documented for design alignment only. Sprint numbers follow the
[Sprint_06…08](Sprint_06.md) plan.

| Sprint | Resource | Endpoints (sketch) |
|--------|----------|--------------------|
| 6 | AI | `POST /ai/teacher`, `POST /ai/tutor` |
| 7 | Today | `GET /today` |
| 7 | Progress | `GET /progress` |
| 8 | Subscription | `GET /subscription`, `POST /subscription/checkout` |

## Versioning

The API is namespaced under `/api/v1`. Breaking changes introduce `/api/v2`
rather than mutating v1.
