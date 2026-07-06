"""Database bootstrap: ensure canonical rows exist (run after migrations).

Invoked by the container entrypoint (``python -m app.infrastructure.db.bootstrap``)
so a deploy always has the selectable languages without a manual seed step.
"""

from __future__ import annotations

from app.core.config import get_settings
from app.core.languages import ensure_languages
from app.core.logging import configure_logging, get_logger
from app.infrastructure.db.session import SessionLocal
from app.infrastructure.repositories.sqlalchemy_repositories import (
    SqlAlchemyLanguageRepository,
)

logger = get_logger(__name__)


def run() -> None:
    session = SessionLocal()
    try:
        created = ensure_languages(SqlAlchemyLanguageRepository(session))
        session.commit()
        if created:
            logger.info("Bootstrapped languages: %s", ", ".join(created))
        else:
            logger.info("Languages already up to date")
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    configure_logging(get_settings().log_level)
    run()
