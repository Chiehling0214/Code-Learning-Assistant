"""In-memory fake repositories for tests (no database required)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from app.application.ports.ai_provider import (
    AIResponse,
    GeneratedExercise,
    GeneratedLesson,
)
from app.domain.entities import (
    AIInteraction,
    Choice,
    Course,
    Exercise,
    Lesson,
    ProgrammingLanguage,
    Question,
    Quiz,
    QuizAttempt,
    StudentProfile,
    Submission,
    User,
)
from app.infrastructure.judge0.client import Judge0Error


def _now() -> datetime:
    return datetime.now(UTC)


class FakeCodeRunner:
    """Configurable stand-in for the Judge0 client used in execution tests."""

    def __init__(self) -> None:
        self.result: dict = {
            "stdout": "",
            "stderr": "",
            "status_id": 3,
            "status": "Accepted",
            "compile_output": None,
        }
        self.raise_error = False

    def set(self, **kwargs) -> None:
        self.result.update(kwargs)

    def execute(self, source_code: str, language: str, stdin: str = "") -> dict:
        if self.raise_error:
            raise Judge0Error("Judge0 unavailable")
        return dict(self.result)


class FakeUserRepository:
    def __init__(self) -> None:
        self._by_id: dict[uuid.UUID, User] = {}

    def get_by_id(self, user_id: uuid.UUID) -> User | None:
        return self._by_id.get(user_id)

    def get_by_firebase_uid(self, firebase_uid: str) -> User | None:
        return next((u for u in self._by_id.values() if u.firebase_uid == firebase_uid), None)

    def create(
        self,
        *,
        firebase_uid: str,
        email: str,
        display_name: str | None = None,
        is_admin: bool = False,
    ) -> User:
        now = _now()
        user = User(
            id=uuid.uuid4(),
            firebase_uid=firebase_uid,
            email=email,
            display_name=display_name,
            is_admin=is_admin,
            created_at=now,
            updated_at=now,
        )
        self._by_id[user.id] = user
        return user

    def update_display_name(self, user_id: uuid.UUID, display_name: str | None) -> User:
        existing = self._by_id[user_id]
        updated = User(
            id=existing.id,
            firebase_uid=existing.firebase_uid,
            email=existing.email,
            display_name=display_name,
            is_admin=existing.is_admin,
            created_at=existing.created_at,
            updated_at=_now(),
        )
        self._by_id[user_id] = updated
        return updated


class FakeStudentProfileRepository:
    def __init__(self) -> None:
        self._by_user: dict[uuid.UUID, StudentProfile] = {}

    def get_by_user_id(self, user_id: uuid.UUID) -> StudentProfile | None:
        return self._by_user.get(user_id)

    def create(self, *, user_id: uuid.UUID, skill_level: str = "beginner") -> StudentProfile:
        now = _now()
        profile = StudentProfile(
            id=uuid.uuid4(),
            user_id=user_id,
            skill_level=skill_level,
            created_at=now,
            updated_at=now,
        )
        self._by_user[user_id] = profile
        return profile

    def update_skill_level(self, user_id: uuid.UUID, skill_level: str) -> StudentProfile:
        existing = self._by_user[user_id]
        updated = StudentProfile(
            id=existing.id,
            user_id=existing.user_id,
            skill_level=skill_level,
            created_at=existing.created_at,
            updated_at=_now(),
        )
        self._by_user[user_id] = updated
        return updated


class FakeLanguageRepository:
    def __init__(self) -> None:
        self._items: dict[uuid.UUID, ProgrammingLanguage] = {}

    def list_all(self) -> list[ProgrammingLanguage]:
        return sorted(self._items.values(), key=lambda x: x.name)

    def get_by_id(self, language_id: uuid.UUID) -> ProgrammingLanguage | None:
        return self._items.get(language_id)

    def get_by_slug(self, slug: str) -> ProgrammingLanguage | None:
        return next((x for x in self._items.values() if x.slug == slug), None)

    def create(self, *, name: str, slug: str) -> ProgrammingLanguage:
        lang = ProgrammingLanguage(id=uuid.uuid4(), name=name, slug=slug, created_at=_now())
        self._items[lang.id] = lang
        return lang

    def update(
        self, language_id: uuid.UUID, *, name: str | None, slug: str | None
    ) -> ProgrammingLanguage:
        existing = self._items[language_id]
        updated = ProgrammingLanguage(
            id=existing.id,
            name=name if name is not None else existing.name,
            slug=slug if slug is not None else existing.slug,
            created_at=existing.created_at,
        )
        self._items[language_id] = updated
        return updated

    def delete(self, language_id: uuid.UUID) -> None:
        if language_id not in self._items:
            raise LookupError(f"Language {language_id} not found")
        del self._items[language_id]


class FakeCourseRepository:
    def __init__(self) -> None:
        self._items: dict[uuid.UUID, Course] = {}

    def list_all(self) -> list[Course]:
        return sorted(self._items.values(), key=lambda x: x.title)

    def get_by_id(self, course_id: uuid.UUID) -> Course | None:
        return self._items.get(course_id)

    def get_by_slug(self, slug: str) -> Course | None:
        return next((x for x in self._items.values() if x.slug == slug), None)

    def create(
        self, *, language_id: uuid.UUID, title: str, slug: str, description: str | None
    ) -> Course:
        now = _now()
        course = Course(
            id=uuid.uuid4(),
            language_id=language_id,
            title=title,
            slug=slug,
            description=description,
            created_at=now,
            updated_at=now,
        )
        self._items[course.id] = course
        return course

    def update(
        self,
        course_id: uuid.UUID,
        *,
        title: str | None,
        slug: str | None,
        description: str | None,
    ) -> Course:
        e = self._items[course_id]
        updated = Course(
            id=e.id,
            language_id=e.language_id,
            title=title if title is not None else e.title,
            slug=slug if slug is not None else e.slug,
            description=description if description is not None else e.description,
            created_at=e.created_at,
            updated_at=_now(),
        )
        self._items[course_id] = updated
        return updated

    def delete(self, course_id: uuid.UUID) -> None:
        if course_id not in self._items:
            raise LookupError(f"Course {course_id} not found")
        del self._items[course_id]


class FakeLessonRepository:
    def __init__(self) -> None:
        self._items: dict[uuid.UUID, Lesson] = {}

    def get_by_id(self, lesson_id: uuid.UUID) -> Lesson | None:
        return self._items.get(lesson_id)

    def list_by_course(self, course_id: uuid.UUID) -> list[Lesson]:
        items = [x for x in self._items.values() if x.course_id == course_id]
        return sorted(items, key=lambda x: (x.order_index, x.title))

    def create(
        self,
        *,
        course_id: uuid.UUID,
        title: str,
        slug: str,
        order_index: int,
        content: str,
        source: str = "human",
    ) -> Lesson:
        now = _now()
        lesson = Lesson(
            id=uuid.uuid4(),
            course_id=course_id,
            title=title,
            slug=slug,
            order_index=order_index,
            content=content,
            created_at=now,
            updated_at=now,
            source=source,
        )
        self._items[lesson.id] = lesson
        return lesson

    def update(
        self,
        lesson_id: uuid.UUID,
        *,
        title: str | None,
        slug: str | None,
        order_index: int | None,
        content: str | None,
    ) -> Lesson:
        e = self._items[lesson_id]
        updated = Lesson(
            id=e.id,
            course_id=e.course_id,
            title=title if title is not None else e.title,
            slug=slug if slug is not None else e.slug,
            order_index=order_index if order_index is not None else e.order_index,
            content=content if content is not None else e.content,
            created_at=e.created_at,
            updated_at=_now(),
        )
        self._items[lesson_id] = updated
        return updated

    def delete(self, lesson_id: uuid.UUID) -> None:
        if lesson_id not in self._items:
            raise LookupError(f"Lesson {lesson_id} not found")
        del self._items[lesson_id]


class FakeExerciseRepository:
    def __init__(self) -> None:
        self._items: dict[uuid.UUID, Exercise] = {}

    def get_by_id(self, exercise_id: uuid.UUID) -> Exercise | None:
        return self._items.get(exercise_id)

    def list_by_lesson(self, lesson_id: uuid.UUID) -> list[Exercise]:
        items = [x for x in self._items.values() if x.lesson_id == lesson_id]
        return sorted(items, key=lambda x: x.title)

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
    ) -> Exercise:
        now = _now()
        exercise = Exercise(
            id=uuid.uuid4(),
            lesson_id=lesson_id,
            language=language,
            title=title,
            slug=slug,
            prompt=prompt,
            starter_code=starter_code,
            test_spec=test_spec,
            created_at=now,
            updated_at=now,
            source=source,
        )
        self._items[exercise.id] = exercise
        return exercise

    def delete(self, exercise_id: uuid.UUID) -> None:
        if exercise_id not in self._items:
            raise LookupError(f"Exercise {exercise_id} not found")
        del self._items[exercise_id]


class FakeSubmissionRepository:
    def __init__(self) -> None:
        self._items: dict[uuid.UUID, Submission] = {}

    def get_by_id(self, submission_id: uuid.UUID) -> Submission | None:
        return self._items.get(submission_id)

    def list_for_user_and_exercise(
        self, user_id: uuid.UUID, exercise_id: uuid.UUID
    ) -> list[Submission]:
        items = [
            x
            for x in self._items.values()
            if x.user_id == user_id and x.exercise_id == exercise_id
        ]
        return sorted(items, key=lambda x: x.created_at, reverse=True)

    def create(
        self,
        *,
        user_id: uuid.UUID,
        exercise_id: uuid.UUID,
        code: str,
        status: str = "pending",
    ) -> Submission:
        now = _now()
        submission = Submission(
            id=uuid.uuid4(),
            user_id=user_id,
            exercise_id=exercise_id,
            code=code,
            status=status,
            result=None,
            created_at=now,
            updated_at=now,
        )
        self._items[submission.id] = submission
        return submission

    def update_result(
        self, submission_id: uuid.UUID, *, status: str, result: dict | None
    ) -> Submission:
        e = self._items[submission_id]
        updated = Submission(
            id=e.id,
            user_id=e.user_id,
            exercise_id=e.exercise_id,
            code=e.code,
            status=status,
            result=result,
            created_at=e.created_at,
            updated_at=_now(),
        )
        self._items[submission_id] = updated
        return updated


class FakeQuizRepository:
    def __init__(self) -> None:
        self._items: dict[uuid.UUID, Quiz] = {}

    def get_by_id(self, quiz_id: uuid.UUID) -> Quiz | None:
        return self._items.get(quiz_id)

    def list_by_lesson(self, lesson_id: uuid.UUID) -> list[Quiz]:
        items = [q for q in self._items.values() if q.lesson_id == lesson_id]
        return sorted(items, key=lambda q: q.title)

    def create(
        self, *, lesson_id: uuid.UUID, title: str, slug: str, description: str | None
    ) -> Quiz:
        now = _now()
        quiz = Quiz(
            id=uuid.uuid4(),
            lesson_id=lesson_id,
            title=title,
            slug=slug,
            description=description,
            questions=[],
            created_at=now,
            updated_at=now,
        )
        self._items[quiz.id] = quiz
        return quiz

    def add_question(
        self,
        *,
        quiz_id: uuid.UUID,
        prompt: str,
        type: str,
        order_index: int,
        choices: list[dict],
    ) -> Question:
        quiz = self._items[quiz_id]
        question_id = uuid.uuid4()
        question = Question(
            id=question_id,
            quiz_id=quiz_id,
            prompt=prompt,
            type=type,
            order_index=order_index,
            choices=[
                Choice(
                    id=uuid.uuid4(),
                    question_id=question_id,
                    text=c["text"],
                    is_correct=bool(c.get("is_correct", False)),
                    order_index=c.get("order_index", idx),
                )
                for idx, c in enumerate(choices)
            ],
        )
        # Quiz is frozen; rebuild it with the appended question.
        self._items[quiz_id] = Quiz(
            id=quiz.id,
            lesson_id=quiz.lesson_id,
            title=quiz.title,
            slug=quiz.slug,
            description=quiz.description,
            questions=[*quiz.questions, question],
            created_at=quiz.created_at,
            updated_at=_now(),
        )
        return question

    def delete(self, quiz_id: uuid.UUID) -> None:
        if quiz_id not in self._items:
            raise LookupError(f"Quiz {quiz_id} not found")
        del self._items[quiz_id]


class FakeQuizAttemptRepository:
    def __init__(self) -> None:
        self._items: dict[uuid.UUID, QuizAttempt] = {}

    def create(
        self, *, user_id: uuid.UUID, quiz_id: uuid.UUID, score: int, answers: dict
    ) -> QuizAttempt:
        now = _now()
        attempt = QuizAttempt(
            id=uuid.uuid4(),
            user_id=user_id,
            quiz_id=quiz_id,
            score=score,
            answers=answers,
            created_at=now,
            updated_at=now,
        )
        self._items[attempt.id] = attempt
        return attempt

    def list_for_user_and_quiz(
        self, user_id: uuid.UUID, quiz_id: uuid.UUID
    ) -> list[QuizAttempt]:
        items = [
            a
            for a in self._items.values()
            if a.user_id == user_id and a.quiz_id == quiz_id
        ]
        return sorted(items, key=lambda a: a.created_at, reverse=True)


class FakeAIProvider:
    """Deterministic stand-in for the Gemini provider (no network).

    Echoes request fields into the text so tests can assert the explanation /
    feedback reflects the input. Generated exercises ship a trivial test case
    (``expected=""``) that the default ``FakeCodeRunner`` passes, so the
    self-verification path succeeds unless the runner is configured to fail.
    """

    model = "fake-model"

    def teach(self, request) -> AIResponse:
        return AIResponse(
            text=f"Explanation of {request.topic}. {request.question}".strip(),
            model=self.model,
            total_tokens=5,
        )

    def tutor(self, request) -> AIResponse:
        return AIResponse(
            text=f"Hint for your {request.language} code: {request.code}",
            model=self.model,
            total_tokens=5,
        )

    def generate_lesson(self, request) -> GeneratedLesson:
        return GeneratedLesson(
            title=f"Lesson: {request.topic}",
            content=f"# {request.topic}\n\nGenerated content.",
            model=self.model,
            total_tokens=7,
        )

    def generate_exercise(self, request) -> GeneratedExercise:
        return GeneratedExercise(
            title=f"Exercise: {request.topic}",
            prompt=f"Solve: {request.topic}",
            starter_code="# your code here\n",
            reference_solution="pass\n",
            test_spec={"cases": [{"input": "", "expected": ""}]},
            model=self.model,
            total_tokens=9,
        )


class FakeAIInteractionRepository:
    def __init__(self) -> None:
        self._items: list[AIInteraction] = []

    def create(
        self, *, user_id: uuid.UUID, kind: str, model: str, total_tokens: int
    ) -> AIInteraction:
        record = AIInteraction(
            id=uuid.uuid4(),
            user_id=user_id,
            kind=kind,
            model=model,
            total_tokens=total_tokens,
            created_at=_now(),
        )
        self._items.append(record)
        return record

    def count_since(self, user_id: uuid.UUID, since: datetime) -> int:
        return sum(
            1 for r in self._items if r.user_id == user_id and r.created_at >= since
        )
