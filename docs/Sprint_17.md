# Sprint 17 — Polish & Quality: Streaming AI, E2E Tests, Account Settings

**Duration:** ~4 days
**Theme:** Make it feel like a product. Stream AI answers token-by-token, cover
the golden path with real browser tests, give users account control, and tighten
mobile layout.

## Goal

Kill the three roughest edges: (1) AI answers appear only after a long silent
wait — stream them instead; (2) nothing tests the app the way a user clicks
through it — add Playwright E2E for the golden path; (3) users can't manage
their account — add settings (display name, delete account). Plus a mobile
layout pass on the learning surfaces.

## User Story

- As a learner, AI Teacher/Tutor/course-chat answers start appearing within a
  second and stream in, instead of a 10-second spinner.
- As a user, I can change my display name and delete my account (all my data).
- As the developer, one command drives a real browser through signup →
  placement → course → exercise and fails loudly if the flow breaks.

## Tasks

### Backend
1. **Streaming**: SSE variants of the AI endpoints — `POST /ai/teacher/stream`,
   `/ai/tutor/stream` (and course chat reply) using Gemini streaming
   (`generate_content_stream`) behind a new `AIProvider.teach_stream` /
   `tutor_stream`; usage recorded once at stream end; same entitlement checks.
   Non-stream endpoints stay (fallback + tests).
2. **Account**: `PATCH /me` (display name) exists? — verify; add
   `DELETE /me` (cascade: tracks/courses/attempts/submissions/reviews/chats,
   Stripe sub noted, Firebase user deletion documented). Tests for full cascade.
3. Consistent API error envelope audit (detail strings, status codes) +
   `X-Request-ID` surfaced in error responses for support.

### Frontend
1. Consume SSE in the Teacher/Tutor/chat panels (progressive Markdown render,
   graceful fallback to the non-stream endpoint on error).
2. **Settings page** (`/settings`): display name edit, plan summary link,
   danger zone (delete account with confirm-by-typing-email).
3. **Mobile pass**: lesson page, exercise editor (Monaco height/scroll), quiz,
   placement review — no horizontal scroll at 375px; nav collapses.
4. Loading skeletons for dashboard/course/lesson (replace text-only loaders).

### E2E (new workspace `e2e/`)
5. Playwright + backend in stub-auth mode with the fake AI provider via a test
   compose profile (`AUTH_STUB_ENABLED=true`, mocked Gemini through a flag or
   recorded fixtures): specs for onboarding → placement submit → review →
   course generation (fake) → open lesson → run exercise (fake runner) → quiz
   submit → review page.
6. Wire into CI (Sprint 14's `ci.yml`) as a separate job.

## Expected Files

```text
backend/
  app/application/ports/ai_provider.py     # + teach_stream/tutor_stream
  app/infrastructure/ai/gemini_provider.py # streaming impls
  app/api/v1/routes/ai.py                  # SSE endpoints
  app/api/v1/routes/me.py                  # DELETE /me
  tests/test_account_delete.py             (new)
e2e/
  playwright.config.ts, specs/golden-path.spec.ts   (new)
frontend/
  src/lib/sse.ts                            (new)
  src/components/A*Panel.tsx                # streaming consumption
  src/pages/Settings.tsx                    (new)
  src/routes.tsx                            # /settings
```

## Acceptance Criteria

- [ ] Teacher/Tutor/chat answers stream progressively; fallback works.
- [ ] Deleting an account removes all learner data (verified by test).
- [ ] Golden-path E2E passes headlessly in CI.
- [ ] Core learning pages are usable at 375px width.
- [ ] `ruff`, `pytest`, frontend `lint` + `build`, and E2E pass.

## Dependency

- **Sprint 14** (CI to host the E2E job).
- **Sprint 6/12** AI surfaces being streamed.
