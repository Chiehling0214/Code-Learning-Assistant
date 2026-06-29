"""Seed the database with sample content.

Idempotent: safe to run repeatedly (rows are keyed by slug). Run with:

    python -m scripts.seed            # from the backend/ directory
"""

from __future__ import annotations

from app.infrastructure.db.session import SessionLocal
from app.infrastructure.models.models import Course, Exercise, Lesson, ProgrammingLanguage
from sqlalchemy import select
from sqlalchemy.orm import Session

LANGUAGE = {"name": "Python", "slug": "python"}
COURSE = {
    "title": "Python Basics",
    "slug": "python-basics",
    "description": "Get started with Python: variables, control flow, and functions.",
}
LESSONS = [
    {
        "title": "Variables & Types",
        "slug": "variables-and-types",
        "order_index": 1,
        "content": (
            "# Variables & Types\n\n"
            "In Python, variables are created on assignment:\n\n"
            "```python\nname = \"Ada\"\nage = 36\n```\n"
        ),
    },
    {
        "title": "Control Flow",
        "slug": "control-flow",
        "order_index": 2,
        "content": (
            "# Control Flow\n\n"
            "Use `if`/`elif`/`else` to branch:\n\n"
            "```python\nif age >= 18:\n    print(\"adult\")\n```\n"
        ),
    },
    {
        "title": "Functions",
        "slug": "functions",
        "order_index": 3,
        "content": (
            "# Functions\n\n"
            "Define reusable logic with `def`:\n\n"
            "```python\ndef greet(name):\n    return f\"Hello, {name}!\"\n```\n"
        ),
    },
]


def _get_or_create_language(session: Session) -> ProgrammingLanguage:
    language = session.scalars(
        select(ProgrammingLanguage).where(ProgrammingLanguage.slug == LANGUAGE["slug"])
    ).first()
    if language is None:
        language = ProgrammingLanguage(**LANGUAGE)
        session.add(language)
        session.flush()
    return language


def _get_or_create_course(session: Session, language: ProgrammingLanguage) -> Course:
    course = session.scalars(select(Course).where(Course.slug == COURSE["slug"])).first()
    if course is None:
        course = Course(language_id=language.id, **COURSE)
        session.add(course)
        session.flush()
    return course


EXERCISE = {
    "lesson_slug": "variables-and-types",
    "slug": "hello-codepath",
    "title": "Hello, CodePath",
    "language": "python",
    "prompt": 'Write a function `solution()` that returns the string "Hello, CodePath!".',
    "starter_code": "def solution():\n    # your code here\n    pass\n\n\nprint(solution())\n",
    "test_spec": {"cases": [{"input": "", "expected": "Hello, CodePath!"}]},
}


def _seed_lessons(session: Session, course: Course) -> int:
    created = 0
    for data in LESSONS:
        exists = session.scalars(
            select(Lesson).where(Lesson.course_id == course.id, Lesson.slug == data["slug"])
        ).first()
        if exists is None:
            session.add(Lesson(course_id=course.id, **data))
            created += 1
    return created


def _seed_exercise(session: Session, course: Course) -> int:
    lesson = session.scalars(
        select(Lesson).where(
            Lesson.course_id == course.id, Lesson.slug == EXERCISE["lesson_slug"]
        )
    ).first()
    if lesson is None:
        return 0
    exists = session.scalars(
        select(Exercise).where(
            Exercise.lesson_id == lesson.id, Exercise.slug == EXERCISE["slug"]
        )
    ).first()
    if exists is not None:
        return 0
    session.add(
        Exercise(
            lesson_id=lesson.id,
            slug=EXERCISE["slug"],
            title=EXERCISE["title"],
            language=EXERCISE["language"],
            prompt=EXERCISE["prompt"],
            starter_code=EXERCISE["starter_code"],
            test_spec=EXERCISE["test_spec"],
        )
    )
    return 1


def seed() -> None:
    session = SessionLocal()
    try:
        language = _get_or_create_language(session)
        course = _get_or_create_course(session, language)
        created = _seed_lessons(session, course)
        session.flush()  # ensure lessons have ids before attaching an exercise
        exercises = _seed_exercise(session, course)
        session.commit()
        print(
            f"Seeded language '{language.slug}', course '{course.slug}', "
            f"{created} new lesson(s), {exercises} new exercise(s)."
        )
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    seed()
