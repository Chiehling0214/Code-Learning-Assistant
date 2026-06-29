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
│   │           └── profile.py
│   ├── core/
│   │   ├── config.py           # Settings (pydantic-settings)
│   │   ├── logging.py          # JSON logging setup
│   │   └── security.py         # Firebase verification (stub-aware)
│   ├── domain/                  # pure: entities + repository interfaces
│   │   ├── entities.py
│   │   └── repositories.py
│   ├── application/             # use cases / services
│   │   └── services/
│   │       ├── health_service.py
│   │       └── user_service.py  # provisioning + profile (Sprint 1)
│   ├── infrastructure/
│   │   ├── db/
│   │   │   ├── base.py         # Declarative Base
│   │   │   └── session.py      # engine + per-request unit of work
│   │   ├── models/             # SQLAlchemy ORM models
│   │   │   └── models.py
│   │   └── repositories/        # concrete repo implementations
│   │       └── sqlalchemy_repositories.py  # User + StudentProfile repos
│   └── schemas/                 # Pydantic DTOs
│       ├── health.py
│       └── user.py             # current user + profile schemas
├── alembic/
│   ├── env.py
│   ├── script.py.mako
│   └── versions/0001_initial.py
├── alembic.ini
├── pyproject.toml
├── requirements.txt
└── Dockerfile
```

## Configuration

`app/core/config.py` defines a `Settings` model read from environment variables
(and `.env`). Access via the cached `get_settings()` accessor. Key vars:
`DATABASE_URL`, `ENVIRONMENT`, `LOG_LEVEL`, `CORS_ORIGINS`,
`FIREBASE_PROJECT_ID`, `FIREBASE_CREDENTIALS_FILE`, `AUTH_STUB_ENABLED`.

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

## Testing

See [09_TESTING.md](09_TESTING.md). `pytest` with FastAPI `TestClient`. Tests use
in-memory fake repositories (`tests/fakes.py`) so the suite needs no database:
`/health` smoke test, `UserService` unit tests, and `/me` + `/me/profile` API
tests (including the `401` path when stub auth is disabled).
