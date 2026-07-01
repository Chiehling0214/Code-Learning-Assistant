"""Stripe client wrapper.

Uses the ``stripe`` SDK, imported lazily so the app (and the test suite, which
mocks this client) does not require the SDK or API keys. All Stripe access flows
through this class so the billing service stays provider-agnostic and testable.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.core.config import Settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class StripeError(RuntimeError):
    """Base error for Stripe failures (incl. bad webhook signatures)."""


class StripeNotConfiguredError(StripeError):
    """Raised when Stripe is used without an API key configured."""


@dataclass(frozen=True)
class CheckoutSession:
    id: str
    url: str


class StripeClient:
    def __init__(self, settings: Settings) -> None:
        self._api_key = settings.stripe_api_key
        self._webhook_secret = settings.stripe_webhook_secret
        self._price_id = settings.stripe_price_id
        self._success_url = settings.checkout_success_url
        self._cancel_url = settings.checkout_cancel_url

    def _sdk(self):
        if not self._api_key:
            raise StripeNotConfiguredError("Stripe API key is not configured")
        try:
            import stripe
        except ImportError as exc:  # pragma: no cover - dependency missing
            raise StripeError("stripe is not installed") from exc
        stripe.api_key = self._api_key
        return stripe

    def create_checkout_session(
        self, *, customer_email: str, client_reference_id: str
    ) -> CheckoutSession:
        stripe = self._sdk()
        if not self._price_id:
            raise StripeNotConfiguredError("STRIPE_PRICE_ID is not configured")
        try:
            session = stripe.checkout.Session.create(
                mode="subscription",
                line_items=[{"price": self._price_id, "quantity": 1}],
                customer_email=customer_email,
                # Lets the webhook map the Stripe session back to our user.
                client_reference_id=client_reference_id,
                success_url=self._success_url,
                cancel_url=self._cancel_url,
            )
        except Exception as exc:  # noqa: BLE001 - normalize SDK errors
            logger.warning("Stripe checkout failed: %s", exc)
            raise StripeError(f"Stripe checkout failed: {exc}") from exc
        return CheckoutSession(id=session["id"], url=session["url"])

    def construct_event(self, payload: bytes, signature: str) -> dict:
        """Verify the webhook signature and return the parsed event."""
        stripe = self._sdk()
        if not self._webhook_secret:
            raise StripeNotConfiguredError("STRIPE_WEBHOOK_SECRET is not configured")
        try:
            event = stripe.Webhook.construct_event(payload, signature, self._webhook_secret)
        except Exception as exc:  # noqa: BLE001 - invalid signature / payload
            logger.warning("Stripe webhook verification failed: %s", exc)
            raise StripeError("Invalid webhook signature") from exc
        return dict(event)
