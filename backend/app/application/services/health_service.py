"""Health-check use case.

Lives in the application layer: it orchestrates an infrastructure concern (the
database connection) without the API layer needing to know the details.
"""

from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.logging import get_logger

logger = get_logger(__name__)


class HealthService:
    def __init__(self, session: Session) -> None:
        self._session = session

    def check_database(self) -> bool:
        """Return ``True`` if a trivial query against the database succeeds."""
        try:
            self._session.execute(text("SELECT 1"))
            return True
        except Exception as exc:  # noqa: BLE001 - report any failure as unhealthy
            logger.warning("Database health check failed: %s", exc)
            return False
