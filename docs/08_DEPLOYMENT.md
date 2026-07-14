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

### Production compose (`docker-compose.prod.yml`)

Sprint 8 ships a production stack:

```bash
cp .env.example .env   # fill POSTGRES_PASSWORD, CORS_ORIGINS, STRIPE_*, etc.
docker compose -f docker-compose.prod.yml up --build
```

Differences from the dev compose:

- **frontend** is built and served as static assets by Nginx (the `prod` Docker
  stage), not the Vite dev server (host `:8080`);
- **backend** runs under **gunicorn with uvicorn workers** (`-w 4`), applying
  migrations on start;
- **hardening on**: `RATE_LIMIT_ENABLED=true`, `AUTH_STUB_ENABLED=false`, CORS
  restricted to `CORS_ORIGINS`;
- **billing on**: `BILLING_ENABLED=true` with the `STRIPE_*` secrets;
- Postgres is **not** published to the host.

> The frontend build bakes `VITE_*` at build time. Pass them as build args (or
> build via Firebase Hosting) to point the static bundle at your real API/Firebase.

### Billing (Stripe)

- Set `STRIPE_API_KEY`, `STRIPE_PRICE_ID`, and `STRIPE_WEBHOOK_SECRET`.
- Point a Stripe webhook at `POST /api/v1/webhooks/stripe`; it is
  **signature-verified** and drives subscription state.
- Premium endpoints (e.g. AI Tutor) return `402` for non-subscribers when
  `BILLING_ENABLED=true`.

Hardening checklist (Sprint 8):

- Set `CORS_ORIGINS` to the Firebase Hosting domain(s).
- VM firewall: open only `443` (backend); keep `5432`/`2358` internal.
- Put the backend behind Caddy/Nginx (or a GCP load balancer) for TLS (the prod
  compose already runs gunicorn/uvicorn workers).
- Enable the in-process rate limiter (`RATE_LIMIT_ENABLED`), or front with a
  shared limiter (Redis) for multi-instance deployments.
- Secrets via the VM's `.env` / a secret manager — never commit them.

## Health & readiness

- Liveness: `GET /health`.
- Readiness (includes DB check): `GET /api/v1/health`.
- Postgres: compose `pg_isready` healthcheck.

## CI

`.github/workflows/ci.yml` lints and builds the frontend and runs backend
checks/tests on every push and PR. See [09_TESTING.md](09_TESTING.md).

---

## Production runbook — single GCE VM + Caddy (Sprint 14)

One VM runs everything behind Caddy with automatic HTTPS:

```text
https://$DOMAIN/        -> frontend (nginx static build)
https://$DOMAIN/api/*   -> backend (FastAPI + gunicorn)
postgres                -> internal only
Judge0                  -> RapidAPI (no local containers)
```

Repo artifacts: `docker-compose.prod.yml` (caddy + build args),
`deploy/Caddyfile`, `deploy/backup.sh`, `.env.prod.example`,
`.github/workflows/deploy.yml` (manual SSH deploy; needs `VM_HOST`/`VM_USER`/
`VM_SSH_KEY` secrets). CI (`ci.yml`) already gates every push.

### One-time setup

1. **gcloud CLI** (Windows): install from
   <https://cloud.google.com/sdk/docs/install>, then `gcloud init`.
2. **Project + budget**: create a project, link billing, and set a budget alert
   (Billing → Budgets & alerts, e.g. US$10/mo).
3. **VM** (≈US$15/mo, stop it when idle):
   ```bash
   gcloud compute instances create codepath --zone=asia-east1-b      --machine-type=e2-small --image-family=ubuntu-2404-lts-amd64      --image-project=ubuntu-os-cloud --boot-disk-size=30GB --tags=http-server,https-server
   gcloud compute firewall-rules create allow-http --allow tcp:80,tcp:443      --target-tags=http-server,https-server
   ```
4. **On the VM** (`gcloud compute ssh codepath --zone=asia-east1-b`): install
   Docker (`curl -fsSL https://get.docker.com | sudo sh`), add 2 GB swap (the
   frontend build needs it on 2 GB RAM), clone the repo to `/opt/codepath`.
5. **Domain**: point a (free) DuckDNS subdomain at the VM's external IP.
6. **Secrets**: copy `.env.prod.example` → `.env` on the VM and fill it in;
   `scp` the Firebase service-account key to `/opt/codepath/firebase-key.json`.
7. **Firebase Console**: add the domain to Auth → Authorized domains.
8. **Start**: `docker compose -f docker-compose.prod.yml up -d --build`.
9. **Backups**: `crontab -e` →
   `0 3 * * * cd /opt/codepath && ./deploy/backup.sh >> backups/backup.log 2>&1`.

### Day-2 operations

- **Update**: `git pull && docker compose -f docker-compose.prod.yml up -d --build`
  (or the manual **Deploy** GitHub Action once the SSH secrets are set).
- **Stop/start to save money**: `gcloud compute instances stop|start codepath
  --zone=asia-east1-b` (billed only while running; the IP changes unless you
  reserve a static one — update DuckDNS after each start, or reserve).
- **Logs**: `docker compose -f docker-compose.prod.yml logs -f backend`.
- **Restore**: see the comment at the bottom of `deploy/backup.sh`.
