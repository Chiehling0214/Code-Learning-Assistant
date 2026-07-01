"""Pydantic schemas for subscriptions/billing."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class SubscriptionResponse(BaseModel):
    plan: str
    status: str  # "inactive" | "active" | "canceled"
    active: bool
    current_period_end: datetime | None = None


class CheckoutResponse(BaseModel):
    checkout_url: str


class WebhookAck(BaseModel):
    received: bool = True
    handled: bool = False
