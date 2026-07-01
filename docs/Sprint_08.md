# Sprint 08 — Subscriptions, Billing & Hardening

**Duration:** ~4 days
**Theme:** Monetization (subscription tiers + Stripe) plus production hardening
ahead of release.

## Goal

Introduce subscription plans with Stripe checkout and webhooks, gate premium
features (e.g. AI Tutor, advanced courses) by entitlement, and harden the
platform for production (rate limits, security review, e2e tests, prod deploy).

## User Story

- As a learner, I can view plans and subscribe via a secure checkout.
- As a subscriber, premium features unlock automatically after payment.
- As a free user, premium actions prompt me to upgrade instead of failing.
- As the team, I can deploy a hardened production build.

## Tasks

### Backend — billing
1. `Subscription` model (FK → user, `plan`, `status`, `stripe_customer_id`,
   `current_period_end`) + migration `0007`.
2. Stripe integration (`infrastructure/billing/stripe_client.py`): create
   checkout session, handle webhook events (checkout completed, subscription
   updated/canceled). Config `STRIPE_API_KEY`, `STRIPE_WEBHOOK_SECRET`,
   `STRIPE_PRICE_*`.
3. `SubscriptionService` + entitlement dependency (`require_active_subscription`)
   used to gate premium endpoints (e.g. AI Tutor, premium courses).
4. Endpoints: `GET /subscription`, `POST /subscription/checkout`,
   `POST /webhooks/stripe` (signature-verified).
5. Tests with a mocked Stripe client (checkout + webhook state transitions).

### Hardening
6. Global rate limiting + tightened CORS for production.
7. Consistent error envelopes; audit auth on every protected route.
8. Run the security review pass; address findings.
9. End-to-end smoke test (Playwright): sign in → open course → submit exercise.
10. Production `docker-compose.prod.yml` (frontend served via Nginx `prod`
    stage, gunicorn/uvicorn workers); update [08_DEPLOYMENT.md](08_DEPLOYMENT.md).

### Frontend
11. `Subscription` page: plans, checkout button, manage/cancel, current status.
12. Upgrade prompts on gated features.

## Expected Files

```text
backend/
  app/core/config.py                          # + STRIPE_* settings
  app/infrastructure/models/models.py          # + Subscription
  alembic/versions/0007_subscriptions.py       (new)
  app/infrastructure/billing/stripe_client.py  (new)
  app/application/services/subscription_service.py  (new)
  app/api/deps.py                              # + require_active_subscription
  app/api/v1/routes/subscription.py            (new)
  app/api/v1/routes/webhooks.py                (new)
  tests/test_subscription.py                   (new, mocked Stripe)
  tests/e2e/                                   (new, Playwright smoke)
docker-compose.prod.yml                        (new)
frontend/
  src/features/billing/hooks.ts                (new)
  src/pages/Subscription.tsx                   # wired to Stripe checkout
  src/components/UpgradePrompt.tsx             (new)
```

## Acceptance Criteria

- [ ] `POST /subscription/checkout` returns a valid Stripe checkout session.
- [ ] The Stripe webhook (signature-verified) transitions a user to active and
      sets `current_period_end`.
- [ ] Premium endpoints return `402`/upgrade response for non-subscribers and
      succeed for active subscribers.
- [ ] Security review findings are resolved; rate limiting is active.
- [ ] Playwright smoke test passes against the running stack.
- [ ] `docker-compose.prod.yml` builds and serves the production frontend.
- [ ] `ruff`, `pytest`, frontend `lint` + `build` pass.

## Dependency

- **Sprint 1** (users to attach subscriptions to).
- **Sprint 6** (AI Tutor) and **Sprint 2** (premium courses) as gating targets.
- Builds on **all prior sprints** for the e2e/hardening pass.

## Status — ✅ Complete

Subscriptions with Stripe checkout + signature-verified webhooks; the AI Tutor is
gated behind an active subscription; the stack is hardened for production.

> **Migration numbering:** the plan called this `0007`, but `0007_progress` was
> taken in Sprint 7, so the subscriptions migration is **`0008_subscriptions`**.

**Backend — billing**
- `Subscription` model + migration `0008_subscriptions`; domain entity +
  `SubscriptionRepository` + SQLAlchemy impl (one row per user, upsert).
- `StripeClient` (`infrastructure/billing/stripe_client.py`, lazy `stripe` import):
  create checkout session (with `client_reference_id`), `construct_event`
  (signature verification). Errors → `StripeError` / `StripeNotConfiguredError`.
- `SubscriptionService`: status, `is_active`, `start_checkout`, and
  `handle_webhook` (activate on `checkout.session.completed` /
  `customer.subscription.updated`, cancel on `...deleted`).
- Entitlement dep `require_active_subscription` — no-op when `BILLING_ENABLED`
  is false, else `402` for non-subscribers; gates `POST /ai/tutor`.
- Endpoints: `GET /subscription`, `POST /subscription/checkout`,
  `POST /webhooks/stripe`. Config `STRIPE_*`, `BILLING_ENABLED`, checkout URLs.

**Backend — hardening**
- Optional in-process per-client rate-limit middleware (`RATE_LIMIT_ENABLED`,
  `RATE_LIMIT_PER_MINUTE`; off in dev, on in prod compose).
- CORS already env-driven; consistent `{"detail": …}` error envelopes and auth on
  every protected route (audited); `409` handler for integrity violations.

**Infra**
- `docker-compose.prod.yml`: Nginx-served frontend (`prod` stage), gunicorn +
  uvicorn workers, `AUTH_STUB_ENABLED=false`, billing + rate limiting on,
  Postgres not published. `gunicorn` added to requirements.
- `e2e/` Playwright smoke test (sign in → dashboard → open a course), opt-in.

**Frontend**
- `features/billing/hooks.ts` (`useSubscription`, `useCheckout`); wired
  `Subscription` page (plan/status + Stripe checkout redirect); `UpgradePrompt`
  shown when the AI Tutor returns `402`.

**Tests**
- `tests/test_subscription.py` — checkout, webhook transitions, bad-signature
  `400`, premium gating `402`/`200`. Full suite: `pytest` **66/66** pass.

### Verification

- Backend: `ruff` clean, `pytest` 66/66 (Stripe mocked, no network).
- Frontend: `lint` clean, `build` succeeds.
- `docker compose -f docker-compose.prod.yml config` validates.
- Live (dev Docker stack): migration `0007 → 0008` applied; `/subscription`,
  `/subscription/checkout`, `/webhooks/stripe` registered; `subscriptions` table
  present; protected endpoints require a token (`401`).

### Notes / follow-ups

- **Billing is off by default** (`BILLING_ENABLED=false`) so dev/tests are
  unaffected; enable it with the `STRIPE_*` secrets. Stripe/webhook logic is
  covered by the mocked-provider suite — a real end-to-end charge needs live
  Stripe keys + a webhook tunnel.
- **Security review:** a manual pass was done — webhook signatures verified,
  secrets kept server-side and out of VCS (`.env` gitignored), premium routes
  gated, auth enforced on protected routes, error envelopes consistent. A formal
  scanner run is recommended before a real launch.
- **Playwright e2e** is provided as an opt-in scaffold; it needs a running stack
  and a browser, so it is not part of the default CI (documented in
  [e2e/README.md](../e2e/README.md)).
- The prod frontend build bakes `VITE_*` at build time — pass build args (or
  deploy via Firebase Hosting) to target your real API/Firebase.
