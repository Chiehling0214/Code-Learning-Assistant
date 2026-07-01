"""SQLAlchemy-backed implementations of the domain repository interfaces.

Write methods ``add``/``flush``/``refresh`` only — the request-scoped session
(see ``infrastructure/db/session.py``) owns the commit/rollback.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.domain.entities import AIInteraction as AIInteractionEntity
from app.domain.entities import Choice as ChoiceEntity
from app.domain.entities import Course as CourseEntity
from app.domain.entities import Exercise as ExerciseEntity
from app.domain.entities import Lesson as LessonEntity
from app.domain.entities import ProgrammingLanguage as LanguageEntity
from app.domain.entities import Question as QuestionEntity
from app.domain.entities import Quiz as QuizEntity
from app.domain.entities import QuizAttempt as QuizAttemptEntity
from app.domain.entities import StudentProfile as ProfileEntity
from app.domain.entities import Submission as SubmissionEntity
from app.domain.entities import User as UserEntity
from app.infrastructure.models.models import AIInteraction as AIInteractionModel
from app.infrastructure.models.models import Choice as ChoiceModel
from app.infrastructure.models.models import Course as CourseModel
from app.infrastructure.models.models import Exercise as ExerciseModel
from app.infrastructure.models.models import Lesson as LessonModel
from app.infrastructure.models.models import ProgrammingLanguage as LanguageModel
from app.infrastructure.models.models import Question as QuestionModel
from app.infrastructure.models.models import Quiz as QuizModel
from app.infrastructure.models.models import QuizAttempt as QuizAttemptModel
from app.infrastructure.models.models import StudentProfile as ProfileModel
from app.infrastructure.models.models import Submission as SubmissionModel
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
        source=model.source,
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
        source: str = "human",
    ) -> LessonEntity:
        model = LessonModel(
            course_id=course_id,
            title=title,
            slug=slug,
            order_index=order_index,
            content=content,
            source=source,
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


def _to_exercise(model: ExerciseModel) -> ExerciseEntity:
    return ExerciseEntity(
        id=model.id,
        lesson_id=model.lesson_id,
        language=model.language,
        title=model.title,
        slug=model.slug,
        prompt=model.prompt,
        starter_code=model.starter_code,
        test_spec=model.test_spec or {},
        created_at=model.created_at,
        updated_at=model.updated_at,
        source=model.source,
    )


def _to_submission(model: SubmissionModel) -> SubmissionEntity:
    return SubmissionEntity(
        id=model.id,
        user_id=model.user_id,
        exercise_id=model.exercise_id,
        code=model.code,
        status=model.status,
        result=model.result,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


class SqlAlchemyExerciseRepository:
    """Concrete :class:`~app.domain.repositories.ExerciseRepository`."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, exercise_id: uuid.UUID) -> ExerciseEntity | None:
        model = self._session.get(ExerciseModel, exercise_id)
        return _to_exercise(model) if model else None

    def list_by_lesson(self, lesson_id: uuid.UUID) -> list[ExerciseEntity]:
        stmt = (
            select(ExerciseModel)
            .where(ExerciseModel.lesson_id == lesson_id)
            .order_by(ExerciseModel.title)
        )
        return [_to_exercise(m) for m in self._session.scalars(stmt).all()]

    def create(
        self,
        *,
        lesson_id: uuid.UUID,
        language: str,
        title: str,
        slug: str,
        prompt: str,
        starter_code: str,
        test_spec: dict,
        source: str = "human",
    ) -> ExerciseEntity:
        model = ExerciseModel(
            lesson_id=lesson_id,
            language=language,
            title=title,
            slug=slug,
            prompt=prompt,
            starter_code=starter_code,
            test_spec=test_spec,
            source=source,
        )
        self._session.add(model)
        self._session.flush()
        self._session.refresh(model)
        return _to_exercise(model)

    def delete(self, exercise_id: uuid.UUID) -> None:
        model = self._session.get(ExerciseModel, exercise_id)
        if model is None:
            raise LookupError(f"Exercise {exercise_id} not found")
        self._session.delete(model)
        self._session.flush()


class SqlAlchemySubmissionRepository:
    """Concrete :class:`~app.domain.repositories.SubmissionRepository`."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, submission_id: uuid.UUID) -> SubmissionEntity | None:
        model = self._session.get(SubmissionModel, submission_id)
        return _to_submission(model) if model else None

    def list_for_user_and_exercise(
        self, user_id: uuid.UUID, exercise_id: uuid.UUID
    ) -> list[SubmissionEntity]:
        stmt = (
            select(SubmissionModel)
            .where(
                SubmissionModel.user_id == user_id,
                SubmissionModel.exercise_id == exercise_id,
            )
            .order_by(SubmissionModel.created_at.desc())
        )
        return [_to_submission(m) for m in self._session.scalars(stmt).all()]

    def create(
        self,
        *,
        user_id: uuid.UUID,
        exercise_id: uuid.UUID,
        code: str,
        status: str = "pending",
    ) -> SubmissionEntity:
        model = SubmissionModel(
            user_id=user_id,
            exercise_id=exercise_id,
            code=code,
            status=status,
        )
        self._session.add(model)
        self._session.flush()
        self._session.refresh(model)
        return _to_submission(model)

    def update_result(
        self, submission_id: uuid.UUID, *, status: str, result: dict | None
    ) -> SubmissionEntity:
        model = self._session.get(SubmissionModel, submission_id)
        if model is None:
            raise LookupError(f"Submission {submission_id} not found")
        model.status = status
        model.result = result
        self._session.flush()
        self._session.refresh(model)
        return _to_submission(model)


# --------------------------------------------------------------------------- #
# Quizzes
# --------------------------------------------------------------------------- #


def _to_choice(model: ChoiceModel) -> ChoiceEntity:
    return ChoiceEntity(
        id=model.id,
        question_id=model.question_id,
        text=model.text,
        is_correct=model.is_correct,
        order_index=model.order_index,
    )


def _to_question(model: QuestionModel) -> QuestionEntity:
    return QuestionEntity(
        id=model.id,
        quiz_id=model.quiz_id,
        prompt=model.prompt,
        type=model.type,
        order_index=model.order_index,
        choices=[_to_choice(c) for c in model.choices],
    )


def _to_quiz(model: QuizModel) -> QuizEntity:
    return QuizEntity(
        id=model.id,
        lesson_id=model.lesson_id,
        title=model.title,
        slug=model.slug,
        description=model.description,
        questions=[_to_question(q) for q in model.questions],
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def _to_attempt(model: QuizAttemptModel) -> QuizAttemptEntity:
    return QuizAttemptEntity(
        id=model.id,
        user_id=model.user_id,
        quiz_id=model.quiz_id,
        score=model.score,
        answers=model.answers or {},
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


class SqlAlchemyQuizRepository:
    """Concrete :class:`~app.domain.repositories.QuizRepository`."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, quiz_id: uuid.UUID) -> QuizEntity | None:
        model = self._session.get(QuizModel, quiz_id)
        return _to_quiz(model) if model else None

    def list_by_lesson(self, lesson_id: uuid.UUID) -> list[QuizEntity]:
        stmt = (
            select(QuizModel)
            .where(QuizModel.lesson_id == lesson_id)
            .order_by(QuizModel.title)
        )
        return [_to_quiz(m) for m in self._session.scalars(stmt).all()]

    def create(
        self, *, lesson_id: uuid.UUID, title: str, slug: str, description: str | None
    ) -> QuizEntity:
        model = QuizModel(lesson_id=lesson_id, title=title, slug=slug, description=description)
        self._session.add(model)
        self._session.flush()
        self._session.refresh(model)
        return _to_quiz(model)

    def add_question(
        self,
        *,
        quiz_id: uuid.UUID,
        prompt: str,
        type: str,
        order_index: int,
        choices: list[dict],
    ) -> QuestionEntity:
        question = QuestionModel(
            quiz_id=quiz_id, prompt=prompt, type=type, order_index=order_index
        )
        for idx, choice in enumerate(choices):
            question.choices.append(
                ChoiceModel(
                    text=choice["text"],
                    is_correct=bool(choice.get("is_correct", False)),
                    order_index=choice.get("order_index", idx),
                )
            )
        self._session.add(question)
        self._session.flush()
        self._session.refresh(question)
        return _to_question(question)

    def delete(self, quiz_id: uuid.UUID) -> None:
        model = self._session.get(QuizModel, quiz_id)
        if model is None:
            raise LookupError(f"Quiz {quiz_id} not found")
        self._session.delete(model)
        self._session.flush()


class SqlAlchemyQuizAttemptRepository:
    """Concrete :class:`~app.domain.repositories.QuizAttemptRepository`."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def create(
        self, *, user_id: uuid.UUID, quiz_id: uuid.UUID, score: int, answers: dict
    ) -> QuizAttemptEntity:
        model = QuizAttemptModel(
            user_id=user_id, quiz_id=quiz_id, score=score, answers=answers
        )
        self._session.add(model)
        self._session.flush()
        self._session.refresh(model)
        return _to_attempt(model)

    def list_for_user_and_quiz(
        self, user_id: uuid.UUID, quiz_id: uuid.UUID
    ) -> list[QuizAttemptEntity]:
        stmt = (
            select(QuizAttemptModel)
            .where(
                QuizAttemptModel.user_id == user_id,
                QuizAttemptModel.quiz_id == quiz_id,
            )
            .order_by(QuizAttemptModel.created_at.desc())
        )
        return [_to_attempt(m) for m in self._session.scalars(stmt).all()]


def _to_interaction(model: AIInteractionModel) -> AIInteractionEntity:
    return AIInteractionEntity(
        id=model.id,
        user_id=model.user_id,
        kind=model.kind,
        model=model.model,
        total_tokens=model.total_tokens,
        created_at=model.created_at,
    )


class SqlAlchemyAIInteractionRepository:
    """Concrete :class:`~app.domain.repositories.AIInteractionRepository`."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def create(
        self, *, user_id: uuid.UUID, kind: str, model: str, total_tokens: int
    ) -> AIInteractionEntity:
        record = AIInteractionModel(
            user_id=user_id, kind=kind, model=model, total_tokens=total_tokens
        )
        self._session.add(record)
        self._session.flush()
        self._session.refresh(record)
        return _to_interaction(record)

    def count_since(self, user_id: uuid.UUID, since: datetime) -> int:
        stmt = select(func.count()).where(
            AIInteractionModel.user_id == user_id,
            AIInteractionModel.created_at >= since,
        )
        return int(self._session.scalar(stmt) or 0)
