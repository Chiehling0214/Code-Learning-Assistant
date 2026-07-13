"""Spaced-review endpoints: due queue, answering, and the mistakes notebook."""

import uuid

from fastapi import APIRouter, HTTPException, status

from app.api.deps import CurrentDbUser, ReviewServiceDep
from app.schemas.review import (
    AnswerRequest,
    DueReviewsResponse,
    NotebookResponse,
    ReviewItemResponse,
)

router = APIRouter(tags=["review"])


def _item(entity) -> ReviewItemResponse:  # noqa: ANN001 - domain entity
    return ReviewItemResponse(
        id=entity.id,
        source=entity.source,
        payload=entity.payload,
        interval_days=entity.interval_days,
        due_at=entity.due_at,
        lapses=entity.lapses,
        passes=entity.passes,
        retired=entity.retired,
    )


@router.get("/me/review", response_model=DueReviewsResponse)
def get_due_reviews(current_user: CurrentDbUser, service: ReviewServiceDep) -> DueReviewsResponse:
    due = service.list_due(current_user.id)
    return DueReviewsResponse(due_count=len(due), items=[_item(i) for i in due])


@router.get("/me/review/all", response_model=NotebookResponse)
def get_notebook(current_user: CurrentDbUser, service: ReviewServiceDep) -> NotebookResponse:
    return NotebookResponse(items=[_item(i) for i in service.notebook(current_user.id)])


@router.post("/me/review/{item_id}/answer", response_model=ReviewItemResponse)
def answer_review(
    item_id: uuid.UUID,
    body: AnswerRequest,
    current_user: CurrentDbUser,
    service: ReviewServiceDep,
) -> ReviewItemResponse:
    try:
        item = service.answer(user_id=current_user.id, item_id=item_id, correct=body.correct)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return _item(item)
