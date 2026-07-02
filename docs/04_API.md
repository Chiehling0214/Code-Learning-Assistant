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
| POST | `/api/v1/ai/teacher` | bearer | 6 | AI explanation for a lesson/topic/question. |
| POST | `/api/v1/ai/tutor` | bearer | 6 | AI hint on the submitted code (not the answer). |
| POST | `/api/v1/admin/ai/generate` | admin | 6 | Generate a lesson/exercise into the content tables. |
| GET | `/api/v1/today` | bearer | 7 | Personalized ordered plan of next items. |
| GET | `/api/v1/progress` | bearer | 7 | Per-course completion, totals, and streak. |
| POST | `/api/v1/lessons/{id}/complete` | bearer | 7 | Mark a lesson complete. |
| GET | `/api/v1/subscription` | bearer | 8 | Current subscription status. |
| POST | `/api/v1/subscription/checkout` | bearer | 8 | Start a Stripe checkout session. |
| POST | `/api/v1/webhooks/stripe` | signature | 8 | Stripe webhook (verified). |
| GET | `/api/v1/me/tracks` | bearer | 9 | The learner's language tracks. |
| POST | `/api/v1/me/tracks` | bearer | 9 | Add a language track (plan-capped). |
| DELETE | `/api/v1/me/tracks/{id}` | bearer | 9 | Remove a language track. |
| POST | `/api/v1/me/tracks/{id}/placement` | bearer | 10 | Generate the placement test (idempotent). |
| GET | `/api/v1/me/tracks/{id}/placement` | bearer | 10 | Read the placement (no answer keys). |
| POST | `/api/v1/me/tracks/{id}/placement/submit` | bearer | 10 | Grade → level. |
| POST | `/api/v1/me/tracks/{id}/generate` | bearer | 11 | Start AI course generation (background job). |
| GET | `/api/v1/me/tracks/{id}/generation` | bearer | 11 | Poll the generation job. |
| GET | `/api/v1/me/courses` | bearer | 11 | The learner's own (generated) courses. |
| GET | `/api/v1/courses/{id}/extension` | bearer | 12 | Completion % + `can_extend` hint. |
| POST | `/api/v1/courses/{id}/extend` | bearer | 12 | Append lessons (optional `topic`, `count`). |
| GET | `/api/v1/courses/{id}/chat` | bearer | 12 | The in-course chat history. |
| POST | `/api/v1/courses/{id}/chat` | bearer | 12 | Ask for a topic (+ optional `count`) → AI appends content. |

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

### AI (Sprint 6)

All model access is behind the `AIProvider` port (Gemini), so swapping the model
or provider is a config change. Requests are built server-side; learner text is
fenced against prompt injection. Per-user rate limiting guards the Gemini free
tier; when AI is unconfigured or out of quota the endpoints return `503`, and
exceeding the per-user budget returns `429`.

`POST /ai/teacher` explains a lesson/topic/question for the learner's level.
`POST /ai/tutor` reviews the submitted code and returns a hint, not the full
solution. `POST /admin/ai/generate` (admin) generates a lesson or exercise and
writes it through `ContentService`/`ExerciseService` into the normal tables,
marked `source="ai"`; a generated exercise is self-verified (its reference
solution must pass its own `test_spec` via Judge0) before it is persisted.

```jsonc
// POST /api/v1/ai/tutor   { "exercise_id": "…", "code": "...", "question": "why is it wrong?" }
{ "answer": "Check your loop bound — …", "model": "gemini-2.5-flash", "total_tokens": 312 }

// POST /api/v1/admin/ai/generate   { "kind": "exercise", "lesson_id": "…", "topic": "loops" }
{ "kind": "exercise", "id": "…", "lesson_id": "…", "title": "…", "slug": "…",
  "language": "python", "source": "ai" }
```

### Today & Progress (Sprint 7)

Completion is tracked as `ProgressEvent`s, emitted automatically when an exercise
is graded `passed`/`failed` and when a quiz is submitted, plus an explicit
`POST /lessons/{id}/complete` for lessons. `GET /today` returns the next
incomplete items in course order (capped by skill level); `GET /progress`
returns per-course completion, overall totals, and a day streak.

```jsonc
// GET /api/v1/today
{ "items": [ { "type": "lesson", "id": "…", "title": "Loops", "course_slug": "basics" },
             { "type": "exercise", "id": "…", "title": "Sum", "course_slug": "basics" } ] }

// GET /api/v1/progress
{ "courses": [ { "course_id": "…", "title": "Basics", "slug": "basics",
                 "total": 3, "completed": 2, "percent": 67 } ],
  "total": 3, "completed": 2, "percent": 67, "streak": 4 }
```

### Subscriptions & billing (Sprint 8)

`GET /subscription` reports the caller's plan/status. `POST /subscription/checkout`
returns a hosted Stripe Checkout URL (the app never trusts the client to confirm
payment). `POST /webhooks/stripe` is **signature-verified** and drives all state
transitions (active on `checkout.session.completed` / `customer.subscription.updated`,
canceled on `customer.subscription.deleted`). Premium endpoints (e.g. the AI
Tutor) are gated by `require_active_subscription`: when `BILLING_ENABLED` is on,
non-subscribers get `402 Payment Required`; when off (dev default) the gate is a
no-op.

```jsonc
// POST /api/v1/subscription/checkout
{ "checkout_url": "https://checkout.stripe.com/c/pay/cs_test_…" }

// GET /api/v1/subscription
{ "plan": "pro", "status": "active", "active": true,
  "current_period_end": "2026-08-01T00:00:00Z" }
```

### Language tracks & onboarding (Sprint 9)

A **track** is a language the learner has chosen to study. `GET /me` gains an
`onboarded` flag (true once ≥1 track exists) so the frontend routes first-login
users to onboarding instead of the dashboard. The number of tracks is
plan-capped: free users get `FREE_MAX_LANGUAGES` (2); an active subscriber gets
`PAID_MAX_LANGUAGES`. Adding beyond the cap returns `402`; a duplicate returns
`409`.

```jsonc
// POST /api/v1/me/tracks   { "language_id": "…" }
{ "id": "…", "language_id": "…", "language_name": "Python",
  "language_slug": "python", "level": null, "status": "active" }
```

### Placement test (Sprint 10)

For a track, `POST …/placement` generates (idempotently) a set of multiple-choice
questions plus two short coding tasks via the AI provider; the coding tasks are
**self-verified** (reference solution must pass its own tests via Judge0) before
being stored. `GET …/placement` returns the test **without** answer keys or
reference solutions. `POST …/placement/submit` grades it (coding weighted higher),
maps the weighted percent to a level (`<40` beginner, `40–75` intermediate, `>75`
advanced), and stores the level on the track and profile.

```jsonc
// POST /api/v1/me/tracks/{id}/placement/submit
//   { "mcq_answers": { "<mcq_id>": "<choice_id>" }, "code": { "<task_id>": "..." } }
{ "level": "intermediate", "percent": 60,
  "breakdown": { "correct_mcqs": 3, "total_mcqs": 5, "passed_coding": 1, "total_coding": 2 } }
```

### AI curriculum generation (Sprint 11)

After placement, `POST …/generate` starts a **background job** that builds a full
course for the track — a syllabus of lessons, each with exercises and a quiz,
generated by the AI and written into the existing content tables
(`source="ai"`, `courses.track_id` set). The client polls `GET …/generation`
for progress (`completed`/`total`); `GET /me/courses` then lists the learner's
generated courses (served by the same `GET /courses/{slug}` machinery). Manual
content CRUD is retired from the primary flow (admin endpoints remain until
Sprint 13 repurposes admin for review).

```jsonc
// POST /api/v1/me/tracks/{id}/generate  -> 202
{ "id": "…", "track_id": "…", "status": "pending", "total": 8, "completed": 0,
  "course_id": null, "error": null }

// GET /api/v1/me/tracks/{id}/generation  (while building)
{ "id": "…", "status": "running", "total": 8, "completed": 3, "course_id": "…" }
```

## Versioning

The API is namespaced under `/api/v1`. Breaking changes introduce `/api/v2`
rather than mutating v1.
