# Sprint 03 — Coding Exercises (Model & Submissions)

**Duration:** ~3 days
**Theme:** Exercise data model and submission storage. Code **execution** is
deliberately deferred to Sprint 4 — this sprint gets exercises loading into the
Monaco editor and submissions persisted with a `pending` status.

## Goal

Model coding exercises (tied to lessons/courses) with starter code and a test
specification, expose them to the frontend, and store learner submissions. The
"Run/Submit" action records a submission; grading arrives next sprint.

## User Story

- As a learner, I can open a coding exercise and see the prompt and starter code
  in the editor.
- As a learner, I can submit my code; the submission is saved and shown as
  pending.
- As a learner, I can see my previous submissions for an exercise.

## Tasks

### Backend
1. `Exercise` ORM model (FK → lesson, `language`, `prompt`, `starter_code`,
   `test_spec` JSON) + `Submission` model (FK → user, exercise, `code`,
   `status` enum `pending|passed|failed|error`, `result` JSON nullable) +
   migration `0003`.
2. Domain entities + repositories.
3. `ExerciseService`: get exercise; `SubmissionService`: create submission
   (status `pending`), list submissions for user+exercise.
4. Endpoints: `GET /exercises/{id}`, `POST /exercises/{id}/submit`
   (stores submission), `GET /exercises/{id}/submissions`.
5. Admin endpoint to create exercises (reuse admin guard).
6. Tests: submission is persisted with `pending` status.

### Frontend
1. `CodingExercise` page loads exercise from API; seed Monaco with
   `starter_code` and correct language.
2. Submit button → mutation that POSTs code; show "pending" state and add to a
   submissions list.
3. Submissions history panel.

## Expected Files

```text
backend/
  app/infrastructure/models/models.py          # + Exercise, Submission
  alembic/versions/0003_exercises.py            (new)
  app/domain/entities.py                         # + Exercise, Submission
  app/domain/repositories.py                     # + repos
  app/infrastructure/repositories/sqlalchemy_repositories.py
  app/application/services/{exercise_service,submission_service}.py  (new)
  app/api/v1/routes/exercises.py                 (new)
  app/schemas/exercise.py                        (new)
  tests/test_submissions.py                      (new)
frontend/
  src/features/exercises/hooks.ts                (new)
  src/pages/CodingExercise.tsx                   # wired to API
  src/components/SubmissionList.tsx              (new)
```

## Acceptance Criteria

- [x] Migration `0003` creates `exercises` and `submissions` tables (applied
      live by the backend container; confirmed via `\dt`).
- [x] `GET /exercises/{id}` returns prompt + starter code + language (and never
      leaks `test_spec`).
- [x] Monaco loads the starter code in the exercise's language.
- [x] `POST /exercises/{id}/submit` persists a submission with status `pending`
      (`test_submissions.py`; submit requires auth → `401` without a token).
- [x] Submissions history lists prior attempts.
- [x] `ruff`, `pytest` (24 tests), frontend `lint` + `build` pass.

## Dependency

- **Sprint 2** (lessons/courses to attach exercises to).
- **Sprint 1** (authenticated user owning the submission).

## Status — ✅ Complete

**Date:** 2026-06-30

### Delivered

**Backend**
- `Exercise` + `Submission` ORM models and migration `0003_exercises`
  (`test_spec`/`result` as JSONB; submission `status` defaults `pending`).
- Domain entities + `ExerciseRepository`/`SubmissionRepository` interfaces and
  SQLAlchemy implementations.
- `ExerciseService` and `SubmissionService` (`application/services/`).
- Endpoints (`api/v1/routes/exercises.py`): public `GET /exercises/{id}` and
  `GET /lessons/{id}/exercises`; learner `POST /exercises/{id}/submit` +
  `GET /exercises/{id}/submissions`; admin `POST/DELETE /admin/exercises`.
- `ExerciseResponse` excludes `test_spec` (hidden test cases).
- Seed extended with a sample exercise ("Hello, CodePath").
- `tests/test_submissions.py` + exercise/submission fakes; shared `fakes`
  fixture in `conftest.py` (24 tests total, DB-free).

**Frontend**
- `features/exercises/hooks.ts` (exercise/submission queries + submit mutation).
- Coding Exercise page wired: loads exercise, seeds Monaco with starter code +
  language, submits code (`pending`), shows submission history
  (`components/SubmissionList.tsx`). Run button stays disabled (Sprint 4).
- Lesson page links to its exercises.

### Verification

- Backend: `ruff` clean, `pytest` 24/24 pass.
- Frontend: `lint` clean, `build` succeeds.
- Live (Docker stack): migration `0003` applied; seed added the exercise;
  `GET /lessons/{id}/exercises` and `GET /exercises/{id}` work (no `test_spec`
  leak); submit/admin without token → `401`.

### Notes / follow-ups

- Submissions are stored `pending`; **Sprint 4** adds Judge0 execution + grading
  that fills `status`/`result`. The `test_spec` column already carries the hidden
  test cases for that.
- Admin can author exercises via the API (`POST /admin/exercises`); a dedicated
  Admin-page exercises UI can be added later if desired.
