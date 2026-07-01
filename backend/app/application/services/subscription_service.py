"""Subscription / billing use cases.

Orchestrates the subscription repository and the Stripe client. Checkout returns
a hosted Stripe session URL; the (signature-verified) webhook drives all state
transitions — the app never trusts the client to say it paid.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from app.domain.entities import Subscription
from app.domain.repositories import SubscriptionRepository
from app.infrastructure.billing.stripe_client import StripeClient

_ACTIVE_STRIPE_STATES = {"active", "trialing", "complete", "paid"}


def _to_datetime(value: object) -> datetime | None:
    """Convert a Stripe unix timestamp (seconds) to an aware datetime."""
    if isinstance(value, int | float):
        return datetime.fromtimestamp(value, tz=UTC)
    return None


class SubscriptionService:
    def __init__(self, subscriptions: SubscriptionRepository, stripe: StripeClient) -> None:
        self._subs = subscriptions
        self._stripe = stripe

    def get_status(self, user_id: uuid.UUID) -> Subscription | None:
        return self._subs.get_by_user_id(user_id)

    def is_active(self, user_id: uuid.UUID) -> bool:
        sub = self._subs.get_by_user_id(user_id)
        return sub is not None and sub.status == "active"

    def start_checkout(self, *, user_id: uuid.UUID, email: str) -> str:
        session = self._stripe.create_checkout_session(
            customer_email=email, client_reference_id=str(user_id)
        )
        return session.url

    def handle_webhook(self, *, payload: bytes, signature: str) -> dict:
        """Verify and apply a Stripe webhook event; returns a small ack dict."""
        event = self._stripe.construct_event(payload, signature)
        event_type = event.get("type", "")
        obj = (event.get("data") or {}).get("object") or {}

        raw_user = obj.get("client_reference_id") or (obj.get("metadata") or {}).get("user_id")
        if not raw_user:
            return {"handled": False}
        try:
            user_id = uuid.UUID(str(raw_user))
        except ValueError:
            return {"handled": False}

        period_end = _to_datetime(obj.get("current_period_end"))

        if event_type in ("checkout.session.completed", "customer.subscription.updated"):
            stripe_status = obj.get("status", "active")
            status = "active" if stripe_status in _ACTIVE_STRIPE_STATES else stripe_status
            self._subs.upsert(
                user_id=user_id,
                plan="pro",
                status=status,
                stripe_customer_id=obj.get("customer"),
                stripe_subscription_id=obj.get("subscription") or obj.get("id"),
                current_period_end=period_end,
            )
            return {"handled": True}

        if event_type in ("customer.subscription.deleted",):
            self._subs.upsert(
                user_id=user_id, plan="free", status="canceled", current_period_end=period_end
            )
            return {"handled": True}

        return {"handled": False}
