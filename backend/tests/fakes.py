"""In-memory fake repositories for tests (no database required)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from app.application.ports.ai_provider import (
    AIResponse,
    GeneratedExercise,
    GeneratedLesson,
    GeneratedLessonBatch,
    GeneratedLessonPack,
    GeneratedPlacement,
    GeneratedSyllabus,
)
from app.domain.entities import (
    AIInteraction,
    Choice,
    Course,
    CourseChatMessage,
    Exercise,
    GenerationJob,
    LanguageTrack,
    Lesson,
    PlacementAssessment,
    ProgrammingLanguage,
    ProgressEvent,
    Question,
    Quiz,
    QuizAttempt,
    ReviewItem,
    StudentProfile,
    Submission,
    Subscription,
    User,
)
from app.infrastructure.billing.stripe_client import (
    CheckoutSession,
    RetrievedSession,
    StripeError,
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

    def list_by_track_ids(self, track_ids: list[uuid.UUID]) -> list[Course]:
        ids = set(track_ids)
        items = [c for c in self._items.values() if c.track_id in ids]
        return sorted(items, key=lambda x: x.created_at)

    def get_by_id(self, course_id: uuid.UUID) -> Course | None:
        return self._items.get(course_id)

    def get_by_slug(self, slug: str) -> Course | None:
        return next((x for x in self._items.values() if x.slug == slug), None)

    def create(
        self,
        *,
        language_id: uuid.UUID,
        title: str,
        slug: str,
        description: str | None,
        track_id: uuid.UUID | None = None,
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
            track_id=track_id,
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

    def list_by_source(self, source: str) -> list[Lesson]:
        items = [x for x in self._items.values() if x.source == source]
        return sorted(items, key=lambda x: x.created_at, reverse=True)

    def create(
        self,
        *,
        course_id: uuid.UUID,
        title: str,
        slug: str,
        order_index: int,
        content: str,
        source: str = "human",
        review_status: str = "approved",
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
            review_status=review_status,
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
            source=e.source,
            review_status=e.review_status,
        )
        self._items[lesson_id] = updated
        return updated

    def set_review_status(self, lesson_id: uuid.UUID, review_status: str) -> Lesson:
        e = self._items[lesson_id]
        updated = Lesson(
            id=e.id,
            course_id=e.course_id,
            title=e.title,
            slug=e.slug,
            order_index=e.order_index,
            content=e.content,
            created_at=e.created_at,
            updated_at=_now(),
            source=e.source,
            review_status=review_status,
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
        explanation: str = "",
    ) -> Question:
        quiz = self._items[quiz_id]
        question_id = uuid.uuid4()
        question = Question(
            id=question_id,
            quiz_id=quiz_id,
            prompt=prompt,
            type=type,
            order_index=order_index,
            explanation=explanation,
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

    def generate_syllabus(self, request) -> GeneratedSyllabus:
        topics = [f"{request.language} topic {i + 1}" for i in range(request.lesson_count)]
        return GeneratedSyllabus(topics=topics, model=self.model, total_tokens=6)

    def generate_lesson_pack(self, request) -> GeneratedLessonPack:
        return GeneratedLessonPack(
            title=request.topic,
            content=f"# {request.topic}\n\nContent.",
            exercises=[
                {
                    "title": f"{request.topic} ex{i + 1}",
                    "prompt": "Solve it",
                    "starter_code": "# start\n",
                    "reference_solution": "pass\n",
                    "test_spec": {"cases": [{"input": "", "expected": ""}]},
                }
                for i in range(request.exercise_count)
            ],
            quiz={
                "title": f"{request.topic} quiz",
                "questions": [
                    {
                        "prompt": "Q?",
                        "choices": [
                            {"text": "A", "is_correct": True},
                            {"text": "B", "is_correct": False},
                        ],
                        "explanation": "A is correct.",
                    }
                    for _ in range(request.quiz_question_count)
                ],
            },
            model=self.model,
            total_tokens=12,
        )

    def generate_lesson_batch(self, request) -> GeneratedLessonBatch:
        start = len(request.prior_titles)
        # Echo the focus into titles so tests can assert targeting.
        base = request.focus.strip() or f"{request.language} lesson"
        lessons = [
            {
                "title": f"{base} {start + n + 1}",
                "content": "# Lesson\n\nContent.",
                "exercises": [
                    {
                        "title": f"ex{i + 1}",
                        "prompt": "Solve it",
                        "starter_code": "# start\n",
                        "reference_solution": "pass\n",
                        "test_spec": {"cases": [{"input": "", "expected": ""}]},
                    }
                    for i in range(request.exercise_count)
                ],
                "quiz": {
                    "title": "quiz",
                    "questions": [
                        {
                            "prompt": "Q?",
                            "choices": [
                                {"text": "A", "is_correct": True},
                                {"text": "B", "is_correct": False},
                            ],
                            "explanation": "A is correct.",
                        }
                        for _ in range(request.quiz_question_count)
                    ],
                },
            }
            for n in range(request.count)
        ]
        return GeneratedLessonBatch(lessons=lessons, model=self.model, total_tokens=20)

    def generate_placement(self, request) -> GeneratedPlacement:
        # 2 MCQs (first choice correct) + 1 coding task whose reference passes the
        # default FakeCodeRunner (stdout "" == expected "").
        return GeneratedPlacement(
            mcqs=[
                {
                    "prompt": "Q1",
                    "choices": [
                        {"text": "A", "is_correct": True},
                        {"text": "B", "is_correct": False},
                    ],
                    "explanation": "A is correct because …",
                },
                {
                    "prompt": "Q2",
                    "choices": [
                        {"text": "C", "is_correct": True},
                        {"text": "D", "is_correct": False},
                    ],
                    "explanation": "C is correct because …",
                },
            ],
            coding=[
                {
                    "prompt": "Print nothing",
                    "language": request.language,
                    "starter_code": "# start\n",
                    "reference_solution": "pass\n",
                    "test_spec": {"cases": [{"input": "", "expected": ""}]},
                }
            ],
            model=self.model,
            total_tokens=11,
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

    def count_since(
        self, user_id: uuid.UUID, since: datetime, *, kind: str | None = None
    ) -> int:
        return sum(
            1
            for r in self._items
            if r.user_id == user_id
            and r.created_at >= since
            and (kind is None or r.kind == kind)
        )


class FakeProgressRepository:
    def __init__(self) -> None:
        self._items: list[ProgressEvent] = []

    def record(
        self,
        *,
        user_id: uuid.UUID,
        item_type: str,
        item_id: uuid.UUID,
        status: str,
        score: int | None = None,
    ) -> ProgressEvent:
        event = ProgressEvent(
            id=uuid.uuid4(),
            user_id=user_id,
            item_type=item_type,
            item_id=item_id,
            status=status,
            score=score,
            completed_at=_now(),
        )
        self._items.append(event)
        return event

    def list_for_user(self, user_id: uuid.UUID) -> list[ProgressEvent]:
        items = [e for e in self._items if e.user_id == user_id]
        return sorted(items, key=lambda e: e.completed_at, reverse=True)


class FakeSubscriptionRepository:
    def __init__(self) -> None:
        self._by_user: dict[uuid.UUID, Subscription] = {}

    def get_by_user_id(self, user_id: uuid.UUID) -> Subscription | None:
        return self._by_user.get(user_id)

    def upsert(
        self,
        *,
        user_id: uuid.UUID,
        plan: str,
        status: str,
        stripe_customer_id: str | None = None,
        stripe_subscription_id: str | None = None,
        current_period_end: datetime | None = None,
    ) -> Subscription:
        existing = self._by_user.get(user_id)
        now = _now()
        sub = Subscription(
            id=existing.id if existing else uuid.uuid4(),
            user_id=user_id,
            plan=plan,
            status=status,
            stripe_customer_id=stripe_customer_id
            or (existing.stripe_customer_id if existing else None),
            stripe_subscription_id=stripe_subscription_id
            or (existing.stripe_subscription_id if existing else None),
            current_period_end=current_period_end,
            created_at=existing.created_at if existing else now,
            updated_at=now,
        )
        self._by_user[user_id] = sub
        return sub


class FakeStripeClient:
    """Deterministic Stripe stand-in: no network, no signature checking."""

    def __init__(self) -> None:
        self.checkout_url = "https://stripe.test/checkout/session_abc"
        self.last_client_reference_id: str | None = None
        self.next_event: dict | None = None
        self.raise_on_construct = False
        # Tunables for retrieve_checkout_session (webhook-free confirm path).
        self.retrieve_client_reference_id: str | None = None  # None → the last checkout
        self.retrieve_payment_status = "paid"
        self.retrieve_status = "complete"

    def create_checkout_session(
        self, *, customer_email: str, client_reference_id: str
    ) -> CheckoutSession:
        self.last_client_reference_id = client_reference_id
        return CheckoutSession(id="cs_test_123", url=self.checkout_url)

    def retrieve_checkout_session(self, session_id: str) -> RetrievedSession:
        ref = self.retrieve_client_reference_id
        if ref is None:
            ref = self.last_client_reference_id
        return RetrievedSession(
            client_reference_id=ref,
            payment_status=self.retrieve_payment_status,
            status=self.retrieve_status,
            customer="cus_test_1",
            subscription="sub_test_1",
        )

    def construct_event(self, payload: bytes, signature: str) -> dict:
        if self.raise_on_construct:
            raise StripeError("Invalid webhook signature")
        return self.next_event or {}


class FakeLanguageTrackRepository:
    def __init__(self) -> None:
        self._items: dict[uuid.UUID, LanguageTrack] = {}

    def get_by_id(self, track_id: uuid.UUID) -> LanguageTrack | None:
        return self._items.get(track_id)

    def list_by_user(self, user_id: uuid.UUID) -> list[LanguageTrack]:
        items = [t for t in self._items.values() if t.user_id == user_id]
        return sorted(items, key=lambda t: t.created_at)

    def get_by_user_and_language(
        self, user_id: uuid.UUID, language_id: uuid.UUID
    ) -> LanguageTrack | None:
        return next(
            (
                t
                for t in self._items.values()
                if t.user_id == user_id and t.language_id == language_id
            ),
            None,
        )

    def count_by_user(self, user_id: uuid.UUID) -> int:
        return sum(1 for t in self._items.values() if t.user_id == user_id)

    def create(
        self, *, user_id: uuid.UUID, language_id: uuid.UUID, status: str = "active"
    ) -> LanguageTrack:
        now = _now()
        track = LanguageTrack(
            id=uuid.uuid4(),
            user_id=user_id,
            language_id=language_id,
            level=None,
            status=status,
            created_at=now,
            updated_at=now,
        )
        self._items[track.id] = track
        return track

    def set_level(self, track_id: uuid.UUID, level: str) -> LanguageTrack:
        e = self._items[track_id]
        updated = LanguageTrack(
            id=e.id,
            user_id=e.user_id,
            language_id=e.language_id,
            level=level,
            status="active",
            created_at=e.created_at,
            updated_at=_now(),
        )
        self._items[track_id] = updated
        return updated

    def delete(self, track_id: uuid.UUID) -> None:
        if track_id not in self._items:
            raise LookupError(f"Track {track_id} not found")
        del self._items[track_id]


class FakeGenerationJobRepository:
    def __init__(self) -> None:
        self._items: dict[uuid.UUID, GenerationJob] = {}

    def get_by_id(self, job_id: uuid.UUID) -> GenerationJob | None:
        return self._items.get(job_id)

    def get_latest_for_track(self, track_id: uuid.UUID) -> GenerationJob | None:
        items = [j for j in self._items.values() if j.track_id == track_id]
        return max(items, key=lambda j: j.created_at) if items else None

    def create(self, *, track_id: uuid.UUID, user_id: uuid.UUID, total: int) -> GenerationJob:
        now = _now()
        job = GenerationJob(
            id=uuid.uuid4(),
            track_id=track_id,
            user_id=user_id,
            status="pending",
            total=total,
            completed=0,
            course_id=None,
            error=None,
            created_at=now,
            updated_at=now,
        )
        self._items[job.id] = job
        return job

    def update(
        self,
        job_id: uuid.UUID,
        *,
        status: str | None = None,
        completed: int | None = None,
        course_id: uuid.UUID | None = None,
        error: str | None = None,
    ) -> GenerationJob:
        e = self._items[job_id]
        updated = GenerationJob(
            id=e.id,
            track_id=e.track_id,
            user_id=e.user_id,
            status=status if status is not None else e.status,
            total=e.total,
            completed=completed if completed is not None else e.completed,
            course_id=course_id if course_id is not None else e.course_id,
            error=error if error is not None else e.error,
            created_at=e.created_at,
            updated_at=_now(),
        )
        self._items[job_id] = updated
        return updated


class FakePlacementRepository:
    def __init__(self) -> None:
        self._items: dict[uuid.UUID, PlacementAssessment] = {}

    def get_by_track(self, track_id: uuid.UUID) -> PlacementAssessment | None:
        return next((p for p in self._items.values() if p.track_id == track_id), None)

    def create(
        self, *, track_id: uuid.UUID, user_id: uuid.UUID, items: dict
    ) -> PlacementAssessment:
        now = _now()
        placement = PlacementAssessment(
            id=uuid.uuid4(),
            track_id=track_id,
            user_id=user_id,
            status="ready",
            items=items,
            result=None,
            score=None,
            level=None,
            created_at=now,
            updated_at=now,
        )
        self._items[placement.id] = placement
        return placement

    def save_result(
        self, assessment_id: uuid.UUID, *, result: dict, score: int, level: str
    ) -> PlacementAssessment:
        e = self._items[assessment_id]
        updated = PlacementAssessment(
            id=e.id,
            track_id=e.track_id,
            user_id=e.user_id,
            status="completed",
            items=e.items,
            result=result,
            score=score,
            level=level,
            created_at=e.created_at,
            updated_at=_now(),
        )
        self._items[assessment_id] = updated
        return updated


class FakeReviewItemRepository:
    def __init__(self) -> None:
        self._items: dict[uuid.UUID, ReviewItem] = {}

    def get_by_id(self, item_id: uuid.UUID) -> ReviewItem | None:
        return self._items.get(item_id)

    def get_by_user_and_ref(
        self, user_id: uuid.UUID, item_ref: uuid.UUID
    ) -> ReviewItem | None:
        return next(
            (
                i
                for i in self._items.values()
                if i.user_id == user_id and i.item_ref == item_ref
            ),
            None,
        )

    def list_due(self, user_id: uuid.UUID, now: datetime) -> list[ReviewItem]:
        items = [
            i
            for i in self._items.values()
            if i.user_id == user_id and not i.retired and i.due_at <= now
        ]
        return sorted(items, key=lambda i: i.due_at)

    def count_due(self, user_id: uuid.UUID, now: datetime) -> int:
        return len(self.list_due(user_id, now))

    def list_all(self, user_id: uuid.UUID) -> list[ReviewItem]:
        items = [i for i in self._items.values() if i.user_id == user_id]
        return sorted(items, key=lambda i: (i.retired, i.due_at))

    def create(
        self,
        *,
        user_id: uuid.UUID,
        source: str,
        item_ref: uuid.UUID,
        payload: dict,
        interval_days: int,
        due_at: datetime,
    ) -> ReviewItem:
        now = _now()
        item = ReviewItem(
            id=uuid.uuid4(),
            user_id=user_id,
            source=source,
            item_ref=item_ref,
            payload=payload,
            interval_days=interval_days,
            due_at=due_at,
            lapses=0,
            passes=0,
            retired=False,
            created_at=now,
            updated_at=now,
        )
        self._items[item.id] = item
        return item

    def update(
        self,
        item_id: uuid.UUID,
        *,
        payload: dict | None = None,
        interval_days: int | None = None,
        due_at: datetime | None = None,
        lapses: int | None = None,
        passes: int | None = None,
        retired: bool | None = None,
    ) -> ReviewItem:
        e = self._items[item_id]
        updated = ReviewItem(
            id=e.id,
            user_id=e.user_id,
            source=e.source,
            item_ref=e.item_ref,
            payload=payload if payload is not None else e.payload,
            interval_days=interval_days if interval_days is not None else e.interval_days,
            due_at=due_at if due_at is not None else e.due_at,
            lapses=lapses if lapses is not None else e.lapses,
            passes=passes if passes is not None else e.passes,
            retired=retired if retired is not None else e.retired,
            created_at=e.created_at,
            updated_at=_now(),
        )
        self._items[item_id] = updated
        return updated


class FakeCourseChatRepository:
    def __init__(self) -> None:
        self._items: list[CourseChatMessage] = []

    def list_by_course_and_user(
        self, course_id: uuid.UUID, user_id: uuid.UUID
    ) -> list[CourseChatMessage]:
        items = [
            m for m in self._items if m.course_id == course_id and m.user_id == user_id
        ]
        return sorted(items, key=lambda m: m.created_at)

    def create(
        self, *, course_id: uuid.UUID, user_id: uuid.UUID, role: str, content: str
    ) -> CourseChatMessage:
        message = CourseChatMessage(
            id=uuid.uuid4(),
            course_id=course_id,
            user_id=user_id,
            role=role,
            content=content,
            created_at=_now(),
        )
        self._items.append(message)
        return message
