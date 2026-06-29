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
