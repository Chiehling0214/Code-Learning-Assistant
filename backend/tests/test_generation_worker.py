"""Concurrency safeguards for the PostgreSQL-backed generation workers."""

from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

from app.infrastructure import generation_worker
from app.infrastructure.repositories.sqlalchemy_repositories import (
    SqlAlchemyGenerationJobRepository,
)


def test_stale_recovery_skips_rows_locked_by_another_worker() -> None:
    session = MagicMock()
    session.scalars.return_value.all.return_value = []

    recovered = SqlAlchemyGenerationJobRepository(session).recover_stale()

    statement = session.scalars.call_args.args[0]
    assert recovered == 0
    assert statement._for_update_arg is not None  # noqa: SLF001
    assert statement._for_update_arg.skip_locked is True  # noqa: SLF001


def test_heartbeat_renews_a_running_job(monkeypatch) -> None:  # noqa: ANN001
    job_id = uuid4()
    session = MagicMock()
    repository = MagicMock()
    repository.get_by_id.return_value = SimpleNamespace(status="running")
    waits = iter([False, True])
    stop = MagicMock()
    stop.wait.side_effect = lambda _interval: next(waits)
    monkeypatch.setattr(generation_worker, "SessionLocal", lambda: session)
    monkeypatch.setattr(
        generation_worker,
        "SqlAlchemyGenerationJobRepository",
        lambda _session: repository,
    )

    generation_worker._heartbeat_loop(job_id, stop, interval=0)

    repository.update.assert_called_once()
    assert repository.update.call_args.args == (job_id,)
    assert "heartbeat_at" in repository.update.call_args.kwargs
    session.commit.assert_called_once()
    session.close.assert_called_once()
