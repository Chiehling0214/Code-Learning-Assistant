"""Recoverable PostgreSQL-backed curriculum worker."""

from __future__ import annotations

import threading
import uuid
from datetime import UTC, datetime, timedelta

from app.application.services.ai_usage import AIUsageGuard
from app.application.services.curriculum_service import CurriculumService
from app.application.services.execution_service import ExecutionService
from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.infrastructure.ai.gemini_provider import GeminiAIProvider
from app.infrastructure.db.session import SessionLocal
from app.infrastructure.judge0.client import Judge0Client
from app.infrastructure.monitoring import OperationalEventRepository
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
    SqlAlchemyStudentProfileRepository,
)

logger = get_logger(__name__)


def _heartbeat_loop(job_id: uuid.UUID, stop: threading.Event, interval: float) -> None:
    """Renew a running job's lease while a slow Gemini request is in flight."""
    while not stop.wait(interval):
        session = SessionLocal()
        try:
            jobs = SqlAlchemyGenerationJobRepository(session)
            job = jobs.get_by_id(job_id)
            if job is None or job.status != "running":
                return
            jobs.update(job_id, heartbeat_at=datetime.now(UTC))
            session.commit()
        except Exception:  # noqa: BLE001 - generation continues until the stale lease expires
            session.rollback()
            logger.exception("Could not renew heartbeat for generation job %s", job_id)
        finally:
            session.close()


def _service(session, settings: Settings) -> CurriculumService:  # noqa: ANN001
    return CurriculumService(
        GeminiAIProvider(settings),
        SqlAlchemyGenerationJobRepository(session),
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
        SqlAlchemyStudentProfileRepository(session),
    )


def _clean_partial_courses(session, job_id: uuid.UUID) -> None:  # noqa: ANN001
    courses = SqlAlchemyCourseRepository(session)
    for course in courses.list_by_generation_job(job_id):
        courses.delete(course.id)
    SqlAlchemyGenerationJobRepository(session).update(job_id, completed=0)
    session.commit()


def run_generation(job_id: uuid.UUID) -> None:
    settings = get_settings()
    session = SessionLocal()
    jobs = SqlAlchemyGenerationJobRepository(session)
    heartbeat_stop: threading.Event | None = None
    heartbeat_thread: threading.Thread | None = None
    try:
        job = jobs.get_by_id(job_id)
        if job is None or job.status in {"done", "cancelled"}:
            return
        heartbeat_stop = threading.Event()
        heartbeat_interval = max(
            5.0,
            min(60.0, settings.generation_worker_stale_minutes * 60 / 3),
        )
        heartbeat_thread = threading.Thread(
            target=_heartbeat_loop,
            args=(job_id, heartbeat_stop, heartbeat_interval),
            name=f"generation-heartbeat-{job_id}",
            daemon=True,
        )
        heartbeat_thread.start()
        _clean_partial_courses(session, job_id)
        service = _service(session, settings)
        if job.kind == "course_set":
            service.generate_course_set(
                job_id, course_count=job.course_count, commit=session.commit
            )
        else:
            service.generate_course(job_id, commit=session.commit)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Generation job %s failed: %s", job_id, exc)
        session.rollback()
        job = jobs.get_by_id(job_id)
        if job is not None:
            retrying = False
            if job.cancel_requested:
                jobs.update(job_id, status="cancelled", error=str(exc)[:500])
            elif job.attempt_count < job.max_attempts:
                retrying = True
                delay = min(60, 2 ** max(0, job.attempt_count - 1) * 5)
                jobs.update(
                    job_id,
                    status="pending",
                    error=str(exc)[:500],
                    next_attempt_at=datetime.now(UTC) + timedelta(seconds=delay),
                )
            else:
                jobs.update(job_id, status="error", error=str(exc)[:500])
            if settings.monitoring_enabled:
                monitoring = OperationalEventRepository(session)
                event_details = {
                    "job_id": str(job.id),
                    "kind": job.kind,
                    "attempt_count": job.attempt_count,
                    "max_attempts": job.max_attempts,
                }
                monitoring.record(
                    category="ai_generation_failure",
                    level="error",
                    message=str(exc),
                    details=event_details,
                )
                if retrying:
                    monitoring.record(
                        category="worker_retry",
                        level="warning",
                        message=f"Generation job scheduled for retry in {delay} seconds",
                        details={**event_details, "retry_delay_seconds": delay},
                    )
                monitoring.prune(retention_days=settings.monitoring_retention_days)
            session.commit()
    finally:
        if heartbeat_stop is not None:
            heartbeat_stop.set()
        if heartbeat_thread is not None:
            heartbeat_thread.join(timeout=2)
        session.close()


def run_course_set_generation(job_id: uuid.UUID, course_count: int = 3) -> None:
    session = SessionLocal()
    try:
        job = SqlAlchemyGenerationJobRepository(session).get_by_id(job_id)
        if job and job.course_count != course_count:
            logger.info("Using persisted course count %d for %s", job.course_count, job_id)
    finally:
        session.close()
    run_generation(job_id)


def run_worker_loop(stop: threading.Event, settings: Settings) -> None:
    """Poll and run persisted jobs until ``stop`` is set."""
    while not stop.is_set():
        session = SessionLocal()
        try:
            jobs = SqlAlchemyGenerationJobRepository(session)
            recovered = jobs.recover_stale(minutes=settings.generation_worker_stale_minutes)
            job = jobs.claim_next()
            session.commit()
            if recovered:
                logger.warning("Recovered %d stale generation job(s)", recovered)
        except Exception:  # noqa: BLE001
            session.rollback()
            logger.exception("Generation worker poll failed")
            job = None
        finally:
            session.close()
        if job is not None:
            run_generation(job.id)
            continue
        stop.wait(max(0.25, settings.generation_worker_poll_seconds))


def start_generation_worker(settings: Settings) -> tuple[threading.Event, threading.Thread]:
    stop = threading.Event()
    thread = threading.Thread(
        target=run_worker_loop,
        args=(stop, settings),
        name="generation-worker",
        daemon=True,
    )
    thread.start()
    return stop, thread
