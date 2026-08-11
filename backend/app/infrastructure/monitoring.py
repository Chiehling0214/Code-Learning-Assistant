"""Persistence helpers for lightweight first-party operational monitoring."""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.infrastructure.db.session import SessionLocal
from app.infrastructure.models.models import OperationalEvent

logger = logging.getLogger(__name__)


class OperationalEventRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def record(
        self,
        *,
        category: str,
        level: str,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> OperationalEvent:
        event = OperationalEvent(
            category=category[:40],
            level=level[:16],
            message=message[:2000],
            details=details or {},
        )
        self._session.add(event)
        self._session.flush()
        self._session.refresh(event)
        return event

    def counts_since(self, since: datetime) -> dict[str, int]:
        rows = self._session.execute(
            select(OperationalEvent.category, func.count())
            .where(OperationalEvent.created_at >= since)
            .group_by(OperationalEvent.category)
        ).all()
        return {str(category): int(count) for category, count in rows}

    def list_since(self, since: datetime, *, limit: int = 50) -> list[OperationalEvent]:
        stmt = (
            select(OperationalEvent)
            .where(OperationalEvent.created_at >= since)
            .order_by(OperationalEvent.created_at.desc())
            .limit(max(1, min(200, limit)))
        )
        return list(self._session.scalars(stmt).all())

    def prune(self, *, retention_days: int) -> int:
        cutoff = datetime.now(UTC) - timedelta(days=max(1, retention_days))
        result = self._session.execute(
            delete(OperationalEvent).where(OperationalEvent.created_at < cutoff)
        )
        return int(result.rowcount or 0)


def record_operational_event(
    *,
    category: str,
    level: str,
    message: str,
    details: dict[str, Any] | None = None,
    retention_days: int = 30,
) -> None:
    """Record from middleware or other code without a request-scoped session."""
    session = SessionLocal()
    try:
        repository = OperationalEventRepository(session)
        repository.record(
            category=category,
            level=level,
            message=message,
            details=details,
        )
        repository.prune(retention_days=retention_days)
        session.commit()
    except Exception:  # noqa: BLE001 - monitoring must never break the app
        session.rollback()
        logger.exception("Could not persist operational monitoring event")
    finally:
        session.close()
