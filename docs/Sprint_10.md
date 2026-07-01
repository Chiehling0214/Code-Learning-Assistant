# Sprint 10 — Placement Test

**Duration:** ~4 days
**Theme:** After a learner picks a language, the AI runs a short placement test
and assigns a level that drives curriculum generation.

## Goal

For a new track, generate a **placement assessment** — a handful of
multiple-choice questions **plus two short coding tasks** — grade it, and derive
the learner's level (`beginner` | `intermediate` | `advanced`). Store the level
on the track (and mirror to `student_profiles.skill_level`) so Sprint 11 can
generate an appropriately-pitched course.

## User Story

- As a learner, right after choosing a language I take a quick placement test
  (some multiple-choice, a couple of small coding tasks).
- As a learner, I immediately see my assessed level and move on to my course.
- As the platform, the level is computed server-side and cannot be self-set.

## Tasks

### Backend
1. Extend the `AIProvider` port with `generate_placement(language, ...)` →
   structured output: MCQs (prompt + choices + correct index) and 2 coding tasks
   (prompt + starter + `test_spec` + reference solution). Implement in
   `GeminiAIProvider`.
2. `PlacementAssessment` + `PlacementResult` models (FK → track/user; store the
   generated items and the submitted answers/score) + migration `0010_placement`.
   Reuse the quiz grading approach for MCQs and the Sprint 4 Judge0 path for the
   coding tasks (self-verify the reference solutions before serving).
3. `PlacementService`: `generate(track_id)` (idempotent per track), `get(track_id)`
   (answer keys stripped), `submit(track_id, answers, code)` → grade → map score
   to a level → persist on the track + profile.
4. Endpoints: `POST /me/tracks/{id}/placement` (generate), `GET …/placement`
   (sanitized), `POST …/placement/submit` (returns level + breakdown).
5. Level mapping is rule-based and documented (e.g. `<40%` beginner,
   `40–75%` intermediate, `>75%` advanced), weighting the coding tasks higher.
6. Tests (AI + Judge0 mocked): answer keys never leak; scoring→level mapping;
   level persists on the track; generation is idempotent.

### Frontend
1. `Placement` page (`/tracks/:id/placement`): renders MCQs + two Monaco coding
   tasks, submits, shows the assessed level, then routes to the course.
2. `features/placement/hooks.ts` (`usePlacement`, `useSubmitPlacement`).
3. Onboarding flow: after selecting a language (Sprint 9) → placement → result.

## Expected Files

```text
backend/
  app/application/ports/ai_provider.py            # + generate_placement
  app/infrastructure/ai/gemini_provider.py
  app/infrastructure/models/models.py              # + PlacementAssessment/Result
  alembic/versions/0010_placement.py               (new)
  app/application/services/placement_service.py     (new)
  app/api/v1/routes/placement.py                    (new)
  app/schemas/placement.py                          (new)
  tests/test_placement.py                           (new, mocked AI + Judge0)
frontend/
  src/features/placement/hooks.ts                   (new)
  src/pages/Placement.tsx                            (new)
```

## Acceptance Criteria

- [ ] Generating a placement returns MCQs + 2 coding tasks; answer keys/reference
      solutions are never sent to the client.
- [ ] Submitting answers computes a level and stores it on the track + profile.
- [ ] Generation is idempotent per track; re-taking is explicit.
- [ ] AI and Judge0 are behind their existing ports (mocked in tests).
- [ ] `ruff`, `pytest`, frontend `lint` + `build` pass.

## Dependency

- **Sprint 9** (a track to assess).
- **Sprint 5** (quiz/MCQ grading) and **Sprint 4** (Judge0) as grading engines.
- **Sprint 6** (`AIProvider`) for generation.

## Status — ✅ Complete

Picking a language leads into an AI-generated placement test; the assessed level
is stored on the track and profile.

> **Design note:** the plan listed separate `PlacementAssessment` + `PlacementResult`
> models; these were consolidated into a single `placement_assessments` row
> (generated `items` + `result`/`score`/`level`), which is simpler and keeps one
> assessment per track. MCQs/coding are stored as JSON rather than reusing the
> quiz/exercise tables, since a placement is standalone (not attached to a lesson).

**Backend**
- `AIProvider.generate_placement` (+ `GeneratedPlacement` DTO) implemented in
  `GeminiAIProvider`.
- `PlacementAssessment` model + migration `0010_placement` (one per track);
  entity + `PlacementRepository`; `LanguageTrackRepository.set_level`.
- `PlacementService`: idempotent `generate` (builds items with ids, **self-verifies**
  each coding task's reference solution via the Judge0 path before storing),
  sanitized `get`, and `submit` (grades MCQs + coding, weights coding higher,
  maps percent → level `<40`/`40–75`/`>75`, persists on track + profile). AI usage
  is rate-limited/logged via `AIUsageGuard`.
- Endpoints: `POST/GET /me/tracks/{id}/placement`, `POST …/placement/submit`.
- `tests/test_placement.py` (79 tests total, DB-free, no network).

**Frontend**
- `features/placement/hooks.ts` (`usePlacement`, `useSubmitPlacement`).
- `Placement` page: MCQs (radio) + Monaco coding editors, submit → shows the
  assessed level → continue. Onboarding now routes into the placement after a
  language is chosen.

### Verification

- Backend: `ruff` clean, `pytest` 79/79 pass (sanitized read, idempotent
  generate, score→level mapping both extremes, level persisted, `404` paths).
- Frontend: `lint` clean, `build` succeeds.
- Live (Docker stack): migration `0009 → 0010` applied; `/me/tracks/{id}/placement`
  (POST/GET + submit) registered; `placement_assessments` table present; endpoints
  require a token (`401`).

### Notes / follow-ups

- Self-verification is **lenient**: a coding task is dropped only when its
  reference solution *ran and produced the wrong output* (`failed`); it is kept
  when it passes and when the grader is unavailable (`error` — Judge0
  quota/outage), and the placement never drops *all* coding tasks. This prevents
  a flaky sandbox from stripping the coding section (an early bug produced
  MCQ-only tests). Generation prompts also require code to be in fenced Markdown
  blocks so the frontend renders it as code, not plain text.
- Re-taking a placement is explicit (generation is idempotent per track); a
  "retake" flow can reset it in a later sprint if needed.
- The assessed `level` is the signal **Sprint 11** uses to pitch generated
  curricula.
