"""Language-track endpoints (the learner's chosen languages)."""

import uuid

from fastapi import APIRouter, HTTPException, status

from app.api.deps import CurrentDbUser, TrackServiceDep
from app.application.services.track_service import DuplicateTrackError, LanguageLimitError
from app.schemas.track import AddTrackRequest, TrackResponse

router = APIRouter(tags=["tracks"])


@router.get("/me/tracks", response_model=list[TrackResponse])
def list_my_tracks(current_user: CurrentDbUser, service: TrackServiceDep) -> list[TrackResponse]:
    return [TrackResponse(**t) for t in service.list_tracks(current_user.id)]


@router.post("/me/tracks", response_model=TrackResponse, status_code=status.HTTP_201_CREATED)
def add_my_track(
    payload: AddTrackRequest,
    current_user: CurrentDbUser,
    service: TrackServiceDep,
) -> TrackResponse:
    try:
        service.add_track(user_id=current_user.id, language_id=payload.language_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except DuplicateTrackError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except LanguageLimitError as exc:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED, detail=str(exc)
        ) from exc
    # Return the enriched view (with language name/slug).
    created = next(
        t for t in service.list_tracks(current_user.id) if t["language_id"] == payload.language_id
    )
    return TrackResponse(**created)


@router.delete("/me/tracks/{track_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_my_track(
    track_id: uuid.UUID,
    current_user: CurrentDbUser,
    service: TrackServiceDep,
) -> None:
    try:
        service.remove_track(user_id=current_user.id, track_id=track_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
