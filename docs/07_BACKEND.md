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
│   │           └── me.py
│   ├── core/
│   │   ├── config.py           # Settings (pydantic-settings)
│   │   ├── logging.py          # JSON logging setup
│   │   └── security.py         # Firebase verification (stub-aware)
│   ├── domain/                  # pure: entities + repository interfaces
│   │   ├── entities.py
│   │   └── repositories.py
│   ├── application/             # use cases / services
│   │   └── services/
│   │       └── health_service.py
│   ├── infrastructure/
│   │   ├── db/
│   │   │   ├── base.py         # Declarative Base
│   │   │   └── session.py      # engine + SessionLocal
│   │   ├── models/             # SQLAlchemy ORM models
│   │   │   └── models.py
│   │   └── repositories/        # concrete repo implementations
│   │       └── sqlalchemy_repositories.py
│   └── schemas/                 # Pydantic DTOs
│       └── health.py
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

FastAPI `Depends` wires concrete infrastructure into the API edge:

- `get_db()` yields a SQLAlchemy `Session`.
- `get_current_user()` verifies the bearer token (or returns the stub identity
  when `AUTH_STUB_ENABLED=true`).
- Repository implementations are constructed from the session and passed to
  application services.

## Authentication (Sprint 0)

`core/security.py` exposes `verify_token`. When `AUTH_STUB_ENABLED=true` it
returns a fixed development identity without contacting Firebase. When disabled,
it verifies the ID token via `firebase-admin` (wired but unused until Sprint 1).

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

See [09_TESTING.md](09_TESTING.md). `pytest` with FastAPI `TestClient`; a smoke
test covers `/health`.
