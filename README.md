# CodePath AI

> AI-powered, personalized programming learning platform.

CodePath AI guides each learner through a tailored path of lessons, coding
exercises, and quizzes — taught and tutored by AI, with code executed in a
sandbox.

**Status — through Sprint 4:** production-quality scaffold (Sprint 0),
authentication & user profiles (Sprint 1), a content domain (Sprint 2 —
languages, courses, lessons + admin CRUD), coding exercises (Sprint 3 — model +
Monaco editor + submissions), and **code execution & grading via Judge0**
(Sprint 4 — Run for live output, Submit graded against hidden tests in the
background). Quizzes, AI Teacher/Tutor, recommendations, and billing follow in
Sprints 5–8.

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
