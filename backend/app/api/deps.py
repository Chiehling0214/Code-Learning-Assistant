"""FastAPI dependency-injection wiring.

This is the composition root: it turns infrastructure (DB sessions, repositories)
and security primitives into ``Depends``-able callables for the API layer.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.application.services.user_service import UserService
from app.core.config import Settings, get_settings
from app.core.security import Identity, verify_token
from app.domain.entities import User
from app.infrastructure.db.session import get_session
from app.infrastructure.repositories.sqlalchemy_repositories import (
    SqlAlchemyStudentProfileRepository,
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
