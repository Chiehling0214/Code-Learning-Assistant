# Sprint 14 — Production Launch: GCP Deployment & CI/CD

**Duration:** ~4 days
**Theme:** Ship it. Put the app on the public internet (the docs/08 architecture),
gate every change with CI, and make the deployment safe to leave running
(backups, budget alert, health monitoring).

## Goal

Deploy the full stack to GCP following the target architecture in
[08_DEPLOYMENT.md](08_DEPLOYMENT.md): frontend on **Firebase Hosting**, backend +
Postgres + Judge0 on **one GCE VM** via `docker-compose.prod.yml`, TLS via Caddy.
Add **GitHub Actions CI** (lint + tests + build on every push/PR) and a
repeatable deploy path. Costs stay in the "demo budget" (< ~US$15/mo, VM
stoppable when idle).

## User Story

- As a visitor, I can open a public HTTPS URL, sign up, and use the whole product.
- As the developer, every push runs lint + tests automatically; a broken build
  never reaches the VM.
- As the owner, I get a budget alert before costs surprise me, and a nightly DB
  backup I can actually restore.

## Tasks

### Infrastructure
1. GCE VM (e2-small/medium, Ubuntu LTS): Docker + compose, clone repo, prod
   `.env` (real Firebase/Gemini/Stripe test keys; `AUTH_STUB_ENABLED=false`,
   `RATE_LIMIT_ENABLED=true`, prod `CORS_ORIGINS`). Judge0 needs cgroup v1
   (GRUB flag per docs/08).
2. **Caddy** (or nginx) container in `docker-compose.prod.yml`: TLS for
   `api.<domain>` → backend:8000. Postgres/Judge0 stay internal-only.
3. **Firebase Hosting**: deploy `frontend/dist` (`VITE_API_BASE_URL` → the API
   URL); add the domain to Firebase Auth authorized domains.
4. Nightly `pg_dump` cron → GCS bucket (or local + `gsutil cp`); document and
   test a restore once.
5. GCP **budget alert** (e.g. US$10/mo) + uptime check on `/health`.

### CI/CD (GitHub Actions)
6. `ci.yml`: backend job (ruff + pytest) and frontend job (eslint + tsc/build)
   on push/PR to `main`; branch protection can require them.
7. `deploy.yml` (manual `workflow_dispatch`): SSH to the VM → `git pull` →
   `docker compose -f docker-compose.prod.yml up -d --build`, then
   `firebase deploy --only hosting`. Secrets via GitHub Actions secrets.
8. README/docs: production runbook — start/stop the VM (cost control), rotate a
   key, view logs, restore a backup.

## Expected Files

```text
.github/workflows/ci.yml                  (new)
.github/workflows/deploy.yml              (new)
docker-compose.prod.yml                   # + caddy service, judge0 profile
deploy/Caddyfile                          (new)
deploy/backup.sh                          (new; pg_dump → GCS)
docs/08_DEPLOYMENT.md                     # runbook: setup, deploy, restore, costs
frontend/.firebaserc / firebase.json      (new; hosting config)
```

## Acceptance Criteria

- [ ] The app is usable end-to-end (signup → placement → generated course →
      exercise run/submit → subscription page) at a public HTTPS URL.
- [ ] CI runs ruff/pytest/eslint/build on every push; a red build blocks deploy.
- [ ] One-command (or one-click) deploy updates the VM + hosting.
- [ ] A backup exists in GCS and a restore was performed once, successfully.
- [ ] Budget alert + `/health` uptime check are active; idle cost documented.

## Dependency

- **Sprint 8** (prod compose, rate limiting), **docs/08** target architecture.
- Stripe stays in test mode; Gemini free tier (documented limits).
