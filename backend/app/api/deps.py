"""FastAPI dependency-injection wiring.

This is the composition root: it turns infrastructure (DB sessions, repositories)
and security primitives into ``Depends``-able callables for the API layer.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.application.ports.ai_provider import AIProvider
from app.application.services.ai_teacher_service import AITeacherService
from app.application.services.ai_tutor_service import AITutorService
from app.application.services.ai_usage import AIUsageGuard
from app.application.services.content_service import ContentService
from app.application.services.curriculum_service import CurriculumService
from app.application.services.execution_service import ExecutionService
from app.application.services.exercise_service import ExerciseService
from app.application.services.generate_content_service import GenerateContentService
from app.application.services.placement_service import PlacementService
from app.application.services.progress_service import ProgressService
from app.application.services.quiz_service import QuizService
from app.application.services.recommendation_service import RecommendationService
from app.application.services.submission_service import SubmissionService
from app.application.services.subscription_service import SubscriptionService
from app.application.services.track_service import TrackService
from app.application.services.user_service import UserService
from app.core.config import Settings, get_settings
from app.core.security import Identity, verify_token
from app.domain.entities import User
from app.infrastructure.ai.gemini_provider import GeminiAIProvider
from app.infrastructure.billing.stripe_client import StripeClient
from app.infrastructure.db.session import get_session
from app.infrastructure.judge0.client import Judge0Client
from app.infrastructure.repositories.sqlalchemy_repositories import (
    SqlAlchemyAIInteractionRepository,
    SqlAlchemyCourseRepository,
    SqlAlchemyExerciseRepository,
    SqlAlchemyGenerationJobRepository,
    SqlAlchemyLanguageRepository,
    SqlAlchemyLanguageTrackRepository,
    SqlAlchemyLessonRepository,
    SqlAlchemyPlacementRepository,
    SqlAlchemyProgressRepository,
    SqlAlchemyQuizAttemptRepository,
    SqlAlchemyQuizRepository,
    SqlAlchemyStudentProfileRepository,
    SqlAlchemySubmissionRepository,
    SqlAlchemySubscriptionRepository,
    SqlAlchemyUserRepository,
)


def get_db() -> Iterator[Session]:
    yield from get_session()


SettingsDep = Annotated[Settings, Depends(get_settings)]
DbSession = Annotated[Session, Depends(get_db)]


def get_current_user(request: Request, settings: SettingsDep) -> Identity:
    """Resolve the authenticated identity from the ``Authorization`` header.

    Verification is delegated to :func:`app.core.security.verify_token`, which
    returns a development stub while ``AUTH_STUB_ENABLED`` is true.
    """
    auth_header = request.headers.get("Authorization", "")
    token = auth_header[7:] if auth_header.lower().startswith("bearer ") else None
    return verify_token(token, settings)


CurrentUser = Annotated[Identity, Depends(get_current_user)]


def get_user_repository(session: DbSession) -> SqlAlchemyUserRepository:
    return SqlAlchemyUserRepository(session)


def get_profile_repository(session: DbSession) -> SqlAlchemyStudentProfileRepository:
    return SqlAlchemyStudentProfileRepository(session)


def get_user_service(
    users: Annotated[SqlAlchemyUserRepository, Depends(get_user_repository)],
    profiles: Annotated[SqlAlchemyStudentProfileRepository, Depends(get_profile_repository)],
) -> UserService:
    return UserService(users, profiles)


UserServiceDep = Annotated[UserService, Depends(get_user_service)]


def get_current_db_user(current_user: CurrentUser, service: UserServiceDep) -> User:
    """Resolve the authenticated identity to a persisted user.

    Provisions the user (and an empty profile) on first sign-in.
    """
    return service.get_or_create_from_identity(current_user)


CurrentDbUser = Annotated[User, Depends(get_current_db_user)]


def require_admin(current_user: CurrentDbUser) -> User:
    """Guard for admin-only endpoints; returns ``403`` for non-admin users."""
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return current_user


AdminUser = Annotated[User, Depends(require_admin)]


def get_content_service(session: DbSession) -> ContentService:
    return ContentService(
        SqlAlchemyLanguageRepository(session),
        SqlAlchemyCourseRepository(session),
        SqlAlchemyLessonRepository(session),
    )


ContentServiceDep = Annotated[ContentService, Depends(get_content_service)]


def get_exercise_service(session: DbSession) -> ExerciseService:
    return ExerciseService(
        SqlAlchemyExerciseRepository(session),
        SqlAlchemyLessonRepository(session),
    )


ExerciseServiceDep = Annotated[ExerciseService, Depends(get_exercise_service)]


def get_submission_service(session: DbSession) -> SubmissionService:
    return SubmissionService(
        SqlAlchemySubmissionRepository(session),
        SqlAlchemyExerciseRepository(session),
    )


SubmissionServiceDep = Annotated[SubmissionService, Depends(get_submission_service)]


def get_execution_service(settings: SettingsDep) -> ExecutionService:
    return ExecutionService(Judge0Client(settings))


ExecutionServiceDep = Annotated[ExecutionService, Depends(get_execution_service)]


def get_quiz_service(session: DbSession) -> QuizService:
    return QuizService(
        SqlAlchemyQuizRepository(session),
        SqlAlchemyQuizAttemptRepository(session),
        SqlAlchemyLessonRepository(session),
        SqlAlchemyProgressRepository(session),
    )


QuizServiceDep = Annotated[QuizService, Depends(get_quiz_service)]


def get_progress_service(session: DbSession) -> ProgressService:
    return ProgressService(
        SqlAlchemyCourseRepository(session),
        SqlAlchemyLessonRepository(session),
        SqlAlchemyExerciseRepository(session),
        SqlAlchemyQuizRepository(session),
        SqlAlchemyProgressRepository(session),
        SqlAlchemyLanguageTrackRepository(session),
    )


ProgressServiceDep = Annotated[ProgressService, Depends(get_progress_service)]


def get_recommendation_service(session: DbSession) -> RecommendationService:
    return RecommendationService(
        SqlAlchemyCourseRepository(session),
        SqlAlchemyLessonRepository(session),
        SqlAlchemyExerciseRepository(session),
        SqlAlchemyQuizRepository(session),
        SqlAlchemyProgressRepository(session),
        SqlAlchemyLanguageTrackRepository(session),
    )


RecommendationServiceDep = Annotated[
    RecommendationService, Depends(get_recommendation_service)
]


# ----- Billing (Sprint 8) -----


def get_subscription_service(session: DbSession, settings: SettingsDep) -> SubscriptionService:
    return SubscriptionService(SqlAlchemySubscriptionRepository(session), StripeClient(settings))


SubscriptionServiceDep = Annotated[SubscriptionService, Depends(get_subscription_service)]


def get_track_service(session: DbSession, settings: SettingsDep) -> TrackService:
    return TrackService(
        SqlAlchemyLanguageTrackRepository(session),
        SqlAlchemyLanguageRepository(session),
        SubscriptionService(SqlAlchemySubscriptionRepository(session), StripeClient(settings)),
        settings,
    )


TrackServiceDep = Annotated[TrackService, Depends(get_track_service)]


def get_placement_service(session: DbSession, settings: SettingsDep) -> PlacementService:
    return PlacementService(
        GeminiAIProvider(settings),
        SqlAlchemyPlacementRepository(session),
        SqlAlchemyLanguageTrackRepository(session),
        SqlAlchemyLanguageRepository(session),
        SqlAlchemyStudentProfileRepository(session),
        ExecutionService(Judge0Client(settings)),
        AIUsageGuard(SqlAlchemyAIInteractionRepository(session), settings),
        settings,
    )


PlacementServiceDep = Annotated[PlacementService, Depends(get_placement_service)]


def get_curriculum_service(session: DbSession, settings: SettingsDep) -> CurriculumService:
    return CurriculumService(
        GeminiAIProvider(settings),
        SqlAlchemyGenerationJobRepository(session),
        SqlAlchemyCourseRepository(session),
        SqlAlchemyLessonRepository(session),
        SqlAlchemyExerciseRepository(session),
        SqlAlchemyQuizRepository(session),
        SqlAlchemyLanguageRepository(session),
        SqlAlchemyLanguageTrackRepository(session),
        ExecutionService(Judge0Client(settings)),
        AIUsageGuard(SqlAlchemyAIInteractionRepository(session), settings),
        settings,
    )


CurriculumServiceDep = Annotated[CurriculumService, Depends(get_curriculum_service)]


def require_active_subscription(
    current_user: CurrentDbUser,
    settings: SettingsDep,
    subscriptions: SubscriptionServiceDep,
) -> User:
    """Guard for premium endpoints.

    A no-op while ``billing_enabled`` is false (dev default). When billing is on,
    non-subscribers get ``402 Payment Required``.
    """
    if not settings.billing_enabled:
        return current_user
    if not subscriptions.is_active(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="This feature requires an active subscription",
        )
    return current_user


PremiumUser = Annotated[User, Depends(require_active_subscription)]


# ----- AI (Sprint 6) -----


def get_ai_provider(settings: SettingsDep) -> AIProvider:
    return GeminiAIProvider(settings)


AIProviderDep = Annotated[AIProvider, Depends(get_ai_provider)]


def get_ai_usage_guard(session: DbSession, settings: SettingsDep) -> AIUsageGuard:
    return AIUsageGuard(SqlAlchemyAIInteractionRepository(session), settings)


AIUsageGuardDep = Annotated[AIUsageGuard, Depends(get_ai_usage_guard)]


def get_ai_teacher_service(
    provider: AIProviderDep, session: DbSession, usage: AIUsageGuardDep
) -> AITeacherService:
    return AITeacherService(provider, SqlAlchemyLessonRepository(session), usage)


AITeacherServiceDep = Annotated[AITeacherService, Depends(get_ai_teacher_service)]


def get_ai_tutor_service(
    provider: AIProviderDep, session: DbSession, usage: AIUsageGuardDep
) -> AITutorService:
    return AITutorService(provider, SqlAlchemyExerciseRepository(session), usage)


AITutorServiceDep = Annotated[AITutorService, Depends(get_ai_tutor_service)]


def get_generate_content_service(
    provider: AIProviderDep, session: DbSession, settings: SettingsDep, usage: AIUsageGuardDep
) -> GenerateContentService:
    content = ContentService(
        SqlAlchemyLanguageRepository(session),
        SqlAlchemyCourseRepository(session),
        SqlAlchemyLessonRepository(session),
    )
    exercises = ExerciseService(
        SqlAlchemyExerciseRepository(session),
        SqlAlchemyLessonRepository(session),
    )
    execution = ExecutionService(Judge0Client(settings))
    return GenerateContentService(provider, content, exercises, execution, usage)


GenerateContentServiceDep = Annotated[
    GenerateContentService, Depends(get_generate_content_service)
]
