"""Authenticated cross-device exercise draft endpoints."""

import uuid

from fastapi import APIRouter, HTTPException, Response, status

from app.api.deps import CurrentDbUser, DraftServiceDep
from app.schemas.draft import DraftResponse, DraftSaveRequest

router = APIRouter(tags=["drafts"])


def _response(draft) -> DraftResponse:  # noqa: ANN001 - domain entity
    return DraftResponse(
        exercise_id=draft.exercise_id,
        code=draft.code,
        updated_at=draft.updated_at,
    )


@router.get("/exercises/{exercise_id}/draft", response_model=DraftResponse | None)
def get_draft(
    exercise_id: uuid.UUID,
    current_user: CurrentDbUser,
    service: DraftServiceDep,
) -> DraftResponse | Response:
    try:
        draft = service.get(user_id=current_user.id, exercise_id=exercise_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    if draft is None:
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    return _response(draft)


@router.put("/exercises/{exercise_id}/draft", response_model=DraftResponse)
def save_draft(
    exercise_id: uuid.UUID,
    body: DraftSaveRequest,
    current_user: CurrentDbUser,
    service: DraftServiceDep,
) -> DraftResponse:
    try:
        draft = service.save(
            user_id=current_user.id,
            exercise_id=exercise_id,
            code=body.code,
        )
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return _response(draft)


@router.delete("/exercises/{exercise_id}/draft", status_code=status.HTTP_204_NO_CONTENT)
def delete_draft(
    exercise_id: uuid.UUID,
    current_user: CurrentDbUser,
    service: DraftServiceDep,
) -> None:
    service.delete(user_id=current_user.id, exercise_id=exercise_id)
