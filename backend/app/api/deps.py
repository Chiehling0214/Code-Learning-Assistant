"""FastAPI dependency-injection wiring.

This is the composition root: it turns infrastructure (DB sessions, repositories)
and security primitives into ``Depends``-able callables for the API layer.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.application.services.content_service import ContentService
from app.application.services.execution_service import ExecutionService
from app.application.services.exercise_service import ExerciseService
from app.application.services.quiz_service import QuizService
from app.application.services.submission_service import SubmissionService
from app.application.services.user_service import UserService
from app.core.config import Settings, get_settings
from app.core.security import Identity, verify_token
from app.domain.entities import User
from app.infrastructure.db.session import get_session
from app.infrastructure.judge0.client import Judge0Client
from app.infrastructure.repositories.sqlalchemy_repositories import (
    SqlAlchemyCourseRepository,
    SqlAlchemyExerciseRepository,
    SqlAlchemyLanguageRepository,
    SqlAlchemyLessonRepository,
    SqlAlchemyQuizAttemptRepository,
    SqlAlchemyQuizRepository,
    SqlAlchemyStudentProfileRepository,
    SqlAlchemySubmissionRepository,
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
    )


QuizServiceDep = Annotated[QuizService, Depends(get_quiz_service)]
