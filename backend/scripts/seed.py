"""Seed the database with sample content.

Idempotent: safe to run repeatedly (rows are keyed by slug). Data-driven — each
entry in ``PACKS`` is a language with a starter course (lessons + an exercise +
a quiz). Run with:

    python -m scripts.seed            # from the backend/ directory
"""

from __future__ import annotations

from typing import Any

from app.infrastructure.db.session import SessionLocal
from app.infrastructure.models.models import (
    Choice,
    Course,
    Exercise,
    Lesson,
    ProgrammingLanguage,
    Question,
    Quiz,
)
from sqlalchemy import select
from sqlalchemy.orm import Session

# --------------------------------------------------------------------------- #
# Content packs
# --------------------------------------------------------------------------- #

PYTHON_PACK: dict[str, Any] = {
    "language": {"name": "Python", "slug": "python"},
    "course": {
        "title": "Python Basics",
        "slug": "python-basics",
        "description": "Get started with Python: variables, control flow, and functions.",
    },
    "lessons": [
        {
            "title": "Variables & Types",
            "slug": "variables-and-types",
            "order_index": 1,
            "content": (
                "# Variables & Types\n\n"
                "In Python, variables are created on assignment:\n\n"
                '```python\nname = "Ada"\nage = 36\n```\n'
            ),
        },
        {
            "title": "Control Flow",
            "slug": "control-flow",
            "order_index": 2,
            "content": (
                "# Control Flow\n\n"
                "Use `if`/`elif`/`else` to branch:\n\n"
                '```python\nif age >= 18:\n    print("adult")\n```\n'
            ),
        },
        {
            "title": "Functions",
            "slug": "functions",
            "order_index": 3,
            "content": (
                "# Functions\n\n"
                "Define reusable logic with `def`:\n\n"
                '```python\ndef greet(name):\n    return f"Hello, {name}!"\n```\n'
            ),
        },
    ],
    "exercise": {
        "lesson_slug": "variables-and-types",
        "slug": "hello-codepath",
        "title": "Hello, CodePath",
        "language": "python",
        "prompt": 'Write a function `solution()` that returns the string "Hello, CodePath!".',
        "starter_code": "def solution():\n    # your code here\n    pass\n\n\nprint(solution())\n",
        "test_spec": {"cases": [{"input": "", "expected": "Hello, CodePath!"}]},
    },
    "quiz": {
        "lesson_slug": "control-flow",
        "slug": "control-flow-check",
        "title": "Control Flow Check",
        "description": "A quick check on Python control flow.",
        "questions": [
            {
                "prompt": "Which keyword starts a conditional branch in Python?",
                "choices": [
                    {"text": "if", "is_correct": True},
                    {"text": "when", "is_correct": False},
                    {"text": "switch", "is_correct": False},
                ],
            },
            {
                "prompt": "What does `else` do?",
                "choices": [
                    {"text": "Runs when no preceding condition matched", "is_correct": True},
                    {"text": "Repeats the loop", "is_correct": False},
                    {"text": "Defines a function", "is_correct": False},
                ],
            },
        ],
    },
}

CPP_PACK: dict[str, Any] = {
    "language": {"name": "C++", "slug": "cpp"},
    "course": {
        "title": "C++ Basics",
        "slug": "cpp-basics",
        "description": "Get started with C++: I/O, variables, and control flow.",
    },
    "lessons": [
        {
            "title": "Hello, World & I/O",
            "slug": "hello-world-io",
            "order_index": 1,
            "content": (
                "# Hello, World & I/O\n\n"
                "A C++ program starts at `main`. Print with `std::cout`:\n\n"
                '```cpp\n#include <iostream>\n\nint main() {\n'
                '    std::cout << "Hello, World!";\n    return 0;\n}\n```\n'
            ),
        },
        {
            "title": "Variables & Types",
            "slug": "variables-and-types",
            "order_index": 2,
            "content": (
                "# Variables & Types\n\n"
                "C++ is statically typed — declare a type with each variable:\n\n"
                '```cpp\nint age = 36;\nstd::string name = "Ada";\ndouble pi = 3.14;\n```\n'
            ),
        },
        {
            "title": "Control Flow",
            "slug": "control-flow",
            "order_index": 3,
            "content": (
                "# Control Flow\n\n"
                "Branch with `if`/`else if`/`else`, and loop with `for`/`while`:\n\n"
                '```cpp\nif (age >= 18) {\n    std::cout << "adult";\n}\n```\n'
            ),
        },
    ],
    "exercise": {
        "lesson_slug": "hello-world-io",
        "slug": "cpp-hello-codepath",
        "title": "Hello, CodePath (C++)",
        "language": "cpp",
        "prompt": 'Print the string "Hello, CodePath!" to standard output.',
        "starter_code": (
            "#include <iostream>\n\nint main() {\n"
            "    // your code here\n    return 0;\n}\n"
        ),
        "test_spec": {"cases": [{"input": "", "expected": "Hello, CodePath!"}]},
    },
    "quiz": {
        "lesson_slug": "control-flow",
        "slug": "cpp-basics-check",
        "title": "C++ Basics Check",
        "description": "A quick check on C++ fundamentals.",
        "questions": [
            {
                "prompt": "Which stream prints to standard output in C++?",
                "choices": [
                    {"text": "std::cout", "is_correct": True},
                    {"text": "std::cin", "is_correct": False},
                    {"text": "print()", "is_correct": False},
                ],
            },
            {
                "prompt": "How do you declare an integer variable?",
                "choices": [
                    {"text": "int x = 5;", "is_correct": True},
                    {"text": "x = 5", "is_correct": False},
                    {"text": "let x = 5;", "is_correct": False},
                ],
            },
        ],
    },
}

PACKS: list[dict[str, Any]] = [PYTHON_PACK, CPP_PACK]


# --------------------------------------------------------------------------- #
# Idempotent seeding (rows keyed by slug)
# --------------------------------------------------------------------------- #


def _get_or_create_language(session: Session, data: dict) -> ProgrammingLanguage:
    language = session.scalars(
        select(ProgrammingLanguage).where(ProgrammingLanguage.slug == data["slug"])
    ).first()
    if language is None:
        language = ProgrammingLanguage(**data)
        session.add(language)
        session.flush()
    return language


def _get_or_create_course(session: Session, language: ProgrammingLanguage, data: dict) -> Course:
    course = session.scalars(select(Course).where(Course.slug == data["slug"])).first()
    if course is None:
        course = Course(language_id=language.id, **data)
        session.add(course)
        session.flush()
    return course


def _seed_lessons(session: Session, course: Course, lessons: list[dict]) -> int:
    created = 0
    for data in lessons:
        exists = session.scalars(
            select(Lesson).where(Lesson.course_id == course.id, Lesson.slug == data["slug"])
        ).first()
        if exists is None:
            session.add(Lesson(course_id=course.id, **data))
            created += 1
    return created


def _seed_exercise(session: Session, course: Course, ex: dict | None) -> int:
    if not ex:
        return 0
    lesson = session.scalars(
        select(Lesson).where(Lesson.course_id == course.id, Lesson.slug == ex["lesson_slug"])
    ).first()
    if lesson is None:
        return 0
    exists = session.scalars(
        select(Exercise).where(Exercise.lesson_id == lesson.id, Exercise.slug == ex["slug"])
    ).first()
    if exists is not None:
        return 0
    session.add(
        Exercise(
            lesson_id=lesson.id,
            slug=ex["slug"],
            title=ex["title"],
            language=ex["language"],
            prompt=ex["prompt"],
            starter_code=ex["starter_code"],
            test_spec=ex["test_spec"],
        )
    )
    return 1


def _seed_quiz(session: Session, course: Course, quiz: dict | None) -> int:
    if not quiz:
        return 0
    lesson = session.scalars(
        select(Lesson).where(Lesson.course_id == course.id, Lesson.slug == quiz["lesson_slug"])
    ).first()
    if lesson is None:
        return 0
    exists = session.scalars(
        select(Quiz).where(Quiz.lesson_id == lesson.id, Quiz.slug == quiz["slug"])
    ).first()
    if exists is not None:
        return 0
    model = Quiz(
        lesson_id=lesson.id,
        slug=quiz["slug"],
        title=quiz["title"],
        description=quiz["description"],
    )
    for order, q in enumerate(quiz["questions"]):
        question = Question(prompt=q["prompt"], type="single", order_index=order)
        for choice_order, c in enumerate(q["choices"]):
            question.choices.append(
                Choice(text=c["text"], is_correct=c["is_correct"], order_index=choice_order)
            )
        model.questions.append(question)
    session.add(model)
    return 1


def _seed_pack(session: Session, pack: dict) -> tuple[str, int, int, int]:
    language = _get_or_create_language(session, pack["language"])
    course = _get_or_create_course(session, language, pack["course"])
    lessons = _seed_lessons(session, course, pack["lessons"])
    session.flush()  # ensure lessons have ids before attaching content
    exercises = _seed_exercise(session, course, pack.get("exercise"))
    quizzes = _seed_quiz(session, course, pack.get("quiz"))
    return language.slug, lessons, exercises, quizzes


def seed() -> None:
    session = SessionLocal()
    try:
        for pack in PACKS:
            slug, lessons, exercises, quizzes = _seed_pack(session, pack)
            print(
                f"Seeded '{slug}': {lessons} new lesson(s), "
                f"{exercises} new exercise(s), {quizzes} new quiz(zes)."
            )
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    seed()
