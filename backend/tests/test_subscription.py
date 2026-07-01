"""API + service tests for subscriptions/billing (Stripe mocked, no network)."""

import time
import uuid
from types import SimpleNamespace

from app.application.services.subscription_service import SubscriptionService
from app.core.config import Settings, get_settings
from app.main import app
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


# ----- premium gating (API, billing enabled) -----


def test_premium_endpoint_gated_by_subscription(
    client: TestClient, fakes: SimpleNamespace
) -> None:
    # Turn billing on for this test only.
    app.dependency_overrides[get_settings] = lambda: Settings(billing_enabled=True)
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

    # No subscription -> 402 Payment Required.
    denied = client.post("/api/v1/ai/tutor", json=payload)
    assert denied.status_code == 402

    # Activate a subscription for the (now provisioned) user, then retry.
    user_id = next(iter(fakes.users._by_id.values())).id
    fakes.subscriptions.upsert(user_id=user_id, plan="pro", status="active")
    allowed = client.post("/api/v1/ai/tutor", json=payload)
    assert allowed.status_code == 200, allowed.text
