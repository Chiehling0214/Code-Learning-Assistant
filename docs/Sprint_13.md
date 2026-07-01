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

- [ ] Free users are capped (2 languages, bounded tutor + generation/day); paid
      users get raised limits; over-limit returns `402`/upgrade.
- [ ] `GET /me/entitlements` reports limits + current usage.
- [ ] Admin can list AI-generated content and hide/approve it; hidden content is
      not served.
- [ ] The old content-CRUD admin surface is gone (replaced by review).
- [ ] `ruff`, `pytest`, frontend `lint` + `build` pass.

## Dependency

- **Sprint 8** (subscription/plan state).
- **Sprints 9–12** (tracks, tutor, generation) as the things being limited.
- **Sprint 6** (`source="ai"` provenance) for the review console.
