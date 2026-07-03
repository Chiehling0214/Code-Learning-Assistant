"""Plan entitlements (Sprint 13).

Central source of truth for free-vs-paid limits and current usage. The plan is
derived from the Sprint 8 subscription (``is_active`` → paid). Limits are
config-driven; usage is counted from tracks and the AI-interaction log. Callers
enforce a limit via :meth:`check_tutor` / :meth:`check_generation`, which raise
:class:`UpgradeRequiredError` (mapped to HTTP 402) when the plan cap is hit.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from app.application.services.subscription_service import SubscriptionService
from app.core.config import Settings
from app.domain.repositories import AIInteractionRepository, LanguageTrackRepository


class UpgradeRequiredError(RuntimeError):
    """Raised when a free-plan limit is reached and an upgrade is required."""


@dataclass(frozen=True)
class Entitlements:
    plan: str  # "free" | "pro"
    max_languages: int
    tutor_daily: int
    generations_daily: int
    languages_used: int
    tutor_used_today: int
    generations_used_today: int


class EntitlementService:
    def __init__(
        self,
        subscriptions: SubscriptionService,
        tracks: LanguageTrackRepository,
        interactions: AIInteractionRepository,
        settings: Settings,
    ) -> None:
        self._subs = subscriptions
        self._tracks = tracks
        self._interactions = interactions
        self._settings = settings

    # ----- plan + limits -----

    def is_paid(self, user_id: uuid.UUID) -> bool:
        return self._subs.is_active(user_id)

    def plan(self, user_id: uuid.UUID) -> str:
        return "pro" if self.is_paid(user_id) else "free"

    def max_languages(self, user_id: uuid.UUID) -> int:
        s = self._settings
        return s.paid_max_languages if self.is_paid(user_id) else s.free_max_languages

    def tutor_daily(self, user_id: uuid.UUID) -> int:
        s = self._settings
        return s.paid_tutor_daily if self.is_paid(user_id) else s.free_tutor_daily

    def generations_daily(self, user_id: uuid.UUID) -> int:
        s = self._settings
        return s.paid_generations_daily if self.is_paid(user_id) else s.free_generations_daily

    # ----- usage -----

    def _used_today(self, user_id: uuid.UUID, kind: str) -> int:
        since = datetime.now(UTC) - timedelta(days=1)
        return self._interactions.count_since(user_id, since, kind=kind)

    # ----- enforcement -----

    def check_tutor(self, user_id: uuid.UUID) -> None:
        if self._used_today(user_id, "tutor") >= self.tutor_daily(user_id):
            raise UpgradeRequiredError(
                "You've reached today's AI Tutor limit for your plan. Upgrade for more."
            )

    def check_generation(self, user_id: uuid.UUID) -> None:
        if self._used_today(user_id, "generate") >= self.generations_daily(user_id):
            raise UpgradeRequiredError(
                "You've reached today's content-generation limit for your plan. "
                "Upgrade for more."
            )

    # ----- snapshot (for GET /me/entitlements) -----

    def snapshot(self, user_id: uuid.UUID) -> Entitlements:
        return Entitlements(
            plan=self.plan(user_id),
            max_languages=self.max_languages(user_id),
            tutor_daily=self.tutor_daily(user_id),
            generations_daily=self.generations_daily(user_id),
            languages_used=self._tracks.count_by_user(user_id),
            tutor_used_today=self._used_today(user_id, "tutor"),
            generations_used_today=self._used_today(user_id, "generate"),
        )
