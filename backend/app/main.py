"""FastAPI application factory and entry point."""

from __future__ import annotations

import time
import uuid
from collections import defaultdict, deque

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

from app import __version__
from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.schemas.health import LivenessResponse

settings = get_settings()
configure_logging(settings.log_level)
logger = get_logger(__name__)


def create_app() -> FastAPI:
    app = FastAPI(
        title="CodePath AI API",
        version=__version__,
        description="Backend API for the CodePath AI learning platform.",
        openapi_url=f"{settings.api_v1_prefix}/openapi.json",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def add_request_id(request: Request, call_next):
        """Attach a request id for traceable structured logs."""
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

    if settings.rate_limit_enabled:
        # Lightweight in-process per-client rate limit (production hardening).
        # For multi-instance deployments, front with a shared limiter (e.g. Redis).
        hits: dict[str, deque[float]] = defaultdict(deque)
        limit = settings.rate_limit_per_minute

        @app.middleware("http")
        async def rate_limit(request: Request, call_next):
            client = request.client.host if request.client else "unknown"
            now = time.monotonic()
            window = hits[client]
            while window and now - window[0] > 60:
                window.popleft()
            if len(window) >= limit:
                return JSONResponse(
                    status_code=429, content={"detail": "Rate limit exceeded; slow down."}
                )
            window.append(now)
            return await call_next(request)

    @app.exception_handler(IntegrityError)
    async def integrity_error_handler(request: Request, exc: IntegrityError):
        # e.g. a duplicate slug or unique-constraint violation on a write.
        logger.warning("Integrity error on %s %s", request.method, request.url.path)
        return JSONResponse(
            status_code=409,
            content={"detail": "Resource conflict (duplicate or constraint violation)"},
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        logger.exception("Unhandled error processing %s %s", request.method, request.url.path)
        return JSONResponse(status_code=500, content={"detail": "Internal server error"})

    @app.get("/health", response_model=LivenessResponse, tags=["health"])
    def liveness() -> LivenessResponse:
        return LivenessResponse(service=settings.app_name, version=__version__)

    app.include_router(api_router, prefix=settings.api_v1_prefix)

    logger.info("Application initialized (environment=%s)", settings.environment)
    return app


app = create_app()
