"""FastAPI application factory and entry point."""

from __future__ import annotations

import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from starlette.concurrency import run_in_threadpool

from app import __version__
from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.infrastructure.generation_worker import start_generation_worker
from app.infrastructure.monitoring import record_operational_event
from app.infrastructure.rate_limit import SharedRateLimiter
from app.schemas.health import LivenessResponse

settings = get_settings()
configure_logging(settings.log_level)
logger = get_logger(__name__)


def create_app() -> FastAPI:
    app = FastAPI(
        title="Code Learning Assistant API",
        version=__version__,
        description="Backend API for the Code Learning Assistant platform.",
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

    @app.middleware("http")
    async def monitor_server_errors(request: Request, call_next):
        response = await call_next(request)
        if settings.monitoring_enabled and response.status_code >= 500:
            details = {
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "request_id": response.headers.get("X-Request-ID", ""),
            }
            await run_in_threadpool(
                record_operational_event,
                category="api_5xx",
                level="error",
                message=f"{request.method} {request.url.path} returned {response.status_code}",
                details=details,
                retention_days=settings.monitoring_retention_days,
            )
            if request.url.path.endswith("/regenerate") or request.url.path.endswith(
                "/adjustments/preview"
            ):
                await run_in_threadpool(
                    record_operational_event,
                    category="ai_generation_failure",
                    level="error",
                    message="AI content generation failed",
                    details=details,
                    retention_days=settings.monitoring_retention_days,
                )
        return response

    if settings.rate_limit_enabled:
        limiter = SharedRateLimiter(
            limit=settings.rate_limit_per_minute,
            redis_url=settings.redis_url,
        )
        app.state.rate_limiter = limiter

        @app.middleware("http")
        async def rate_limit(request: Request, call_next):
            client = request.client.host if request.client else "unknown"
            if not await limiter.allow(client):
                return JSONResponse(
                    status_code=429, content={"detail": "Rate limit exceeded; slow down."}
                )
            return await call_next(request)

        @app.on_event("shutdown")
        async def close_rate_limiter() -> None:
            await limiter.close()

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
        if settings.monitoring_enabled:
            await run_in_threadpool(
                record_operational_event,
                category="api_5xx",
                level="error",
                message=f"Unhandled {type(exc).__name__}: {str(exc)[:1500]}",
                details={
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": 500,
                    "request_id": request.headers.get("X-Request-ID", ""),
                },
                retention_days=settings.monitoring_retention_days,
            )
        return JSONResponse(status_code=500, content={"detail": "Internal server error"})

    @app.get("/health", response_model=LivenessResponse, tags=["health"])
    def liveness() -> LivenessResponse:
        return LivenessResponse(service=settings.app_name, version=__version__)

    app.include_router(api_router, prefix=settings.api_v1_prefix)

    if settings.generation_worker_enabled:

        @app.on_event("startup")
        def start_worker() -> None:
            app.state.generation_worker = start_generation_worker(settings)

        @app.on_event("shutdown")
        def stop_worker() -> None:
            stop, thread = app.state.generation_worker
            stop.set()
            thread.join(timeout=5)

    logger.info("Application initialized (environment=%s)", settings.environment)
    return app


app = create_app()
