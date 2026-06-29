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
