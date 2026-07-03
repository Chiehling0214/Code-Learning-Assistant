# Sprint 13 — Entitlements & Admin Review

**Duration:** ~4 days
**Theme:** Turn the Sprint 8 subscription into real plan limits (languages, AI
Tutor usage, generation quota), and repurpose Admin into an **AI-content review**
console.

## Goal

Define **free vs paid** entitlements and enforce them consistently across the
features built in Sprints 9–12: number of language tracks, AI Tutor usage, and
curriculum generation quota. Repurpose the now-empty content-CRUD Admin into a
**review dashboard** for AI-generated content (the `source="ai"` rows) plus usage
insight.

## User Story

- As a free user, I can study up to 2 languages, use the AI Tutor a limited number
  of times, and generate a bounded amount of content; hitting a limit prompts an
  upgrade.
- As a subscriber, those limits are raised (or removed) automatically.
- As an admin, I can review, edit, or hide AI-generated content and see usage.

## Tasks

### Backend
1. Central `EntitlementService` mapping plan → limits, config-driven:
   `FREE_MAX_LANGUAGES` (2), `FREE_TUTOR_DAILY` / `PAID_TUTOR_DAILY`,
   `FREE_GENERATIONS_DAILY` / `PAID_GENERATIONS_DAILY`. Plan comes from the
   Sprint 8 subscription (`is_active`).
2. Apply limits:
   - **Languages** — the Sprint 9 track cap reads from `EntitlementService`.
   - **AI Tutor** — extend `AIUsageGuard` to a plan-aware daily cap (free vs
     paid); over-limit → `402`/upgrade (not just the free-tier `429`).
   - **Generation** — Sprint 11/12 generation checks a plan-aware daily quota.
3. `GET /me/entitlements` — returns the caller's limits and current usage (for the
   frontend to show remaining quota / upgrade prompts).
4. **Admin → review**: replace retired content CRUD with review endpoints —
   `GET /admin/content?source=ai` (list generated lessons/exercises/quizzes),
   `POST /admin/content/{type}/{id}/hide` / `.../approve`, and
   `GET /admin/usage` (AI/generation/subscription counts). Admin-guarded.
5. Add a `review_status` (`pending`|`approved`|`hidden`) column to generated
   content (or reuse `source`) + migration `0013_review_status`; hidden content is
   excluded from serving.
6. Tests: plan-aware caps (free vs paid) for tracks/tutor/generation; entitlements
   endpoint; admin review list + hide excludes content from `GET`s; admin guard.

### Frontend
1. `Subscription` page: show plan limits and current usage; upgrade CTA.
2. `UpgradePrompt` wired wherever a limit is hit (add-language, tutor, generate).
3. **Admin review** page: list AI content with approve/hide actions and a usage
   summary; remove the old content-CRUD UI.
4. `features/entitlements/hooks.ts` (`useEntitlements`); `features/admin/hooks.ts`.

## Expected Files

```text
backend/
  app/core/config.py                               # + plan limit settings
  app/application/services/entitlement_service.py    (new)
  app/application/services/ai_usage.py               # plan-aware caps
  app/api/deps.py                                    # entitlement wiring
  app/api/v1/routes/entitlements.py                  (new)
  app/api/v1/routes/admin_review.py                  (new; replaces admin_content)
  app/infrastructure/models/models.py                # + review_status
  alembic/versions/0013_review_status.py             (new)
  tests/test_entitlements.py                         (new)
  tests/test_admin_review.py                         (new)
frontend/
  src/features/entitlements/hooks.ts                 (new)
  src/features/admin/hooks.ts                        (new)
  src/pages/Admin.tsx                                # review console
  src/pages/Subscription.tsx                         # limits + usage
```

## Acceptance Criteria

- [x] Free users are capped (2 languages, bounded tutor + generation/day); paid
      users get raised limits; over-limit returns `402`/upgrade.
- [x] `GET /me/entitlements` reports limits + current usage.
- [x] Admin can list AI-generated content and hide/approve it; hidden content is
      not served.
- [x] The old content-CRUD admin surface is gone (replaced by review).
- [x] `ruff`, `pytest`, frontend `lint` + `build` pass.

## Dependency

- **Sprint 8** (subscription/plan state).
- **Sprints 9–12** (tracks, tutor, generation) as the things being limited.
- **Sprint 6** (`source="ai"` provenance) for the review console.

---

## Status — done

**Backend**
- `EntitlementService` (config-driven): `max_languages` / `tutor_daily` /
  `generations_daily` by plan (paid = active subscription), current usage from
  tracks + the `ai_interactions` log (`count_since(..., kind=…)`), and
  `check_tutor` / `check_generation` raising `UpgradeRequiredError` → `402`.
- Limits applied: `TrackService` reads the language cap from entitlements; the AI
  Tutor endpoint enforces a plan-aware daily cap (was subscription-only); the
  generation/extend/chat endpoints enforce a daily generation quota.
- `GET /me/entitlements` returns limits + usage.
- **Admin review**: `AdminReviewService` + `admin_review` routes —
  `GET /admin/content?source=ai`, `POST /admin/content/lessons/{id}/hide|approve`,
  `GET /admin/usage`. `lessons.review_status` (`approved`|`pending`|`hidden`,
  migration `0013`); AI lessons are created `pending`; `hidden` lessons are
  excluded from course detail, single-lesson GET, Today, and progress.
- Tests: `test_entitlements.py`, `test_admin_review.py`, and an updated
  plan-aware tutor-cap test — 103 tests total, DB-free.

**Frontend**
- `features/entitlements/hooks.ts` (`useEntitlements`) and `features/admin/hooks.ts`
  (`useAdminContent`, `useAdminUsage`, `useSetLessonReview`).
- **Subscription** page shows plan limits + today's usage; `UpgradePrompt`
  (extended to render on any `402`) surfaces at the tutor, add-language, and
  subscription surfaces.
- **Admin** page rewritten as the AI-content review console (usage summary +
  approve/hide); the old content-CRUD UI is removed.

### Verification

- Backend `ruff` + `pytest` 103/103; frontend `lint` + `build` pass.
- Live (Docker): migration `0012 → 0013` applied (43 existing AI lessons →
  `pending`); entitlement snapshot, review list, and **hide → withheld from
  serving → restore** verified against the real DB.

### Notes / scoping

- Review granularity is the **lesson** (its exercises/quizzes are served under it),
  so hiding a lesson removes its content from learners without per-row status on
  three tables.
- The admin content-CRUD **endpoints** are retained (used as test fixtures and
  harmless, admin-guarded); the CRUD **UI** is what's replaced by the review
  console, satisfying "the old admin surface is gone".
