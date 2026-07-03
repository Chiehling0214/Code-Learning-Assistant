"""Subscription status + Stripe checkout endpoints."""

from fastapi import APIRouter, HTTPException, status

from app.api.deps import CurrentDbUser, SubscriptionServiceDep
from app.infrastructure.billing.stripe_client import StripeError, StripeNotConfiguredError
from app.schemas.subscription import (
    CheckoutResponse,
    ConfirmRequest,
    SubscriptionResponse,
)

router = APIRouter(tags=["subscription"])


def _sub_response(sub) -> SubscriptionResponse:  # noqa: ANN001 - domain entity
    return SubscriptionResponse(
        plan=sub.plan,
        status=sub.status,
        active=sub.status == "active",
        current_period_end=sub.current_period_end,
    )


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


@router.post("/subscription/confirm", response_model=SubscriptionResponse)
def confirm_checkout(
    body: ConfirmRequest, current_user: CurrentDbUser, service: SubscriptionServiceDep
) -> SubscriptionResponse:
    """Activate the plan from a completed Checkout Session (webhook-free)."""
    try:
        sub = service.confirm_checkout(session_id=body.session_id, user_id=current_user.id)
    except StripeNotConfiguredError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Billing is not configured on this server.",
        ) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except StripeError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)
        ) from exc
    return _sub_response(sub)
