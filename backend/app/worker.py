"""Dedicated entry point for recoverable curriculum generation jobs."""

from __future__ import annotations

import signal
import threading

from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.infrastructure.generation_worker import run_worker_loop


def main() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    logger = get_logger(__name__)
    stop = threading.Event()

    def request_stop(signum: int, _frame: object) -> None:
        logger.info("Generation worker received signal %s; stopping", signum)
        stop.set()

    signal.signal(signal.SIGINT, request_stop)
    signal.signal(signal.SIGTERM, request_stop)
    logger.info("Dedicated generation worker started")
    run_worker_loop(stop, settings)
    logger.info("Dedicated generation worker stopped")


if __name__ == "__main__":
    main()
