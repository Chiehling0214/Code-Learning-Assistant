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
