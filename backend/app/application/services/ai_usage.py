"""Per-user AI usage guard: free-tier rate limiting + usage logging.

Counts recorded :class:`AIInteraction` rows in rolling windows to keep within
the Gemini free-tier limits, and records each successful call (with token usage)
for observability.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from app.core.config import Settings
from app.domain.repositories import AIInteractionRepository


class RateLimitError(RuntimeError):
    """Raised when a user exceeds their per-minute or daily AI budget."""


class AIUsageGuard:
    def __init__(self, interactions: AIInteractionRepository, settings: Settings) -> None:
        self._interactions = interactions
        self._per_minute = settings.ai_rate_limit_per_minute
        self._per_day = settings.ai_daily_limit

    def check(self, user_id: uuid.UUID) -> None:
        """Raise :class:`RateLimitError` if the user is over budget."""
        now = datetime.now(UTC)
        if self._interactions.count_since(user_id, now - timedelta(minutes=1)) >= self._per_minute:
            raise RateLimitError("Too many AI requests; please wait a minute.")
        if self._interactions.count_since(user_id, now - timedelta(days=1)) >= self._per_day:
            raise RateLimitError("Daily AI limit reached; try again tomorrow.")

    def record(self, user_id: uuid.UUID, *, kind: str, model: str, total_tokens: int) -> None:
        self._interactions.create(
            user_id=user_id, kind=kind, model=model, total_tokens=total_tokens
        )
