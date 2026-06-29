"""Versioned health endpoint (includes a database readiness check)."""

from fastapi import APIRouter

from app.api.deps import DbSession
from app.application.services.health_service import HealthService
from app.schemas.health import ReadinessResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=ReadinessResponse)
def health(session: DbSession) -> ReadinessResponse:
    db_ok = HealthService(session).check_database()
    return ReadinessResponse(
        status="ok" if db_ok else "degraded",
        database="ok" if db_ok else "error",
    )
