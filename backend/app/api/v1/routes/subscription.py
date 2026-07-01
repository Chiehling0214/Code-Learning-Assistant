"""Subscription status + Stripe checkout endpoints."""

from fastapi import APIRouter, HTTPException, status

from app.api.deps import CurrentDbUser, SubscriptionServiceDep
from app.infrastructure.billing.stripe_client import StripeNotConfiguredError
from app.schemas.subscription import CheckoutResponse, SubscriptionResponse

router = APIRouter(tags=["subscription"])


@router.get("/subscription", response_model=SubscriptionResponse)
def get_subscription(
    current_user: CurrentDbUser, service: SubscriptionServiceDep
) -> SubscriptionResponse:
    sub = service.get_status(current_user.id)
    if sub is None:
        return SubscriptionResponse(plan="free", status="inactive", active=False)
    return SubscriptionResponse(
        plan=sub.plan,
        status=sub.status,
        active=sub.status == "active",
        current_period_end=sub.current_period_end,
    )


@router.post("/subscription/checkout", response_model=CheckoutResponse)
def start_checkout(
    current_user: CurrentDbUser, service: SubscriptionServiceDep
) -> CheckoutResponse:
    email = current_user.email or f"{current_user.firebase_uid}@unknown.local"
    try:
        url = service.start_checkout(user_id=current_user.id, email=email)
    except StripeNotConfiguredError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Billing is not configured on this server.",
        ) from exc
    return CheckoutResponse(checkout_url=url)
