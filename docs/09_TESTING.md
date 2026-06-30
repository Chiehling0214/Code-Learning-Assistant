# 09 — Testing & Quality

## Philosophy

Sprint 0 establishes the testing *harness* and quality gates. Coverage is
intentionally minimal (smoke tests) since business logic arrives in later
sprints. The goal: the project compiles, builds, lints, and a basic test passes.

## Backend

| Tool | Purpose |
|------|---------|
| `pytest` | test runner |
| `ruff` | lint + format check |
| FastAPI `TestClient` | HTTP-level tests |

Run:

```bash
cd backend
pip install -r requirements.txt
ruff check .
pytest -q
```

Tests use in-memory fake repositories (`tests/fakes.py`) and dependency
overrides (`tests/conftest.py`), so the suite runs without a database.

Included tests:

- `tests/test_health.py` — `GET /health` returns `200` and `status: ok`.
- `tests/test_user_service.py` — user/profile provisioning + profile updates.
- `tests/test_me_api.py` — `/me` and `/me/profile` behaviour, plus the `401`
  path when stub auth is disabled.
- `tests/test_content.py` — content reads (ordered lessons, `404`s) and the
  admin guard (`403` for non-admins, create/delete for admins).
- `tests/test_submissions.py` — exercise reads (no `test_spec` leak), submitting
  (`pending`), submission history, and the admin create guard.
- `tests/test_execution.py` — grading (`passed`/`failed`/`error`, runtime/compile
  errors, hidden-case I/O), the `/run` endpoint, graceful degradation when Judge0
  is unavailable, and `GET /submissions/{id}` ownership.

## Frontend

| Tool | Purpose |
|------|---------|
| `tsc` (via `vite build`) | type checking |
| `eslint` | linting |

Run:

```bash
cd frontend
npm install
npm run lint
npm run build      # type-check + bundle; fails on type errors
```

A unit-test runner (Vitest) can be added in Sprint 1 when components gain logic.

## CI

`.github/workflows/ci.yml` runs two jobs on push/PR:

1. **backend** — install deps, `ruff check`, `pytest`.
2. **frontend** — `npm ci`, `npm run lint`, `npm run build`.

## Quality Gates (Sprint 0 definition of done)

- [ ] `docker compose up` starts postgres + backend + frontend.
- [ ] `GET /health` returns `200`.
- [ ] Frontend builds and every route renders.
- [ ] No TODO/placeholder-comment stubs pretending to be features.
- [ ] Lint passes for both apps.

## Future testing strategy

| Layer | Approach (later) |
|-------|------------------|
| domain | pure unit tests, no I/O |
| application | use-case tests with fake repositories |
| infrastructure | integration tests against a test Postgres |
| api | TestClient contract tests |
| frontend | Vitest + Testing Library, Playwright e2e |
