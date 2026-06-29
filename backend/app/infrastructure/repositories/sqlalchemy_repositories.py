"""SQLAlchemy-backed implementations of the domain repository interfaces."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.entities import User as UserEntity
from app.infrastructure.models.models import User as UserModel


def _to_entity(model: UserModel) -> UserEntity:
    return UserEntity(
        id=model.id,
        firebase_uid=model.firebase_uid,
        email=model.email,
        display_name=model.display_name,
        is_admin=model.is_admin,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


class SqlAlchemyUserRepository:
    """Concrete :class:`~app.domain.repositories.UserRepository`."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, user_id: uuid.UUID) -> UserEntity | None:
        model = self._session.get(UserModel, user_id)
        return _to_entity(model) if model else None

    def get_by_firebase_uid(self, firebase_uid: str) -> UserEntity | None:
        stmt = select(UserModel).where(UserModel.firebase_uid == firebase_uid)
        model = self._session.scalars(stmt).first()
        return _to_entity(model) if model else None
