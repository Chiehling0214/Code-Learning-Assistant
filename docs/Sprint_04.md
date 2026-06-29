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

- [ ] `docker compose up` starts Judge0 alongside the existing services.
- [ ] Run returns real stdout/stderr for arbitrary code.
- [ ] Submitting a correct solution → `passed`; an incorrect one → `failed`
      with per-test diagnostics; a runtime error → `error`.
- [ ] Verdict + results are persisted on the submission.
- [ ] Execution failures (Judge0 down/timeout) degrade gracefully (submission
      `error`, no crash).
- [ ] `ruff`, `pytest`, frontend `lint` + `build` pass.

## Dependency

- **Sprint 3** (`Exercise` + `Submission` models, submit endpoint).
