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


@dataclass(frozen=True)
class RetrievedSession:
    """The subset of a retrieved Checkout Session we act on."""

    client_reference_id: str | None
    payment_status: str  # "paid" | "unpaid" | "no_payment_required"
    status: str  # "complete" | "open" | "expired"
    customer: str | None = None
    subscription: str | None = None


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
        # Carry the session id back on success so the app can confirm the payment
        # via the API (works without webhooks / the Stripe CLI). Stripe substitutes
        # the {CHECKOUT_SESSION_ID} template into the redirect URL.
        sep = "&" if "?" in self._success_url else "?"
        success_url = f"{self._success_url}{sep}session_id={{CHECKOUT_SESSION_ID}}"
        try:
            session = stripe.checkout.Session.create(
                mode="subscription",
                line_items=[{"price": self._price_id, "quantity": 1}],
                customer_email=customer_email,
                # Lets the webhook / confirm step map the session back to our user.
                client_reference_id=client_reference_id,
                success_url=success_url,
                cancel_url=self._cancel_url,
            )
        except Exception as exc:  # noqa: BLE001 - normalize SDK errors
            logger.warning("Stripe checkout failed: %s", exc)
            raise StripeError(f"Stripe checkout failed: {exc}") from exc
        return CheckoutSession(id=session["id"], url=session["url"])

    def retrieve_checkout_session(self, session_id: str) -> RetrievedSession:
        """Fetch a Checkout Session to confirm a payment (webhook-free path)."""
        stripe = self._sdk()
        try:
            s = stripe.checkout.Session.retrieve(session_id)
        except Exception as exc:  # noqa: BLE001 - normalize SDK errors
            logger.warning("Stripe session retrieve failed: %s", exc)
            raise StripeError(f"Could not retrieve checkout session: {exc}") from exc
        return RetrievedSession(
            client_reference_id=s.get("client_reference_id"),
            payment_status=s.get("payment_status", ""),
            status=s.get("status", ""),
            customer=s.get("customer"),
            subscription=s.get("subscription"),
        )

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
