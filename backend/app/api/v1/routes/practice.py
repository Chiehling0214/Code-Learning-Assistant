"""Practice drills + topic mastery endpoints (Sprint 16)."""

from fastapi import APIRouter, HTTPException, status

from app.api.deps import (
    CurrentDbUser,
    EntitlementServiceDep,
    MasteryServiceDep,
    PracticeServiceDep,
)
from app.application.ports.ai_provider import (
    AINotConfiguredError,
    AIProviderError,
    AIQuotaError,
)
from app.application.services.ai_usage import RateLimitError
from app.application.services.entitlement_service import UpgradeRequiredError
from app.schemas.practice import (
    MasteryResponse,
    PracticeExerciseResponse,
    PracticeGenerateRequest,
    PracticeHistoryEntry,
    TopicMasteryResponse,
)

router = APIRouter(tags=["practice"])


@router.post("/practice/generate", response_model=PracticeExerciseResponse)
def generate_drill(
    body: PracticeGenerateRequest,
    current_user: CurrentDbUser,
    service: PracticeServiceDep,
    entitlements: EntitlementServiceDep,
) -> PracticeExerciseResponse:
    try:
        # Drills consume the plan's daily generation quota (402 over the cap).
        entitlements.check_generation(current_user.id)
        exercise = service.generate(
            user_id=current_user.id,
            language_slug=body.language,
            topic=body.topic,
            difficulty=body.difficulty,
        )
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except UpgradeRequiredError as exc:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED, detail=str(exc)
        ) from exc
    except RateLimitError as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(exc)
        ) from exc
    except AINotConfiguredError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc
    except (AIQuotaError, AIProviderError) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI is busy right now; please try again shortly.",
        ) from exc
    # The lesson title is the topic; look it up cheaply from the exercise itself.
    topic = body.topic or ""
    return PracticeExerciseResponse(
        exercise_id=exercise.id,
        title=exercise.title,
        topic=topic or service.topic_of(exercise),
        language=exercise.language,
    )


@router.get("/practice/history", response_model=list[PracticeHistoryEntry])
def practice_history(
    current_user: CurrentDbUser,
    service: PracticeServiceDep,
    language: str | None = None,
) -> list[PracticeHistoryEntry]:
    items = service.history(user_id=current_user.id, language_slug=language)
    return [
        PracticeHistoryEntry(
            exercise_id=i.exercise_id,
            title=i.title,
            topic=i.topic,
            language=i.language,
            last_verdict=i.last_verdict,
        )
        for i in items
    ]


@router.get("/me/mastery", response_model=MasteryResponse)
def get_mastery(
    language: str,
    current_user: CurrentDbUser,
    service: MasteryServiceDep,
) -> MasteryResponse:
    try:
        topics = service.snapshot(user_id=current_user.id, language_slug=language)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return MasteryResponse(
        language=language,
        topics=[
            TopicMasteryResponse(
                topic=t.topic,
                attempts=t.attempts,
                correct=t.correct,
                correct_rate=t.correct_rate,
                level=t.level,
                lesson_id=t.lesson_id,
            )
            for t in topics
        ],
    )
