# 08 — Deployment

## Local (Docker Compose)

The whole stack runs with one command:

```bash
cp .env.example .env
docker compose up --build
```

Services:

| Service | Image / Build | Port | Notes |
|---------|---------------|------|-------|
| `postgres` | postgres:16-alpine | 5432 | data persisted in named volume |
| `backend` | `./backend` | 8000 | runs `alembic upgrade head` then uvicorn |
| `frontend` | `./frontend` | 5173 | Vite dev server (compose dev mode) |

URLs:

- Frontend: <http://localhost:5173>
- Backend API: <http://localhost:8000/api/v1>
- API docs: <http://localhost:8000/docs>

### Startup order

`backend` waits for `postgres` to be healthy (compose healthcheck). On start the
backend applies migrations automatically, so a fresh database is ready without
manual steps.

## Environment

All configuration is environment-driven. See the root [.env.example](../.env.example)
for the complete variable list. Never commit a real `.env`.

## Build images

```bash
docker compose build              # all
docker compose build backend       # one service
```

## Production notes (future)

Sprint 0 ships a development-oriented compose file. For production later:

- Serve the frontend as static assets (the `frontend/Dockerfile` includes a
  multi-stage build that produces an Nginx image; the compose file uses the dev
  target for hot reload).
- Run uvicorn behind a process manager / gunicorn workers.
- Use managed PostgreSQL and a secrets manager.
- Terminate TLS at a reverse proxy / load balancer.

## Health & readiness

- Liveness: `GET /health`.
- Readiness (includes DB check): `GET /api/v1/health`.
- Postgres: compose `pg_isready` healthcheck.

## CI

`.github/workflows/ci.yml` lints and builds the frontend and runs backend
checks/tests on every push and PR. See [09_TESTING.md](09_TESTING.md).
