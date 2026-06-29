# Sprint 06 — AI Teacher & AI Tutor (Claude)

**Duration:** ~4 days
**Theme:** Bring the AI features online behind a provider interface, powered by
Claude. See [05_AI.md](05_AI.md) for the design this sprint implements.

## Goal

Implement the `AIProvider` port and a concrete `ClaudeAIProvider`, exposing an
**AI Teacher** (explains/expands lesson content for the learner's level) and an
**AI Tutor** (reviews submitted code, gives hints/feedback, answers questions).

## User Story

- As a learner, I can ask the AI Teacher to explain a lesson concept in more
  depth or in simpler terms.
- As a learner stuck on an exercise, I can ask the AI Tutor for a hint or
  feedback on my current code without being given the full answer.
- As the platform, I control which Claude model is used and cap usage per user.

## Tasks

### Backend
1. Define `AIProvider` protocol (`application/ports/ai_provider.py`) with
   `teach()` and `tutor()` (per [05_AI.md](05_AI.md)).
2. `ClaudeAIProvider` (`infrastructure/ai/claude_provider.py`) using the
   Anthropic SDK; model ids from config (default `claude-opus-4-8` for teaching,
   `claude-sonnet-4-6` for tutoring). Add `ANTHROPIC_API_KEY`, model settings.
3. Server-side prompt construction; never pass raw client prompts through.
4. `AITeacherService` / `AITutorService` orchestrating the provider; persist an
   `AIInteraction` record (FK → user, type, tokens) + migration `0005`.
5. Endpoints: `POST /ai/teacher`, `POST /ai/tutor` (accepts exercise id +
   current code + question). Optional streaming response.
6. Per-user rate limiting / token budget; log token usage.
7. Tests with a mocked provider (no live API calls).

### Frontend
1. "Ask AI Teacher" panel on the `Lesson` page.
2. AI Tutor side panel on the `CodingExercise` page (sends current editor code).
3. Streaming/typing UI; loading + error states.

## Expected Files

```text
backend/
  app/core/config.py                          # + ANTHROPIC_API_KEY, model ids, budgets
  app/application/ports/ai_provider.py        (new)
  app/infrastructure/ai/claude_provider.py    (new)
  app/application/services/{ai_teacher_service,ai_tutor_service}.py  (new)
  app/infrastructure/models/models.py          # + AIInteraction
  alembic/versions/0005_ai_interactions.py     (new)
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
- [ ] Model selection is configuration-driven; swapping the model id requires no
      code change.
- [ ] Token usage is logged; per-user rate limit is enforced.
- [ ] All AI calls go through `AIProvider` — no provider SDK calls leak into the
      api/application layers.
- [ ] Tests pass with the provider mocked (no network).
- [ ] `ruff`, `pytest`, frontend `lint` + `build` pass.

## Dependency

- **Sprint 2** (lessons for the Teacher).
- **Sprint 3 / 4** (exercises + submitted code for the Tutor).
