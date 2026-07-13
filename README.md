# CodePath AI

> AI-powered, personalized programming learning platform.

CodePath AI guides each learner through a tailored path of lessons, coding
exercises, and quizzes — taught and tutored by AI, with code executed in a
sandbox.

**Status — Sprints 0–13 and 15 complete** (14 — GCP deployment — designed, deferred to avoid hosting costs; see [docs/Sprint_14.md](docs/Sprint_14.md)).
The platform also includes **spaced review** (Sprint 15 — every wrong quiz/placement
answer and failed exercise lands in a mistakes notebook and comes back on a
1→2→4-day schedule until mastered, surfaced first in "Today").
The product is pivoting to AI-generated, personalized curricula (Sprints 9–13,
see [docs/00_PROJECT.md](docs/00_PROJECT.md)): learners now pick a language on
first login and hold plan-capped language "tracks". Foundation:
production-quality scaffold (Sprint 0),
authentication & user profiles (Sprint 1), a content domain (Sprint 2 —
languages, courses, lessons + admin CRUD), coding exercises (Sprint 3 — model +
Monaco editor + submissions), **code execution & grading via Judge0** (Sprint 4 —
Run for live output, Submit graded against hidden tests in the background),
**quizzes with auto-grading** (Sprint 5 — multiple-choice quizzes attached to
lessons, taken without the answer key leaking, scored instantly, with admin
authoring), **AI Teacher / AI Tutor + content generation** (Sprint 6 — Gemini
behind an `AIProvider` port; explain lessons, hint on code, and generate
self-verified lessons/exercises into the existing tables), and a **personalized
"Today" plan + progress analytics** (Sprint 7 — completion tracking across
lessons/exercises/quizzes, an ordered daily plan, and per-course completion +
streak), **subscriptions + hardening** (Sprint 8 — Stripe checkout & signature-verified
webhooks, premium gating of the AI Tutor, an in-process rate limiter, and a
production `docker-compose.prod.yml`), and **onboarding & language tracks**
(Sprint 9 — first-login language picker, per-user tracks, free-tier cap of 2
languages), and a **placement test** (Sprint 10 — AI-generated MCQs + coding
tasks, self-verified, graded into an assessed level on the track/profile), and
**AI curriculum generation** (Sprint 11 — a background job builds a full
personalized course of lessons/exercises/quizzes for the track+level; manual
course authoring is retired), **continuous learning** (Sprint 12 — a
near-completion "Learn more" action and an in-course chat where the learner asks
for a topic and the AI appends a matching lesson + exercises + quiz, reusing the
generation pipeline), and **entitlements & admin review** (Sprint 13 — plan-aware
limits on languages, AI Tutor hints, and generation quota, exposed via
`/me/entitlements` with a `402`/upgrade prompt over-limit; the admin surface is
now an AI-content review console, where hidden lessons are withheld from learners).

See [`docs/`](docs/) for full design documentation — start with
[00_PROJECT.md](docs/00_PROJECT.md) and the per-sprint plans
[Sprint_01.md](docs/Sprint_01.md) … [Sprint_08.md](docs/Sprint_08.md).

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | React, TypeScript, Vite, TailwindCSS, shadcn/ui, TanStack Query, Zustand, Monaco Editor |
| Backend | FastAPI, SQLAlchemy 2.0, Alembic (Clean Architecture) |
| Database | PostgreSQL 16 |
| Auth | Firebase Authentication (token verification; stubbed in Sprint 0) |
| Infra | Docker Compose |

## Repository Structure

```text
.
├── docs/                 # Design documentation (00–09)
├── frontend/             # React + Vite app
│   └── src/
│       ├── pages/        # Route pages (Landing, Dashboard, ...)
│       ├── components/   # ui/ (shadcn) + layout
│       ├── lib/          # api, query-client, firebase, utils
│       └── store/        # Zustand stores
├── backend/              # FastAPI app (Clean Architecture)
│   ├── app/
│   │   ├── api/          # routers + DI (presentation)
│   │   ├── application/  # use cases / services
│   │   ├── domain/       # entities + repository interfaces (pure)
│   │   ├── infrastructure/  # db, models, repositories
│   │   ├── core/         # config, logging, security
│   │   └── schemas/      # Pydantic DTOs
│   └── alembic/          # migrations
├── docker/               # shared docker assets/notes
├── scripts/              # dev helper scripts
├── .github/workflows/    # CI
├── docker-compose.yml
└── .env.example
```

## Quick Start (Docker — recommended)

Prerequisites: Docker + Docker Compose.

```bash
cp .env.example .env
docker compose up --build
```

Then open:

- Frontend: <http://localhost:5173>
- API: <http://localhost:8000/api/v1/health>
- API docs: <http://localhost:8000/docs>

The backend applies database migrations automatically on startup, so the stack
is ready with no manual steps.

**Code execution (Judge0)** is opt-in — it's a heavy, privileged service kept
behind a compose profile so the default stack stays lean:

```bash
docker compose --profile judge0 up --build
```

Without it, the app still runs; exercise submissions resolve to an `error`
verdict (graceful degradation). See [docs/08_DEPLOYMENT.md](docs/08_DEPLOYMENT.md).

## Local Development (without Docker)

### Backend

```bash
cd backend
python -m venv .venv
source .venv/Scripts/activate     # Windows; use .venv/bin/activate on macOS/Linux
pip install -r requirements.txt
cp .env.example .env              # point DATABASE_URL at a running Postgres
alembic upgrade head
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```

## Development Commands

| Command | Where | Purpose |
|---------|-------|---------|
| `docker compose up --build` | root | Run the whole stack |
| `npm run dev` | frontend | Vite dev server |
| `npm run build` | frontend | Type-check + production build |
| `npm run lint` | frontend | ESLint |
| `uvicorn app.main:app --reload` | backend | Run API |
| `alembic upgrade head` | backend | Apply migrations |
| `alembic revision --autogenerate -m "..."` | backend | New migration |
| `python -m scripts.seed` | backend | Seed sample content |
| `python -m scripts.set_admin <email>` | backend | Promote a user to admin |
| `ruff check .` | backend | Lint |
| `pytest -q` | backend | Tests |

## Configuration

All configuration is environment-driven. Copy [.env.example](.env.example) to
`.env` and adjust. Never commit a real `.env`. Variable reference lives in the
example file and [docs/08_DEPLOYMENT.md](docs/08_DEPLOYMENT.md).

**Authentication:** with `AUTH_STUB_ENABLED=true` (default) the backend accepts a
fixed dev identity and the frontend offers a "Continue (development mode)"
sign-in — no Firebase needed for local work. To use real auth, set the
`FIREBASE_*` (backend) and `VITE_FIREBASE_*` (frontend) variables and set
`AUTH_STUB_ENABLED=false`.

**AI (Sprint 6):** set `GEMINI_API_KEY` (from [Google AI Studio](https://aistudio.google.com))
to enable the AI Teacher/Tutor and content generation. Left empty, those
endpoints return a friendly `503` and the rest of the app works unchanged.

**Billing (Sprint 8):** billing is off by default (`BILLING_ENABLED=false`), so
premium gating is a no-op in dev. To enable it, set `BILLING_ENABLED=true` and
the `STRIPE_*` variables, and point a Stripe webhook at `/api/v1/webhooks/stripe`.
For production use [docker-compose.prod.yml](docker-compose.prod.yml) (Nginx-served
frontend, gunicorn workers, rate limiting on). See [docs/08_DEPLOYMENT.md](docs/08_DEPLOYMENT.md).

## Documentation

| Doc | Topic |
|-----|-------|
| [00_PROJECT.md](docs/00_PROJECT.md) | Overview & roadmap |
| [01_PRD.md](docs/01_PRD.md) | Product requirements |
| [02_ARCHITECTURE.md](docs/02_ARCHITECTURE.md) | System & clean architecture |
| [03_DATABASE.md](docs/03_DATABASE.md) | Schema & migrations |
| [04_API.md](docs/04_API.md) | Endpoints |
| [05_AI.md](docs/05_AI.md) | AI design (deferred) |
| [06_FRONTEND.md](docs/06_FRONTEND.md) | Frontend structure |
| [07_BACKEND.md](docs/07_BACKEND.md) | Backend structure |
| [08_DEPLOYMENT.md](docs/08_DEPLOYMENT.md) | Running & deployment |
| [09_TESTING.md](docs/09_TESTING.md) | Testing & quality |
| [Sprint_01.md](docs/Sprint_01.md) … [Sprint_08.md](docs/Sprint_08.md) | Per-sprint implementation plans |

## License

Proprietary — internal hackathon project (placeholder).
