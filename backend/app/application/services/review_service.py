"""Spaced review of mistakes (Sprint 15).

Every miss — a wrong quiz/placement answer or a failed exercise — is captured as
a :class:`ReviewItem` with a snapshot payload, and scheduled with a simple
spaced-repetition rule:

* captured (or answered wrong) → due again in 1 day, ``passes`` reset;
* answered correctly → interval doubles (1 → 2 → 4 days);
* three consecutive passes → the item is **retired** (mastered).

Capture is best-effort: it must never break grading, so callers wrap it via
:meth:`capture_miss` which swallows nothing — but writes are simple upserts on
``(user_id, item_ref)``.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from app.domain.entities import ReviewItem
from app.domain.repositories import ReviewItemRepository

_START_INTERVAL_DAYS = 1
_PASSES_TO_RETIRE = 3


def _now() -> datetime:
    return datetime.now(UTC)


class ReviewService:
    def __init__(self, items: ReviewItemRepository) -> None:
        self._items = items

    # ----- capture (called from grading paths) -----

    def capture_miss(
        self,
        *,
        user_id: uuid.UUID,
        source: str,
        item_ref: uuid.UUID,
        payload: dict[str, Any],
    ) -> ReviewItem:
        """Record a miss: create the item, or lapse-reset an existing one."""
        due = _now() + timedelta(days=_START_INTERVAL_DAYS)
        existing = self._items.get_by_user_and_ref(user_id, item_ref)
        if existing is None:
            return self._items.create(
                user_id=user_id,
                source=source,
                item_ref=item_ref,
                payload=payload,
                interval_days=_START_INTERVAL_DAYS,
                due_at=due,
            )
        return self._items.update(
            existing.id,
            payload=payload,  # refresh the snapshot
            interval_days=_START_INTERVAL_DAYS,
            due_at=due,
            lapses=existing.lapses + 1,
            passes=0,
            retired=False,
        )

    def record_pass(self, *, user_id: uuid.UUID, item_ref: uuid.UUID) -> ReviewItem | None:
        """Apply a pass to an active item, if one exists (e.g. an exercise later
        solved outside the review flow). Returns the updated item or None."""
        existing = self._items.get_by_user_and_ref(user_id, item_ref)
        if existing is None or existing.retired:
            return None
        return self._apply_pass(existing)

    # ----- the review flow -----

    def list_due(self, user_id: uuid.UUID) -> list[ReviewItem]:
        return self._items.list_due(user_id, _now())

    def due_count(self, user_id: uuid.UUID) -> int:
        return self._items.count_due(user_id, _now())

    def notebook(self, user_id: uuid.UUID) -> list[ReviewItem]:
        return self._items.list_all(user_id)

    def answer(self, *, user_id: uuid.UUID, item_id: uuid.UUID, correct: bool) -> ReviewItem:
        item = self._items.get_by_id(item_id)
        if item is None or item.user_id != user_id:
            raise LookupError("Review item not found")
        if correct:
            return self._apply_pass(item)
        return self._items.update(
            item.id,
            interval_days=_START_INTERVAL_DAYS,
            due_at=_now() + timedelta(days=_START_INTERVAL_DAYS),
            lapses=item.lapses + 1,
            passes=0,
        )

    def _apply_pass(self, item: ReviewItem) -> ReviewItem:
        passes = item.passes + 1
        if passes >= _PASSES_TO_RETIRE:
            return self._items.update(item.id, passes=passes, retired=True)
        interval = item.interval_days * 2
        return self._items.update(
            item.id,
            passes=passes,
            interval_days=interval,
            due_at=_now() + timedelta(days=interval),
        )
