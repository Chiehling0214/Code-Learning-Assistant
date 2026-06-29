"""SQLAlchemy-backed implementations of the domain repository interfaces.

Write methods ``add``/``flush``/``refresh`` only — the request-scoped session
(see ``infrastructure/db/session.py``) owns the commit/rollback.
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.entities import Course as CourseEntity
from app.domain.entities import Lesson as LessonEntity
from app.domain.entities import ProgrammingLanguage as LanguageEntity
from app.domain.entities import StudentProfile as ProfileEntity
from app.domain.entities import User as UserEntity
from app.infrastructure.models.models import Course as CourseModel
from app.infrastructure.models.models import Lesson as LessonModel
from app.infrastructure.models.models import ProgrammingLanguage as LanguageModel
from app.infrastructure.models.models import StudentProfile as ProfileModel
from app.infrastructure.models.models import User as UserModel


def _to_user(model: UserModel) -> UserEntity:
    return UserEntity(
        id=model.id,
        firebase_uid=model.firebase_uid,
        email=model.email,
        display_name=model.display_name,
        is_admin=model.is_admin,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def _to_profile(model: ProfileModel) -> ProfileEntity:
    return ProfileEntity(
        id=model.id,
        user_id=model.user_id,
        skill_level=model.skill_level,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


class SqlAlchemyUserRepository:
    """Concrete :class:`~app.domain.repositories.UserRepository`."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, user_id: uuid.UUID) -> UserEntity | None:
        model = self._session.get(UserModel, user_id)
        return _to_user(model) if model else None

    def get_by_firebase_uid(self, firebase_uid: str) -> UserEntity | None:
        stmt = select(UserModel).where(UserModel.firebase_uid == firebase_uid)
        model = self._session.scalars(stmt).first()
        return _to_user(model) if model else None

    def create(
        self,
        *,
        firebase_uid: str,
        email: str,
        display_name: str | None = None,
        is_admin: bool = False,
    ) -> UserEntity:
        model = UserModel(
            firebase_uid=firebase_uid,
            email=email,
            display_name=display_name,
            is_admin=is_admin,
        )
        self._session.add(model)
        self._session.flush()
        self._session.refresh(model)
        return _to_user(model)

    def update_display_name(self, user_id: uuid.UUID, display_name: str | None) -> UserEntity:
        model = self._session.get(UserModel, user_id)
        if model is None:
            raise LookupError(f"User {user_id} not found")
        model.display_name = display_name
        self._session.flush()
        self._session.refresh(model)
        return _to_user(model)


class SqlAlchemyStudentProfileRepository:
    """Concrete :class:`~app.domain.repositories.StudentProfileRepository`."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_user_id(self, user_id: uuid.UUID) -> ProfileEntity | None:
        stmt = select(ProfileModel).where(ProfileModel.user_id == user_id)
        model = self._session.scalars(stmt).first()
        return _to_profile(model) if model else None

    def create(self, *, user_id: uuid.UUID, skill_level: str = "beginner") -> ProfileEntity:
        model = ProfileModel(user_id=user_id, skill_level=skill_level)
        self._session.add(model)
        self._session.flush()
        self._session.refresh(model)
        return _to_profile(model)

    def update_skill_level(self, user_id: uuid.UUID, skill_level: str) -> ProfileEntity:
        stmt = select(ProfileModel).where(ProfileModel.user_id == user_id)
        model = self._session.scalars(stmt).first()
        if model is None:
            raise LookupError(f"Profile for user {user_id} not found")
        model.skill_level = skill_level
        self._session.flush()
        self._session.refresh(model)
        return _to_profile(model)


def _to_language(model: LanguageModel) -> LanguageEntity:
    return LanguageEntity(
        id=model.id, name=model.name, slug=model.slug, created_at=model.created_at
    )


def _to_course(model: CourseModel) -> CourseEntity:
    return CourseEntity(
        id=model.id,
        language_id=model.language_id,
        title=model.title,
        slug=model.slug,
        description=model.description,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def _to_lesson(model: LessonModel) -> LessonEntity:
    return LessonEntity(
        id=model.id,
        course_id=model.course_id,
        title=model.title,
        slug=model.slug,
        order_index=model.order_index,
        content=model.content,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


class SqlAlchemyLanguageRepository:
    """Concrete :class:`~app.domain.repositories.LanguageRepository`."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def list_all(self) -> list[LanguageEntity]:
        stmt = select(LanguageModel).order_by(LanguageModel.name)
        return [_to_language(m) for m in self._session.scalars(stmt).all()]

    def get_by_id(self, language_id: uuid.UUID) -> LanguageEntity | None:
        model = self._session.get(LanguageModel, language_id)
        return _to_language(model) if model else None

    def get_by_slug(self, slug: str) -> LanguageEntity | None:
        stmt = select(LanguageModel).where(LanguageModel.slug == slug)
        model = self._session.scalars(stmt).first()
        return _to_language(model) if model else None

    def create(self, *, name: str, slug: str) -> LanguageEntity:
        model = LanguageModel(name=name, slug=slug)
        self._session.add(model)
        self._session.flush()
        self._session.refresh(model)
        return _to_language(model)

    def update(
        self, language_id: uuid.UUID, *, name: str | None, slug: str | None
    ) -> LanguageEntity:
        model = self._session.get(LanguageModel, language_id)
        if model is None:
            raise LookupError(f"Language {language_id} not found")
        if name is not None:
            model.name = name
        if slug is not None:
            model.slug = slug
        self._session.flush()
        self._session.refresh(model)
        return _to_language(model)

    def delete(self, language_id: uuid.UUID) -> None:
        model = self._session.get(LanguageModel, language_id)
        if model is None:
            raise LookupError(f"Language {language_id} not found")
        self._session.delete(model)
        self._session.flush()


class SqlAlchemyCourseRepository:
    """Concrete :class:`~app.domain.repositories.CourseRepository`."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def list_all(self) -> list[CourseEntity]:
        stmt = select(CourseModel).order_by(CourseModel.title)
        return [_to_course(m) for m in self._session.scalars(stmt).all()]

    def get_by_id(self, course_id: uuid.UUID) -> CourseEntity | None:
        model = self._session.get(CourseModel, course_id)
        return _to_course(model) if model else None

    def get_by_slug(self, slug: str) -> CourseEntity | None:
        stmt = select(CourseModel).where(CourseModel.slug == slug)
        model = self._session.scalars(stmt).first()
        return _to_course(model) if model else None

    def create(
        self, *, language_id: uuid.UUID, title: str, slug: str, description: str | None
    ) -> CourseEntity:
        model = CourseModel(
            language_id=language_id, title=title, slug=slug, description=description
        )
        self._session.add(model)
        self._session.flush()
        self._session.refresh(model)
        return _to_course(model)

    def update(
        self,
        course_id: uuid.UUID,
        *,
        title: str | None,
        slug: str | None,
        description: str | None,
    ) -> CourseEntity:
        model = self._session.get(CourseModel, course_id)
        if model is None:
            raise LookupError(f"Course {course_id} not found")
        if title is not None:
            model.title = title
        if slug is not None:
            model.slug = slug
        if description is not None:
            model.description = description
        self._session.flush()
        self._session.refresh(model)
        return _to_course(model)

    def delete(self, course_id: uuid.UUID) -> None:
        model = self._session.get(CourseModel, course_id)
        if model is None:
            raise LookupError(f"Course {course_id} not found")
        self._session.delete(model)
        self._session.flush()


class SqlAlchemyLessonRepository:
    """Concrete :class:`~app.domain.repositories.LessonRepository`."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, lesson_id: uuid.UUID) -> LessonEntity | None:
        model = self._session.get(LessonModel, lesson_id)
        return _to_lesson(model) if model else None

    def list_by_course(self, course_id: uuid.UUID) -> list[LessonEntity]:
        stmt = (
            select(LessonModel)
            .where(LessonModel.course_id == course_id)
            .order_by(LessonModel.order_index, LessonModel.title)
        )
        return [_to_lesson(m) for m in self._session.scalars(stmt).all()]

    def create(
        self,
        *,
        course_id: uuid.UUID,
        title: str,
        slug: str,
        order_index: int,
        content: str,
    ) -> LessonEntity:
        model = LessonModel(
            course_id=course_id,
            title=title,
            slug=slug,
            order_index=order_index,
            content=content,
        )
        self._session.add(model)
        self._session.flush()
        self._session.refresh(model)
        return _to_lesson(model)

    def update(
        self,
        lesson_id: uuid.UUID,
        *,
        title: str | None,
        slug: str | None,
        order_index: int | None,
        content: str | None,
    ) -> LessonEntity:
        model = self._session.get(LessonModel, lesson_id)
        if model is None:
            raise LookupError(f"Lesson {lesson_id} not found")
        if title is not None:
            model.title = title
        if slug is not None:
            model.slug = slug
        if order_index is not None:
            model.order_index = order_index
        if content is not None:
            model.content = content
        self._session.flush()
        self._session.refresh(model)
        return _to_lesson(model)

    def delete(self, lesson_id: uuid.UUID) -> None:
        model = self._session.get(LessonModel, lesson_id)
        if model is None:
            raise LookupError(f"Lesson {lesson_id} not found")
        self._session.delete(model)
        self._session.flush()
