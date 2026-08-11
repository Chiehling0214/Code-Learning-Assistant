from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, Query, Request, Response, status

from app.api.deps import DbSession, SettingsDep, require_admin
from app.infrastructure.monitoring import OperationalEventRepository
from app.schemas.monitoring import (
    FrontendErrorCreate,
    MonitoringSummaryResponse,
    OperationalEventResponse,
)

router = APIRouter(prefix="/monitoring", tags=["monitoring"])
admin_router = APIRouter(
    prefix="/admin/monitoring",
    tags=["admin"],
    dependencies=[Depends(require_admin)],
)


@router.post(
    "/frontend-errors",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
def record_frontend_error(
    body: FrontendErrorCreate,
    request: Request,
    session: DbSession,
    settings: SettingsDep,
) -> Response:
    if not settings.monitoring_enabled:
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    repository = OperationalEventRepository(session)
    repository.record(
        category=body.kind,
        level="error",
        message=body.message,
        details={
            "stack": body.stack,
            "path": body.path,
            "user_agent": request.headers.get("user-agent", "")[:500],
        },
    )
    repository.prune(retention_days=settings.monitoring_retention_days)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@admin_router.get("", response_model=MonitoringSummaryResponse)
def monitoring_summary(
    session: DbSession,
    hours: int = Query(default=24, ge=1, le=24 * 30),
    limit: int = Query(default=40, ge=1, le=200),
) -> MonitoringSummaryResponse:
    since = datetime.now(UTC) - timedelta(hours=hours)
    repository = OperationalEventRepository(session)
    return MonitoringSummaryResponse(
        window_hours=hours,
        counts=repository.counts_since(since),
        recent=[
            OperationalEventResponse(
                id=event.id,
                category=event.category,
                level=event.level,
                message=event.message,
                details=event.details,
                created_at=event.created_at,
            )
            for event in repository.list_since(since, limit=limit)
        ],
    )
