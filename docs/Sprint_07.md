# Sprint 07 — Recommendation ("Today") & Progress Analytics

**Duration:** ~4 days
**Theme:** Track learner progress and assemble a personalized daily plan.

## Goal

Record completion events across lessons, exercises, and quizzes; compute
aggregate progress; and generate a "Today" plan of the next items the learner
should tackle, ordered by course structure and tuned to their skill level.

## User Story

- As a learner, my completed lessons/exercises/quizzes are tracked.
- As a learner, I open **Today** and see a focused list of what to do next.
- As a learner, I open **Progress** and see my completion stats and streak.

## Tasks

### Backend
1. `ProgressEvent` model (FK → user, `item_type`, `item_id`, `status`,
   `score` nullable, `completed_at`) + migration `0006`. Emit events from the
   submission-grading (Sprint 4) and quiz-grading (Sprint 5) flows.
2. `ProgressService`: aggregate per-course completion %, totals, current streak.
3. `RecommendationService`: rule-based — next incomplete items in course order,
   filtered/weighted by `StudentProfile.skill_level`; cap the daily list size.
4. Endpoints: `GET /today` (ordered plan), `GET /progress` (aggregates).
5. Tests: completing an item advances the plan; progress aggregates are correct.

### Frontend
1. `Today` page: render the plan with links to each item (lesson/exercise/quiz).
2. `Progress` page: completion bars per course, totals, streak indicator.
3. Mark-complete wiring where applicable (e.g. finishing a lesson).

## Expected Files

```text
backend/
  app/infrastructure/models/models.py          # + ProgressEvent
  alembic/versions/0006_progress.py             (new)
  app/domain/entities.py                         # + ProgressEvent
  app/domain/repositories.py                     # + ProgressRepository
  app/infrastructure/repositories/sqlalchemy_repositories.py
  app/application/services/{progress_service,recommendation_service}.py  (new)
  app/api/v1/routes/{today,progress}.py          (new)
  app/schemas/{progress,today}.py                (new)
  tests/test_recommendation.py                   (new)
frontend/
  src/features/progress/hooks.ts                 (new)
  src/pages/{Today,Progress}.tsx                 # wired to API
  src/components/ProgressBar.tsx                 (new)
```

## Acceptance Criteria

- [ ] Migration `0006` creates `progress_events`.
- [ ] Grading an exercise / quiz writes a `ProgressEvent`.
- [ ] `GET /today` returns ordered next items and excludes completed ones.
- [ ] `GET /progress` returns accurate per-course completion and a streak count.
- [ ] Today and Progress pages render live data (no placeholders).
- [ ] `ruff`, `pytest`, frontend `lint` + `build` pass.

## Dependency

- **Sprint 2** (content to recommend / complete).
- **Sprint 4** (exercise verdicts) and **Sprint 5** (quiz attempts) as
  completion sources.

## Status — ✅ Complete

Completion is tracked across lessons/exercises/quizzes; a personalized "Today"
plan surfaces the next items, and Progress shows per-course completion + streak.

> **Migration numbering:** the plan called this `0006`, but `0006_content_source`
> was taken in Sprint 6, so the progress migration is **`0007_progress`**.

**Backend**
- `ProgressEvent` model + migration `0007_progress`; domain entity +
  `ProgressRepository` + SQLAlchemy implementation.
- Events emitted automatically: exercise grading (`infrastructure/grading.py`,
  via the testable `record_exercise_progress` helper — records `passed`/`failed`,
  skips infra `error`) and quiz submission (`QuizService.grade`, now given a
  `ProgressRepository`); lessons via `POST /lessons/{id}/complete`.
- `ProgressService` (per-course completion %, totals, day streak; completion
  semantics: lesson/quiz = event exists, exercise = `passed`) and
  `RecommendationService` (rule-based next-incomplete-in-course-order, capped by
  skill level: beginner 3 / intermediate 5 / advanced 8).
- Endpoints: `GET /today`, `GET /progress`, `POST /lessons/{id}/complete`.
- `tests/test_recommendation.py` (60 tests total, DB-free).

**Frontend**
- `features/progress/hooks.ts` (`useToday`, `useProgress`, `useMarkLessonComplete`);
  `ProgressBar` component.
- `Today` page: ordered plan with links per item (lesson/exercise/quiz), empty
  state. `Progress` page: overall % + streak + per-course bars. Lesson page gains
  a "Mark lesson complete" button.

### Verification

- Backend: `ruff` clean, `pytest` 60/60 pass (Today lists then excludes completed
  items, per-user isolation, progress aggregates + streak, grading→progress
  helper).
- Frontend: `lint` clean, `build` succeeds.
- Live (Docker stack): migration `0006 → 0007` applied to Postgres on start;
  `/today`, `/progress`, `/lessons/{id}/complete` registered in the OpenAPI
  schema; with auth-stub disabled they correctly require a token (`401`).

### Notes / follow-ups

- Recommendation is rule-based (course order + skill-level cap); AI-driven "fill
  my weak spot" generation (using Sprint 6's `GenerateContentService`) is a
  natural follow-up but was out of scope here.
- Exercise-grading progress runs inside the Sprint 4 background task; its emission
  is covered by a focused unit test of the `record_exercise_progress` helper.
