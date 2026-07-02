# 07 — Backend

## Stack

| Concern | Choice |
|---------|--------|
| Framework | FastAPI |
| ORM | SQLAlchemy 2.0 |
| Migrations | Alembic |
| Validation | Pydantic v2 / pydantic-settings |
| Server | Uvicorn |
| Auth | Firebase Admin (token verification) — stubbed in Sprint 0 |

## Structure (Clean Architecture)

```text
backend/
├── app/
│   ├── main.py                  # FastAPI app factory, middleware, routers
│   ├── api/
│   │   ├── deps.py             # DI: db session, current user
│   │   └── v1/
│   │       ├── router.py       # aggregates v1 routes
│   │       └── routes/
│   │           ├── health.py
│   │           ├── me.py
│   │           ├── profile.py
│   │           ├── languages.py     # content reads (Sprint 2)
│   │           ├── courses.py
│   │           ├── lessons.py
│   │           ├── admin_content.py # admin CRUD (Sprint 2)
│   │           ├── exercises.py     # exercises + submissions (Sprint 3)
│   │           ├── quizzes.py       # quizzes + grading + authoring (Sprint 5)
│   │           ├── ai.py            # AI teacher/tutor + generation (Sprint 6)
│   │           ├── today.py         # personalized daily plan (Sprint 7)
│   │           ├── progress.py      # progress analytics + mark-complete (Sprint 7)
│   │           ├── subscription.py  # subscription status + checkout (Sprint 8)
│   │           ├── webhooks.py      # Stripe webhook receiver (Sprint 8)
│   │           ├── tracks.py        # language tracks + onboarding (Sprint 9)
│   │           ├── placement.py     # placement test (Sprint 10)
│   │           └── curriculum.py    # AI course generation + /me/courses (Sprint 11)
│   ├── core/
│   │   ├── config.py           # Settings (pydantic-settings)
│   │   ├── logging.py          # JSON logging setup
│   │   └── security.py         # Firebase verification (stub-aware)
│   ├── domain/                  # pure: entities + repository interfaces
│   │   ├── entities.py
│   │   └── repositories.py
│   ├── application/             # use cases / services
│   │   ├── ports/              # provider-agnostic ports
│   │   │   └── ai_provider.py  # AIProvider protocol + DTOs (Sprint 6)
│   │   └── services/
│   │       ├── health_service.py
│   │       ├── user_service.py        # provisioning + profile (Sprint 1)
│   │       ├── content_service.py     # languages/courses/lessons (Sprint 2)
│   │       ├── exercise_service.py    # exercises (Sprint 3)
│   │       ├── submission_service.py  # submissions (Sprint 3)
│   │       ├── execution_service.py   # run + grade against tests (Sprint 4)
│   │       ├── quiz_service.py        # quizzes + auto-grading (Sprint 5)
│   │       ├── ai_teacher_service.py  # AI teacher (Sprint 6)
│   │       ├── ai_tutor_service.py    # AI tutor (Sprint 6)
│   │       ├── ai_usage.py            # per-user rate limit + usage log (Sprint 6)
│   │       ├── generate_content_service.py  # AI -> lessons/exercises (Sprint 6)
│   │       ├── progress_service.py    # completion aggregates + streak (Sprint 7)
│   │       ├── recommendation_service.py    # "Today" plan (Sprint 7)
│   │       ├── subscription_service.py      # billing + entitlement (Sprint 8)
│   │       ├── track_service.py             # language tracks + caps (Sprint 9)
│   │       ├── placement_service.py         # placement generate/grade (Sprint 10)
│   │       └── curriculum_service.py        # AI course generation (Sprint 11)
│   ├── infrastructure/
│   │   ├── db/
│   │   │   ├── base.py         # Declarative Base
│   │   │   └── session.py      # engine + per-request unit of work
│   │   ├── models/             # SQLAlchemy ORM models
│   │   │   └── models.py
│   │   ├── judge0/             # Judge0 HTTP client (Sprint 4)
│   │   │   └── client.py
│   │   ├── ai/                 # AIProvider implementation (Sprint 6)
│   │   │   └── gemini_provider.py
│   │   ├── billing/            # Stripe client (Sprint 8)
│   │   │   └── stripe_client.py
│   │   ├── grading.py         # background grading orchestrator (Sprint 4)
│   │   ├── generation_worker.py  # background curriculum generation (Sprint 11)
│   │   └── repositories/        # concrete repo implementations
│   │       └── sqlalchemy_repositories.py  # User, Profile, Language, Course, Lesson, ...
│   └── schemas/                 # Pydantic DTOs
│       ├── health.py
│       ├── user.py             # current user + profile schemas
│       ├── content.py          # language/course/lesson schemas
│       └── exercise.py         # exercise + submission schemas
├── alembic/
│   ├── env.py
│   ├── script.py.mako
│   └── versions/{0001_initial,0002_lessons,0003_exercises}.py
├── scripts/                     # seed.py, set_admin.py
├── alembic.ini
├── pyproject.toml
├── requirements.txt
└── Dockerfile
```

## Configuration

`app/core/config.py` defines a `Settings` model read from environment variables
(and `.env`). Access via the cached `get_settings()` accessor. Key vars:
`DATABASE_URL`, `ENVIRONMENT`, `LOG_LEVEL`, `CORS_ORIGINS`,
`FIREBASE_PROJECT_ID`, `FIREBASE_CREDENTIALS_FILE`, `AUTH_STUB_ENABLED`,
`JUDGE0_URL`, `JUDGE0_AUTH_TOKEN`, `JUDGE0_TIMEOUT`.

## Code Execution (Sprint 4)

Submitting an exercise stores the submission `pending` and schedules background
grading (`infrastructure/grading.py`) which runs the code against the exercise's
`test_spec` via the Judge0 client and persists a `passed` / `failed` / `error`
verdict. The Run button uses `POST /exercises/{id}/run` (no grading). Judge0 is
**opt-in** (`docker compose --profile judge0 up`); when it is unreachable,
run/submit degrade gracefully to an `error` result instead of failing.

## Dependency Injection

FastAPI `Depends` wires concrete infrastructure into the API edge (see
`app/api/deps.py`):

- `get_db()` yields a request-scoped `Session` (unit of work: commits on
  success, rolls back on error).
- `get_current_user()` verifies the bearer token (or returns the stub identity
  when `AUTH_STUB_ENABLED=true`).
- `get_user_service()` builds `UserService` from the user + profile
  repositories.
- `get_current_db_user()` resolves the token identity to a persisted `User`,
  provisioning it on first sign-in.

## Authentication & User Provisioning (Sprint 1)

`core/security.py` exposes `verify_token`. When `AUTH_STUB_ENABLED=true` it
returns a fixed development identity without contacting Firebase. When disabled,
it verifies the Firebase ID token via `firebase-admin` and returns `401` on a
missing/invalid token.

On the first authenticated request, `UserService.get_or_create_from_identity`
creates the `User` row and an empty `StudentProfile`. Subsequent requests reuse
the existing user (idempotent). Profile reads/updates go through
`/api/v1/me/profile`.

## Logging

`core/logging.py` configures structured JSON logging at `LOG_LEVEL`. A request
ID is attached per request via middleware for traceability.

## Database

- Engine/session in `infrastructure/db/session.py`.
- ORM models in `infrastructure/models/`.
- Alembic `env.py` imports the models' metadata for autogeneration.

## Running

```bash
# local (with a running postgres)
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8000

# via docker compose (recommended)
docker compose up backend
```

## Seeding & admin

- `python -m scripts.seed` inserts a sample language, course, and lessons
  (idempotent).
- `python -m scripts.set_admin <email>` promotes a user to admin (users are
  provisioned non-admin on first sign-in).

## Testing

See [09_TESTING.md](09_TESTING.md). `pytest` with FastAPI `TestClient`. Tests use
in-memory fake repositories (`tests/fakes.py`, shared via a `fakes` fixture) so
the suite needs no database: `/health` smoke test, `UserService` unit tests,
`/me` + `/me/profile` API tests (including the `401` path when stub auth is
disabled), content read/admin-guard tests, exercise/submission tests, and
execution/grading tests (mocked Judge0 runner — pass/fail/error paths and the
graceful-degradation path).
