"""Database engine and session factory."""

from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings

settings = get_settings()

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    future=True,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_session() -> Iterator[Session]:
    """Yield a database session, ensuring it is closed afterwards.

    Used as a FastAPI dependency (see ``app/api/deps.py``).
    """
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
