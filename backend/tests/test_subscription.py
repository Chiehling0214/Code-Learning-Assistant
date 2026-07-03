"""API + service tests for subscriptions/billing (Stripe mocked, no network)."""

import time
import uuid
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

from app.application.services.subscription_service import SubscriptionService
from app.domain.entities import AIInteraction
from fastapi.testclient import TestClient

from tests.fakes import FakeStripeClient, FakeSubscriptionRepository

# ----- status & checkout (API) -----


def test_get_subscription_defaults_to_free(client: TestClient) -> None:
    res = client.get("/api/v1/subscription")
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["plan"] == "free"
    assert body["active"] is False


def test_checkout_returns_stripe_url(client: TestClient, fakes: SimpleNamespace) -> None:
    res = client.post("/api/v1/subscription/checkout")
    assert res.status_code == 200, res.text
    assert res.json()["checkout_url"] == fakes.stripe.checkout_url
    # The user id was attached so the webhook can map the session back.
    assert fakes.stripe.last_client_reference_id is not None


def test_webhook_bad_signature_returns_400(client: TestClient, fakes: SimpleNamespace) -> None:
    fakes.stripe.raise_on_construct = True
    res = client.post(
        "/api/v1/webhooks/stripe", content=b"{}", headers={"Stripe-Signature": "bad"}
    )
    assert res.status_code == 400


# ----- webhook state transitions (service level) -----


def test_webhook_activates_subscription() -> None:
    subs = FakeSubscriptionRepository()
    stripe = FakeStripeClient()
    service = SubscriptionService(subs, stripe)
    user_id = uuid.uuid4()
    period_end = int(time.time()) + 30 * 24 * 3600

    stripe.next_event = {
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "client_reference_id": str(user_id),
                "customer": "cus_1",
                "subscription": "sub_1",
                "current_period_end": period_end,
                "status": "active",
            }
        },
    }
    result = service.handle_webhook(payload=b"{}", signature="sig")
    assert result["handled"] is True
    assert service.is_active(user_id) is True
    status = service.get_status(user_id)
    assert status.plan == "pro"
    assert status.current_period_end is not None


def test_webhook_cancel_deactivates() -> None:
    subs = FakeSubscriptionRepository()
    stripe = FakeStripeClient()
    service = SubscriptionService(subs, stripe)
    user_id = uuid.uuid4()
    subs.upsert(user_id=user_id, plan="pro", status="active")

    stripe.next_event = {
        "type": "customer.subscription.deleted",
        "data": {"object": {"client_reference_id": str(user_id)}},
    }
    service.handle_webhook(payload=b"{}", signature="sig")
    assert service.is_active(user_id) is False


# ----- webhook-free checkout confirmation -----


def test_confirm_checkout_activates(client: TestClient, fakes: SimpleNamespace) -> None:
    # Checkout records this user as the session's client_reference_id.
    assert client.post("/api/v1/subscription/checkout").status_code == 200
    res = client.post("/api/v1/subscription/confirm", json={"session_id": "cs_test_123"})
    assert res.status_code == 200, res.text
    assert res.json()["active"] is True
    assert client.get("/api/v1/subscription").json()["active"] is True


def test_confirm_checkout_rejects_unpaid(client: TestClient, fakes: SimpleNamespace) -> None:
    client.post("/api/v1/subscription/checkout")
    fakes.stripe.retrieve_payment_status = "unpaid"
    fakes.stripe.retrieve_status = "open"
    res = client.post("/api/v1/subscription/confirm", json={"session_id": "cs_test_123"})
    assert res.status_code == 400


def test_confirm_checkout_rejects_other_users_session(
    client: TestClient, fakes: SimpleNamespace
) -> None:
    client.post("/api/v1/subscription/checkout")
    # The retrieved session belongs to someone else.
    fakes.stripe.retrieve_client_reference_id = str(uuid.uuid4())
    res = client.post("/api/v1/subscription/confirm", json={"session_id": "cs_test_123"})
    assert res.status_code == 403


# ----- plan-aware AI Tutor cap (Sprint 13) -----


def test_tutor_daily_cap_prompts_upgrade(client: TestClient, fakes: SimpleNamespace) -> None:
    # Provision the current (stub) user so we can seed usage for them.
    user = fakes.users.create(firebase_uid="stub-uid", email="dev@codepath.local")
    exercise = fakes.exercises.create(
        lesson_id=uuid.uuid4(),
        language="python",
        title="Sum",
        slug="sum",
        prompt="Add",
        starter_code="",
        test_spec={},
    )
    payload = {"exercise_id": str(exercise.id), "code": "x = 1"}

    # Exhaust the free tutor daily cap (5) → next call is 402 (upgrade prompt).
    # Backdate the seeded usage so it counts toward the daily cap but not the
    # per-minute burst guard (which would otherwise mask the 402 with a 429).
    earlier = datetime.now(UTC) - timedelta(minutes=5)
    for _ in range(5):
        fakes.interactions._items.append(
            AIInteraction(
                id=uuid.uuid4(),
                user_id=user.id,
                kind="tutor",
                model="m",
                total_tokens=1,
                created_at=earlier,
            )
        )
    denied = client.post("/api/v1/ai/tutor", json=payload)
    assert denied.status_code == 402, denied.text

    # Upgrading raises the cap, so the same call now succeeds.
    fakes.subscriptions.upsert(user_id=user.id, plan="pro", status="active")
    allowed = client.post("/api/v1/ai/tutor", json=payload)
    assert allowed.status_code == 200, allowed.text
