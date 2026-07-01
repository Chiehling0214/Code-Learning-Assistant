"""Stripe webhook receiver (signature-verified, unauthenticated)."""

from fastapi import APIRouter, HTTPException, Request, status

from app.api.deps import SubscriptionServiceDep
from app.infrastructure.billing.stripe_client import StripeError
from app.schemas.subscription import WebhookAck

router = APIRouter(tags=["webhooks"])


@router.post("/webhooks/stripe", response_model=WebhookAck)
async def stripe_webhook(
    request: Request, service: SubscriptionServiceDep
) -> WebhookAck:
    payload = await request.body()
    signature = request.headers.get("Stripe-Signature", "")
    try:
        result = service.handle_webhook(payload=payload, signature=signature)
    except StripeError as exc:
        # Bad signature or unverifiable payload -> reject.
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return WebhookAck(received=True, handled=bool(result.get("handled")))
