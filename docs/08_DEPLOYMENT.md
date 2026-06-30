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
| `judge0`* | judge0/judge0:1.13.1 | 2358 | code execution — **opt-in profile** |

\* Judge0 (plus `judge0-workers`, `judge0-db`, `judge0-redis`) is behind the
`judge0` compose profile, so the default `docker compose up` stays lean and
reliable. Start it with `docker compose --profile judge0 up`. It is a privileged,
heavy service and may need extra host configuration on Docker Desktop / cgroup
v2; the app degrades gracefully (submissions resolve to `error`) when it is not
running.

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

## Target production architecture (Sprint 8)

Free-tier-friendly deployment for the hackathon:

```text
                         User's browser
                              │
          ┌───────────────────┴───────────────────┐
          │ HTTPS (static)                         │ HTTPS (REST /api)
          ▼                                        ▼
 ┌──────────────────┐                  ┌────────────────────────────────┐
 │ Firebase Hosting │                  │            GCE VM              │
 │ (frontend build) │                  │  backend (FastAPI, Docker)     │
 └──────────────────┘                  │     │ internal      │ internal │
          │ Firebase Auth              │     ▼               ▼          │
          ▼ (ID token)                 │  postgres        judge0 stack  │
 ┌──────────────────┐                  │  (Docker)        (Docker)      │
 │ Firebase (Auth)  │◀── verify ───────┼─────┘                          │
 └──────────────────┘                  └──────────────┬─────────────────┘
                                                       │ HTTPS (external)
                                                       ▼
                                                 ┌───────────┐
                                                 │ Gemini API│ (free tier)
                                                 └───────────┘
```

- **Frontend → Firebase Hosting.** Deploy the `npm run build` output (`dist/`)
  with `firebase deploy`. CDN-served, free tier, same Firebase project as Auth.
- **Backend + PostgreSQL → one GCE VM (Compute Engine), via Docker Compose.** The
  backend reaches Postgres over the internal compose network.
- **Judge0 → same VM (Docker), internal only.** Backend calls `http://judge0:2358`;
  the `2358` port is **not** exposed publicly. Requires a privileged container and
  cgroup v1 — on Ubuntu 22.04+ force it with `systemd.unified_cgroup_hierarchy=0`
  (GRUB) and reboot, or use Ubuntu 20.04.
- **Gemini → external API** called by the backend (`GEMINI_API_KEY`, free tier).
- **Firebase Auth → external**, verified server-side (`AUTH_STUB_ENABLED=false`).

Hardening checklist (Sprint 8):

- Set `CORS_ORIGINS` to the Firebase Hosting domain(s).
- VM firewall: open only `443` (backend); keep `5432`/`2358` internal.
- Put the backend behind Caddy/Nginx (or a GCP load balancer) for TLS; run
  uvicorn with gunicorn workers.
- Secrets via the VM's `.env` / a secret manager — never commit them.
- A `docker-compose.prod.yml` overlay pins the frontend `prod` target only if you
  ever serve it from the VM instead of Firebase Hosting.

## Health & readiness

- Liveness: `GET /health`.
- Readiness (includes DB check): `GET /api/v1/health`.
- Postgres: compose `pg_isready` healthcheck.

## CI

`.github/workflows/ci.yml` lints and builds the frontend and runs backend
checks/tests on every push and PR. See [09_TESTING.md](09_TESTING.md).
