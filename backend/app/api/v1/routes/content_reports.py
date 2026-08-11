import uuid

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import ContentReportServiceDep, CurrentDbUser, require_admin
from app.application.ports.ai_provider import AIProviderError
from app.application.services.ai_usage import RateLimitError
from app.schemas.content_reports import (
    ContentRegenerateRequest,
    ContentReportCreate,
    ContentReportResponse,
    ContentReportStatus,
    ContentVersionHistoryResponse,
    ContentVersionResponse,
)

router = APIRouter(tags=["content reports"])
admin_router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])


def _version_response(version) -> ContentVersionResponse:  # noqa: ANN001
    return ContentVersionResponse(
        id=version.id,
        item_type=version.item_type,
        item_id=version.item_id,
        created_by=version.created_by,
        created_at=version.created_at,
        snapshot=version.snapshot,
    )


@router.post("/content/reports", response_model=ContentReportResponse, status_code=201)
def create_report(
    body: ContentReportCreate,
    current_user: CurrentDbUser,
    service: ContentReportServiceDep,
) -> ContentReportResponse:
    try:
        return service.report(user_id=current_user.id, **body.model_dump())
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@admin_router.get("/content-reports", response_model=list[ContentReportResponse])
def list_reports(
    service: ContentReportServiceDep, report_status: str | None = None
) -> list[ContentReportResponse]:
    return service.list_reports(report_status)


@admin_router.patch("/content-reports/{report_id}", response_model=ContentReportResponse)
def set_report_status(
    report_id: uuid.UUID,
    body: ContentReportStatus,
    service: ContentReportServiceDep,
) -> ContentReportResponse:
    try:
        return service.set_status(report_id, body.status)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@admin_router.get(
    "/content/{item_type}/{item_id}/versions",
    response_model=ContentVersionHistoryResponse,
)
def list_content_versions(
    item_type: str,
    item_id: uuid.UUID,
    service: ContentReportServiceDep,
) -> ContentVersionHistoryResponse:
    try:
        return ContentVersionHistoryResponse(
            current_snapshot=service.current_snapshot(item_type, item_id),
            versions=[
                _version_response(version)
                for version in service.list_versions(item_type, item_id)
            ],
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@admin_router.post(
    "/content/versions/{version_id}/restore",
    status_code=status.HTTP_204_NO_CONTENT,
)
def restore_content_version(
    version_id: uuid.UUID,
    current_user: CurrentDbUser,
    service: ContentReportServiceDep,
) -> None:
    try:
        service.restore(version_id, current_user.id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@admin_router.post(
    "/content/{item_type}/{item_id}/regenerate",
    status_code=status.HTTP_204_NO_CONTENT,
)
def regenerate_content(
    item_type: str,
    item_id: uuid.UUID,
    current_user: CurrentDbUser,
    service: ContentReportServiceDep,
    body: ContentRegenerateRequest | None = None,
) -> None:
    try:
        service.regenerate(
            item_type=item_type,
            item_id=item_id,
            admin_user_id=current_user.id,
            instructions=body.instructions if body else "",
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RateLimitError as exc:
        raise HTTPException(status_code=429, detail=str(exc)) from exc
    except AIProviderError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
