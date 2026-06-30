# Sprint 05 — Quizzes & Auto-Grading

**Duration:** ~3 days
**Theme:** Multiple-choice quizzes attached to lessons/courses, taken by
learners and graded automatically.

## Goal

Model quizzes (questions + choices + correct answers), let learners take a quiz
without the answers leaking, auto-grade submissions, and store the attempt with
a score. Admins can author quizzes.

## User Story

- As a learner, I can take a quiz attached to a lesson/course.
- As a learner, I submit my answers and immediately see my score and which
  questions I got wrong.
- As an admin, I can create quizzes with questions and mark correct answers.

## Tasks

### Backend
1. ORM models `Quiz` (FK → course/lesson), `Question` (FK → quiz, `prompt`,
   `type`), `Choice` (FK → question, `text`, `is_correct`), `QuizAttempt`
   (FK → user, quiz, `score`, `answers` JSON) + migration `0004`.
2. Domain entities + repositories.
3. `QuizService`: get quiz **without** `is_correct` exposed; `grade()` compares
   submitted answers, computes score, persists `QuizAttempt`.
4. Endpoints: `GET /quizzes/{id}` (sanitized), `POST /quizzes/{id}/submit`
   (returns score + correctness), `GET /quizzes/{id}/attempts`.
5. Admin quiz CRUD endpoints (admin guard).
6. Tests: answers never leaked in `GET`; grading correctness; attempt persisted.

### Frontend
1. `Quiz` page: render questions + choices, collect answers.
2. Submit → show score and per-question result.
3. Admin quiz authoring UI.

## Expected Files

```text
backend/
  app/infrastructure/models/models.py        # + Quiz, Question, Choice, QuizAttempt
  alembic/versions/0004_quizzes.py            (new)
  app/domain/entities.py                       # + quiz entities
  app/domain/repositories.py                   # + repos
  app/infrastructure/repositories/sqlalchemy_repositories.py
  app/application/services/quiz_service.py     (new)
  app/api/v1/routes/quizzes.py                 (new)
  app/schemas/quiz.py                          (new)
  tests/test_quiz.py                           (new)
frontend/
  src/features/quizzes/hooks.ts                (new)
  src/pages/Quiz.tsx                           # wired to API
  src/pages/Admin.tsx                          # + quiz authoring
```

## Acceptance Criteria

- [ ] Migration `0004` creates the quiz tables.
- [ ] `GET /quizzes/{id}` never includes `is_correct` / answer keys.
- [ ] `POST /quizzes/{id}/submit` returns a correct score and per-question
      correctness; a `QuizAttempt` row is stored.
- [ ] Admin can author a quiz; non-admin write → `403`.
- [ ] Quiz page renders and reports the score.
- [ ] `ruff`, `pytest`, frontend `lint` + `build` pass.

## Dependency

- **Sprint 2** (courses/lessons to attach quizzes to).
- **Sprint 1** (user owning the attempt).

## Status — ✅ Complete

Quizzes attach to lessons; learners take them without the answer key leaking and
are graded instantly; admins author them.

**Backend**
- Models `Quiz`, `Question`, `Choice`, `QuizAttempt` + migration `0004_quizzes`
  (note: numbered 0004 — Sprint 4 added no table, reusing `submissions`).
- Domain entities (nested `Quiz → Question → Choice`) + `QuizRepository` /
  `QuizAttemptRepository` interfaces and SQLAlchemy implementations.
- `QuizService`: `get_quiz` (full entity; API strips the answer key), `grade`
  (compares answers, computes score, persists a `QuizAttempt`), `list_attempts`,
  and authoring (`create_quiz`, `add_question` with validation, `delete_quiz`).
- Schemas: learner-facing `QuizResponse`/`QuestionResponse`/`ChoiceResponse`
  **omit `is_correct`**; submit/grade and admin authoring schemas.
- Endpoints: `GET /lessons/{id}/quizzes`, `GET /quizzes/{id}` (sanitized),
  `POST /quizzes/{id}/submit`, `GET /quizzes/{id}/attempts`; admin
  `POST /admin/quizzes`, `POST /admin/quizzes/{id}/questions`,
  `DELETE /admin/quizzes/{id}`.
- `tests/test_quiz.py` + `FakeQuizRepository`/`FakeQuizAttemptRepository`
  (44 tests total, DB-free).

**Frontend**
- `features/quizzes/hooks.ts` (quiz read, lesson quizzes, submit, attempts; admin
  create/add-question/delete).
- Quiz page: renders questions + choices, collects answers, submits, shows the
  score and per-question correctness (correct choice highlighted, wrong pick
  flagged).
- Lesson page lists a lesson's quizzes; Admin page gains a quiz-authoring section
  (create quiz under a course→lesson, add questions with choices + correct flag).

### Verification

- Backend: `ruff` clean, `pytest` 44/44 pass (answer-key never leaked, grading
  full/partial score, attempt persisted, admin guard `403`, invalid question
  `400`).
- Frontend: `lint` clean, `build` succeeds.
- Live (Docker stack): migration `0003_exercises → 0004_quizzes` applied to
  Postgres on backend start; all seven quiz endpoints registered in the OpenAPI
  schema; `GET /quizzes/{id}` on a real seeded row returned questions/choices with
  **no `is_correct`**; unknown id → `404`. Auth-stub is disabled in this
  deployment, so `submit`/`attempts` correctly require a token (`401` without
  one); the grading path itself is covered by the unit suite.

### Notes / follow-ups

- Quizzes attach to a **lesson** (mirroring exercises); a lesson belongs to a
  course, so they are reachable from a course too. Attaching directly to a course
  was not needed for the acceptance criteria.
- Questions use a single-correct-choice model (`type = "single"`); the column is
  in place to extend to other question types later.
