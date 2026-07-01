"""Placement-test endpoints (per language track)."""

import uuid

from fastapi import APIRouter, HTTPException, status

from app.api.deps import CurrentDbUser, PlacementServiceDep
from app.application.ports.ai_provider import (
    AINotConfiguredError,
    AIProviderError,
    AIQuotaError,
)
from app.application.services.ai_usage import RateLimitError
from app.schemas.placement import (
    PlacementCoding,
    PlacementMCQ,
    PlacementResponse,
    PlacementSubmitRequest,
    PlacementSubmitResponse,
)

router = APIRouter(tags=["placement"])


def _sanitized(placement) -> PlacementResponse:  # noqa: ANN001 - domain entity
    """Serialize a placement without answer keys / reference solutions."""
    items = placement.items or {}
    return PlacementResponse(
        track_id=placement.track_id,
        status=placement.status,
        level=placement.level,
        mcqs=[
            PlacementMCQ(
                id=m["id"],
                prompt=m["prompt"],
                choices=[{"id": c["id"], "text": c["text"]} for c in m["choices"]],
            )
            for m in items.get("mcqs", [])
        ],
        coding=[
            PlacementCoding(
                id=t["id"],
                prompt=t["prompt"],
                language=t["language"],
                starter_code=t["starter_code"],
            )
            for t in items.get("coding", [])
        ],
    )


def _handle_ai_error(exc: Exception) -> HTTPException:
    if isinstance(exc, LookupError):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    if isinstance(exc, RateLimitError):
        return HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(exc))
    if isinstance(exc, AINotConfiguredError):
        return HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI is not configured on this server.",
        )
    if isinstance(exc, AIQuotaError):
        return HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))
    if isinstance(exc, AIProviderError):
        return HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail="The AI service failed; try again."
        )
    raise exc


@router.post("/me/tracks/{track_id}/placement", response_model=PlacementResponse)
def generate_placement(
    track_id: uuid.UUID,
    current_user: CurrentDbUser,
    service: PlacementServiceDep,
) -> PlacementResponse:
    try:
        placement = service.generate(user_id=current_user.id, track_id=track_id)
    except Exception as exc:  # noqa: BLE001 - mapped to HTTP below
        raise _handle_ai_error(exc) from exc
    return _sanitized(placement)


@router.get("/me/tracks/{track_id}/placement", response_model=PlacementResponse)
def get_placement(
    track_id: uuid.UUID,
    current_user: CurrentDbUser,
    service: PlacementServiceDep,
) -> PlacementResponse:
    try:
        placement = service.get(user_id=current_user.id, track_id=track_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return _sanitized(placement)


@router.post("/me/tracks/{track_id}/placement/submit", response_model=PlacementSubmitResponse)
def submit_placement(
    track_id: uuid.UUID,
    payload: PlacementSubmitRequest,
    current_user: CurrentDbUser,
    service: PlacementServiceDep,
) -> PlacementSubmitResponse:
    try:
        level, percent, breakdown = service.submit(
            user_id=current_user.id,
            track_id=track_id,
            mcq_answers=payload.mcq_answers,
            code=payload.code,
        )
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return PlacementSubmitResponse(level=level, percent=percent, breakdown=breakdown)
