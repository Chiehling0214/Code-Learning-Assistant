"""Background worker for AI curriculum generation.

Runs after the HTTP response (FastAPI ``BackgroundTasks``): opens its own
session, builds a :class:`CurriculumService` with real dependencies, and runs the
generation, committing after each lesson so ``GET …/generation`` shows progress.
"""

from __future__ import annotations

import uuid

from app.application.services.ai_usage import AIUsageGuard
from app.application.services.curriculum_service import CurriculumService
from app.application.services.execution_service import ExecutionService
from app.core.config import get_settings
from app.core.logging import get_logger
from app.infrastructure.ai.gemini_provider import GeminiAIProvider
from app.infrastructure.db.session import SessionLocal
from app.infrastructure.judge0.client import Judge0Client
from app.infrastructure.repositories.sqlalchemy_repositories import (
    SqlAlchemyAIInteractionRepository,
    SqlAlchemyCourseRepository,
    SqlAlchemyExerciseRepository,
    SqlAlchemyGenerationJobRepository,
    SqlAlchemyLanguageRepository,
    SqlAlchemyLanguageTrackRepository,
    SqlAlchemyLessonRepository,
    SqlAlchemyProgressRepository,
    SqlAlchemyQuizRepository,
)

logger = get_logger(__name__)


def run_generation(job_id: uuid.UUID) -> None:
    """Generate a course for a job, persisting progress as it goes."""
    settings = get_settings()
    session = SessionLocal()
    jobs = SqlAlchemyGenerationJobRepository(session)
    try:
        service = CurriculumService(
            GeminiAIProvider(settings),
            jobs,
            SqlAlchemyCourseRepository(session),
            SqlAlchemyLessonRepository(session),
            SqlAlchemyExerciseRepository(session),
            SqlAlchemyQuizRepository(session),
            SqlAlchemyLanguageRepository(session),
            SqlAlchemyLanguageTrackRepository(session),
            ExecutionService(Judge0Client(settings)),
            AIUsageGuard(SqlAlchemyAIInteractionRepository(session), settings),
            settings,
            SqlAlchemyProgressRepository(session),
        )
        service.generate_course(job_id, commit=session.commit)
    except Exception as exc:  # noqa: BLE001 - never let the background task crash
        logger.exception("Generation worker failed for job %s: %s", job_id, exc)
        session.rollback()
        try:
            jobs.update(job_id, status="error", error="Generation failed")
            session.commit()
        except Exception:  # noqa: BLE001
            session.rollback()
    finally:
        session.close()
