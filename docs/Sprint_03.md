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

- [ ] Migration `0003` creates `exercises` and `submissions` tables.
- [ ] `GET /exercises/{id}` returns prompt + starter code + language.
- [ ] Monaco loads the starter code in the exercise's language.
- [ ] `POST /exercises/{id}/submit` persists a submission with status `pending`.
- [ ] Submissions history lists prior attempts.
- [ ] `ruff`, `pytest`, frontend `lint` + `build` pass.

## Dependency

- **Sprint 2** (lessons/courses to attach exercises to).
- **Sprint 1** (authenticated user owning the submission).
