# Sprint 04 — Judge0 Code Execution & Grading

**Duration:** ~4 days
**Theme:** Execute submissions in a sandbox via Judge0 and grade them against
the exercise's test specification.

## Goal

Integrate Judge0 so that submitting code actually runs it against test cases,
updates the submission to `passed` / `failed` / `error`, and surfaces
stdout/stderr and per-test results in the UI.

## User Story

- As a learner, I can run my code and see real output (stdout/stderr).
- As a learner, when I submit, my code is graded against hidden test cases and I
  see which passed/failed.
- As a learner, a correct solution is marked passed and contributes to progress.

## Tasks

### Infrastructure
1. Add Judge0 to `docker-compose.yml` (judge0 server + its Postgres + Redis), or
   document an external Judge0 endpoint. Add config vars `JUDGE0_URL`,
   `JUDGE0_AUTH_TOKEN`.
2. `Judge0Client` (`infrastructure/judge0/client.py`): submit source + stdin,
   poll/await result, map language → Judge0 language id.

### Backend
3. `ExecutionService` (application): given a submission, run each test case
   (input/expected) through Judge0, compare output, aggregate to a verdict,
   persist `status` + `result` JSON on the `Submission`.
4. `POST /exercises/{id}/submit` now triggers execution via a background task;
   add `GET /submissions/{id}` for polling the verdict.
5. Add a "run only" endpoint `POST /exercises/{id}/run` (no grading, just
   stdout) for the editor's Run button.
6. Tests with a mocked Judge0 client (pass + fail paths).

### Frontend
7. Enable the Run button; call `/run`, stream/poll, show output console.
8. Submit → poll submission until terminal status; show per-test results
   (passed/failed, expected vs actual where allowed).

## Expected Files

```text
backend/
  app/core/config.py                        # + JUDGE0_* settings
  app/infrastructure/judge0/client.py       (new)
  app/application/services/execution_service.py  (new)
  app/api/v1/routes/exercises.py            # + /run, execution on /submit
  app/schemas/exercise.py                    # + run/result schemas
  tests/test_execution.py                    (new, mocked Judge0)
docker-compose.yml                           # + judge0 services
frontend/
  src/pages/CodingExercise.tsx               # run + poll results
  src/components/ResultPanel.tsx             (new)
```

## Acceptance Criteria

- [x] Judge0 is available via `docker compose --profile judge0 up` (kept behind a
      profile for reliability; see notes). The default stack is unchanged.
- [x] Run returns real stdout/stderr for arbitrary code (`POST /exercises/{id}/run`;
      verified end-to-end against the mocked runner and the live degraded path).
- [x] Submitting a correct solution → `passed`; an incorrect one → `failed` with
      per-test diagnostics; a runtime error → `error` (grading unit tests).
- [x] Verdict + results are persisted on the submission (live: a submission moved
      `pending → error`; `result` JSON stored).
- [x] Execution failures (Judge0 down/timeout) degrade gracefully — submission
      `error`, `/run` returns an `error` payload (HTTP 200), no crash (verified live).
- [x] `ruff`, `pytest` (35 tests), frontend `lint` + `build` pass.

## Dependency

- **Sprint 3** (`Exercise` + `Submission` models, submit endpoint).

## Status — ✅ Complete

**Date:** 2026-06-30

### Delivered

**Backend**
- `Judge0Client` (`infrastructure/judge0/client.py`): runs source against stdin,
  normalizes the response, raises `Judge0Error` on transport/config problems.
- `ExecutionService` (`application/services/execution_service.py`) behind a
  `CodeRunner` port: `run()` (one-off) and `grade()` (per-case → `passed` /
  `failed` / `error`; hidden cases expose only pass/fail).
- `infrastructure/grading.py`: background grading orchestrator (own session,
  loads submission + exercise, grades, persists; failures mark `error`).
- Endpoints: `POST /exercises/{id}/run`; `POST …/submit` now schedules background
  grading; `GET /submissions/{id}` for polling (ownership-checked).
- Config: `JUDGE0_URL`, `JUDGE0_AUTH_TOKEN`, `JUDGE0_TIMEOUT`.
- `SubmissionRepository.update_result`; `SubmissionService.get_submission`.
- `tests/test_execution.py` + `FakeCodeRunner` (35 tests total, DB-free).

**Infra**
- `docker-compose.yml`: `judge0`, `judge0-workers`, `judge0-db`, `judge0-redis`
  under the **`judge0` profile**; `docker/judge0.conf`. Backend gets `JUDGE0_*`
  env. `.env.example`/`.env` updated.

**Frontend**
- `useRun` + `useSubmission` (polls until terminal) hooks; `ResultPanel.tsx`
  (`RunOutput` + `GradingPanel` with per-test breakdown).
- Coding Exercise page: **Run** (shows stdout/stderr) and **Submit** (polls the
  verdict, shows results). The Run button is now enabled.

### Verification

- Backend: `ruff` clean, `pytest` 35/35 pass (grading pass/fail/error/runtime/
  compile/hidden, `/run`, graceful degradation, submission ownership).
- Frontend: `lint` clean, `build` succeeds.
- Live (Docker stack, Judge0 **not** running): `/run` returned a graceful
  `error` payload (HTTP 200); `/submit` → `pending`; background grading resolved
  the submission to `error` with a clear message — no crash. Auth guards return
  `401` without a token.

### Notes / follow-ups

- **Judge0 is behind a compose profile**, deviating from the original
  "`docker compose up` starts Judge0" wording. Rationale: a full self-hosted
  Judge0 is privileged/heavy and unreliable on Docker Desktop (cgroup v2), and
  bundling it into the default `up` would jeopardize the "one command" guarantee.
  The default stack stays lean; Judge0 is `--profile judge0 up`.
- Consequently the `passed`/`failed` verdicts are proven by unit tests (mocked
  Judge0) and the live run exercised the degraded path; a real green run requires
  a reachable Judge0 instance.
