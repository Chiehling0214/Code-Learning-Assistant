# Sprint 09 — Onboarding & Language Tracks

**Duration:** ~3 days
**Theme:** First-login onboarding — the learner picks a language to study before
seeing a dashboard — and per-user "language tracks" that anchor all later
personalization.

> **Direction change (Sprints 9–13).** From here the product pivots to
> **AI-generated, personalized curricula**. Content is no longer authored by
> admins; it is generated per learner (Sprint 11). The manual content CRUD and
> seed from Sprints 2–3 are **deprecated** — kept only as dev fixtures until
> Sprint 11 removes them from the primary flow, and the admin surface is
> repurposed in Sprint 13.

## Goal

On first sign-in, route the learner to an onboarding screen — **"What do you want
to study?"** — instead of the dashboard. Persist the chosen language(s) as
**tracks**. Free users may hold at most **2** tracks; adding more prompts an
upgrade. Existing users can add/remove tracks later from the dashboard.

## User Story

- As a new learner, right after I sign in I'm asked what I want to study and I
  pick a language — I don't land on an empty dashboard.
- As a learner, I can add another language later (up to my plan's limit).
- As a free user, trying to add a 3rd language prompts me to upgrade.

## Tasks

### Backend
1. `LanguageTrack` model (FK → user, FK → language, `level` nullable,
   `status` = `onboarding` | `active`, timestamps; unique `(user_id, language_id)`)
   + migration `0009_language_tracks`. Domain entity + `LanguageTrackRepository`.
2. `TrackService`: list a user's tracks, create a track (enforcing the plan's
   language cap), delete a track. Cap is config-driven
   (`FREE_MAX_LANGUAGES`, default 2) and lifted for active subscribers.
3. Endpoints: `GET /me/tracks`, `POST /me/tracks` (`{language_id}`; `409`/`402`
   when over the free cap and not subscribed), `DELETE /me/tracks/{id}`.
4. Extend `GET /me` (or add `GET /me/state`) with an `onboarded` flag
   (true once the user has ≥1 track) so the frontend can route first-login users.
5. Tests: cap enforced (free 2 → 3rd blocked; subscriber allowed); track
   create/list/delete; onboarded flag flips.

### Frontend
1. `Onboarding` page (`/onboarding`): "What do you want to study?" language grid
   (from `GET /languages`), select → `POST /me/tracks` → continue.
2. Routing: after auth, if `onboarded` is false, redirect to `/onboarding`
   instead of `/dashboard` (guard in `ProtectedRoute` / a post-login effect).
3. Dashboard: show the learner's tracks and an **"Add a language"** action
   (opens the picker; shows `UpgradePrompt` when at the free cap).
4. `features/tracks/hooks.ts` (`useTracks`, `useAddTrack`, `useRemoveTrack`).

## Expected Files

```text
backend/
  app/infrastructure/models/models.py            # + LanguageTrack
  alembic/versions/0009_language_tracks.py        (new)
  app/domain/entities.py                           # + LanguageTrack
  app/domain/repositories.py                       # + LanguageTrackRepository
  app/infrastructure/repositories/sqlalchemy_repositories.py
  app/application/services/track_service.py        (new)
  app/api/v1/routes/tracks.py                      (new)
  app/schemas/track.py                             (new)
  app/core/config.py                               # + FREE_MAX_LANGUAGES
  tests/test_tracks.py                             (new)
frontend/
  src/features/tracks/hooks.ts                     (new)
  src/pages/Onboarding.tsx                         (new)
  src/pages/Dashboard.tsx                          # tracks + add-language
  src/components/ProtectedRoute.tsx                # first-login redirect
```

## Acceptance Criteria

- [ ] First-login users are routed to `/onboarding`, not `/dashboard`.
- [ ] Selecting a language creates a track and marks the user onboarded.
- [ ] Free users are capped at 2 tracks; a 3rd returns `402`/upgrade; subscribers
      exceed the cap.
- [ ] Tracks can be listed, added, and removed from the dashboard.
- [ ] `ruff`, `pytest`, frontend `lint` + `build` pass.

## Dependency

- **Sprint 1** (users/profile) and **Sprint 2** (languages).
- **Sprint 8** (subscription state) for the paid language cap.

## Status — ✅ Complete

First-login learners pick a language before seeing a dashboard; language "tracks"
are capped by plan.

**Backend**
- `LanguageTrack` model + migration `0009_language_tracks` (unique per
  user+language); domain entity + `LanguageTrackRepository` + SQLAlchemy impl.
- `TrackService`: list (enriched with language name/slug), `has_tracks`,
  `add_track` (validates language `404`, duplicate `409`, plan cap `402`),
  `remove_track` (ownership-checked). Cap is config-driven
  (`FREE_MAX_LANGUAGES`=2, `PAID_MAX_LANGUAGES`) and lifted for active subscribers.
- `GET /me` gains an `onboarded` flag (true once ≥1 track).
- Endpoints: `GET/POST /me/tracks`, `DELETE /me/tracks/{id}`.
- `tests/test_tracks.py` (73 tests total, DB-free).

**Frontend**
- `features/tracks/hooks.ts` (`useTracks`, `useAddTrack`, `useRemoveTrack`).
- `Onboarding` page ("What do you want to study?") + `OnboardingGate` that
  redirects first-login users there instead of `/dashboard`.
- Dashboard "Your languages" section: chips + add/remove, `UpgradePrompt` at the
  free cap.

### Verification

- Backend: `ruff` clean, `pytest` 73/73 pass (onboarded flip, add/list/remove,
  `404`/`409`, free cap `402`, subscriber over-cap).
- Frontend: `lint` clean, `build` succeeds.
- Live (Docker stack): migration `0008 → 0009` applied to Postgres on start;
  `/me/tracks` (GET/POST/DELETE) registered; `language_tracks` table present;
  endpoints require a token (`401`).

### Notes / follow-ups

- A track starts `status="active"`; the `level` column stays null until the
  **Sprint 10** placement test sets it (and may introduce an `onboarding` status
  before placement completes).
- The onboarding gate keys off the tracks query (not a session flag), so adding a
  track (which invalidates the query) immediately lets the learner into the app.
- Manual content CRUD/seed still exists this sprint; **Sprint 11** replaces it
  with AI generation, at which point languages will need a non-admin source.
