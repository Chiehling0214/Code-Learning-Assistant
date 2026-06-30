# Sprint 06 — AI Teacher & AI Tutor (Gemini)

**Duration:** ~4 days
**Theme:** Bring the AI features online behind a provider interface, powered by
**Google Gemini (free tier)**. See [05_AI.md](05_AI.md) for the design this
sprint implements.

## Goal

Implement the `AIProvider` port and a concrete `GeminiAIProvider`, exposing an
**AI Teacher** (explains/expands lesson content for the learner's level) and an
**AI Tutor** (reviews submitted code, gives hints/feedback, answers questions).
The AI Teacher can also **generate lessons/exercises that are written back into
the existing `lessons`/`exercises` tables** (see "Content generation" in
[05_AI.md](05_AI.md)), so generated content is served and graded by the same
Sprint 2–4 machinery.

## User Story

- As a learner, I can ask the AI Teacher to explain a lesson concept in more
  depth or in simpler terms.
- As a learner stuck on an exercise, I can ask the AI Tutor for a hint or
  feedback on my current code without being given the full answer.
- As the platform, I control which Gemini model is used and cap usage per user
  (the free tier has hard request limits).
- As an admin, I can have the AI Teacher generate a lesson or exercise for a
  topic/level; it is saved as a (reviewable) row in the normal content tables.

## Tasks

### Backend
1. Define `AIProvider` protocol (`application/ports/ai_provider.py`) with
   `teach()` and `tutor()` (per [05_AI.md](05_AI.md)).
2. `GeminiAIProvider` (`infrastructure/ai/gemini_provider.py`) using the Google
   Gen AI SDK (`google-genai`); model ids from config (default
   `gemini-2.5-flash`; `gemini-2.5-pro` optionally for teaching). Add
   `GEMINI_API_KEY` (from Google AI Studio) + model settings. Handle `429`
   quota errors from the free tier gracefully.
3. Server-side prompt construction; never pass raw client prompts through.
4. `AITeacherService` / `AITutorService` orchestrating the provider; persist an
   `AIInteraction` record (FK → user, type, tokens) + migration `0005`.
5. Endpoints: `POST /ai/teacher`, `POST /ai/tutor` (accepts exercise id +
   current code + question). Optional streaming response.
6. Per-user rate limiting / token budget; log token usage.
7. Tests with a mocked provider (no live API calls).

### Backend — content generation
8. Add a `source` column (`human` | `ai`) to `lessons` and `exercises` (migration
   `0006_content_source`) so AI-authored rows are distinguishable and reviewable.
9. `GenerateContentService` (`application/services/generate_content_service.py`):
   builds a generation request from topic + learner level, calls
   `AIProvider.teach()`, and **writes the result through `ContentService` into the
   `lessons`/`exercises` tables** — generation is just another author, so serving
   (`GET /courses|/lessons|/exercises`) and grading (Judge0) are unchanged.
10. Self-verify generated exercises before publishing: run the reference solution
    against the generated `test_spec` via the Sprint 4 Judge0 path; reject if it
    doesn't pass its own tests.
11. Admin endpoint `POST /admin/ai/generate` to trigger generation for a
    lesson/exercise (guarded by `require_admin`); generated rows default to
    `source = "ai"` for later review.

### Frontend
1. "Ask AI Teacher" panel on the `Lesson` page.
2. AI Tutor side panel on the `CodingExercise` page (sends current editor code).
3. Streaming/typing UI; loading + error states.

## Expected Files

```text
backend/
  app/core/config.py                          # + GEMINI_API_KEY, model ids, budgets
  app/application/ports/ai_provider.py        (new)
  app/infrastructure/ai/gemini_provider.py    (new)
  app/application/services/{ai_teacher_service,ai_tutor_service}.py  (new)
  app/application/services/generate_content_service.py  (new — AI -> lessons/exercises)
  app/infrastructure/models/models.py          # + AIInteraction, + source columns
  alembic/versions/0005_ai_interactions.py     (new)
  alembic/versions/0006_content_source.py      (new — source on lessons/exercises)
  app/api/v1/routes/ai.py                       (new)
  app/schemas/ai.py                             (new)
  tests/test_ai.py                              (new, mocked provider)
frontend/
  src/features/ai/hooks.ts                      (new)
  src/components/AiTutorPanel.tsx               (new)
  src/components/AiTeacherPanel.tsx             (new)
  src/pages/{Lesson,CodingExercise}.tsx         # mount panels
```

## Acceptance Criteria

- [ ] `POST /ai/teacher` returns a relevant explanation for a lesson concept.
- [ ] `POST /ai/tutor` returns feedback that references the submitted code and
      gives hints rather than a full solution.
- [ ] Model selection is configuration-driven; swapping the model id (or provider)
      requires no code change.
- [ ] Usage is logged; per-user rate limiting respects the Gemini free-tier limits
      and `429` quota errors are handled gracefully.
- [ ] All AI calls go through `AIProvider` — no provider SDK calls leak into the
      api/application layers.
- [ ] AI-generated lessons/exercises are written via `ContentService` into the
      existing tables, marked `source = "ai"`, and served unchanged by the
      existing `GET` endpoints.
- [ ] A generated exercise is self-verified (its reference solution passes its
      own `test_spec` via Judge0) before being published.
- [ ] Tests pass with the provider mocked (no network).
- [ ] `ruff`, `pytest`, frontend `lint` + `build` pass.

## Dependency

- **Sprint 2** (lessons for the Teacher).
- **Sprint 3 / 4** (exercises + submitted code for the Tutor).
