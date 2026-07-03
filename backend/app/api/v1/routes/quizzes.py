"""Quiz endpoints.

- Public: list a lesson's quizzes, read a quiz (answer keys stripped).
- Authenticated learner: submit answers (auto-graded), list own attempts.
- Admin: create quizzes, add questions, delete quizzes.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import CurrentDbUser, QuizServiceDep, require_admin
from app.schemas.quiz import (
    AttemptResponse,
    ChoiceResponse,
    QuestionCreate,
    QuestionResponse,
    QuizCreate,
    QuizResponse,
    QuizSubmitRequest,
    QuizSubmitResponse,
    QuizSummary,
)

router = APIRouter(tags=["quizzes"])
admin_router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])


def _quiz_response(quiz) -> QuizResponse:  # noqa: ANN001 - domain entity
    """Serialize a quiz for learners, stripping the ``is_correct`` answer key."""
    return QuizResponse(
        id=quiz.id,
        lesson_id=quiz.lesson_id,
        title=quiz.title,
        slug=quiz.slug,
        description=quiz.description,
        questions=[
            QuestionResponse(
                id=q.id,
                prompt=q.prompt,
                type=q.type,
                order_index=q.order_index,
                choices=[
                    ChoiceResponse(id=c.id, text=c.text, order_index=c.order_index)
                    for c in q.choices
                ],
            )
            for q in quiz.questions
        ],
    )


# ----- public reads -----


@router.get("/lessons/{lesson_id}/quizzes", response_model=list[QuizSummary])
def list_lesson_quizzes(lesson_id: uuid.UUID, service: QuizServiceDep) -> list[QuizSummary]:
    return [
        QuizSummary(id=q.id, title=q.title, slug=q.slug)
        for q in service.list_for_lesson(lesson_id)
    ]


@router.get("/quizzes/{quiz_id}", response_model=QuizResponse)
def get_quiz(quiz_id: uuid.UUID, service: QuizServiceDep) -> QuizResponse:
    try:
        quiz = service.get_quiz(quiz_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return _quiz_response(quiz)


# ----- learner -----


@router.post("/quizzes/{quiz_id}/submit", response_model=QuizSubmitResponse)
def submit_quiz(
    quiz_id: uuid.UUID,
    payload: QuizSubmitRequest,
    current_user: CurrentDbUser,
    service: QuizServiceDep,
) -> QuizSubmitResponse:
    try:
        attempt, total, results = service.grade(
            user_id=current_user.id, quiz_id=quiz_id, answers=payload.answers
        )
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return QuizSubmitResponse(
        attempt_id=attempt.id, score=attempt.score, total=total, results=results
    )


@router.get("/quizzes/{quiz_id}/attempts", response_model=list[AttemptResponse])
def list_quiz_attempts(
    quiz_id: uuid.UUID,
    current_user: CurrentDbUser,
    service: QuizServiceDep,
) -> list[AttemptResponse]:
    attempts = service.list_attempts(user_id=current_user.id, quiz_id=quiz_id)
    return [
        AttemptResponse(
            id=a.id,
            quiz_id=a.quiz_id,
            score=a.score,
            total=a.answers.get("total", a.score),
            created_at=a.created_at,
        )
        for a in attempts
    ]


# ----- admin -----


@admin_router.post("/quizzes", response_model=QuizResponse, status_code=status.HTTP_201_CREATED)
def create_quiz(payload: QuizCreate, service: QuizServiceDep) -> QuizResponse:
    try:
        quiz = service.create_quiz(
            lesson_id=payload.lesson_id,
            title=payload.title,
            slug=payload.slug,
            description=payload.description,
        )
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return _quiz_response(quiz)


@admin_router.post(
    "/quizzes/{quiz_id}/questions",
    response_model=QuestionResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_question(
    quiz_id: uuid.UUID, payload: QuestionCreate, service: QuizServiceDep
) -> QuestionResponse:
    try:
        question = service.add_question(
            quiz_id=quiz_id,
            prompt=payload.prompt,
            type=payload.type,
            order_index=payload.order_index,
            choices=[c.model_dump() for c in payload.choices],
            explanation=payload.explanation,
        )
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return QuestionResponse(
        id=question.id,
        prompt=question.prompt,
        type=question.type,
        order_index=question.order_index,
        choices=[
            ChoiceResponse(id=c.id, text=c.text, order_index=c.order_index)
            for c in question.choices
        ],
    )


@admin_router.delete("/quizzes/{quiz_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_quiz(quiz_id: uuid.UUID, service: QuizServiceDep) -> None:
    try:
        service.delete_quiz(quiz_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
