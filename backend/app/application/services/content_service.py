"""Content use cases: languages, courses, and lessons.

Read operations for learners and full CRUD for admins. Depends only on the
domain repository interfaces. Raises :class:`LookupError` when an entity is
missing; the API layer maps that to ``404``.
"""

from __future__ import annotations

import uuid

from app.domain.entities import Course, Lesson, ProgrammingLanguage
from app.domain.repositories import (
    CourseRepository,
    LanguageRepository,
    LessonRepository,
)


class ContentService:
    def __init__(
        self,
        languages: LanguageRepository,
        courses: CourseRepository,
        lessons: LessonRepository,
    ) -> None:
        self._languages = languages
        self._courses = courses
        self._lessons = lessons

    # ----- Languages -----
    def list_languages(self) -> list[ProgrammingLanguage]:
        return self._languages.list_all()

    def create_language(self, *, name: str, slug: str) -> ProgrammingLanguage:
        return self._languages.create(name=name, slug=slug)

    def update_language(
        self, language_id: uuid.UUID, *, name: str | None, slug: str | None
    ) -> ProgrammingLanguage:
        return self._languages.update(language_id, name=name, slug=slug)

    def delete_language(self, language_id: uuid.UUID) -> None:
        self._languages.delete(language_id)

    # ----- Courses -----
    def list_courses(self) -> list[Course]:
        return self._courses.list_all()

    def get_course_by_slug(self, slug: str) -> Course:
        course = self._courses.get_by_slug(slug)
        if course is None:
            raise LookupError(f"Course '{slug}' not found")
        return course

    def list_lessons_for_course(self, course_id: uuid.UUID) -> list[Lesson]:
        return self._lessons.list_by_course(course_id)

    def create_course(
        self, *, language_id: uuid.UUID, title: str, slug: str, description: str | None
    ) -> Course:
        if self._languages.get_by_id(language_id) is None:
            raise LookupError(f"Language {language_id} not found")
        return self._courses.create(
            language_id=language_id, title=title, slug=slug, description=description
        )

    def update_course(
        self,
        course_id: uuid.UUID,
        *,
        title: str | None,
        slug: str | None,
        description: str | None,
    ) -> Course:
        return self._courses.update(
            course_id, title=title, slug=slug, description=description
        )

    def delete_course(self, course_id: uuid.UUID) -> None:
        self._courses.delete(course_id)

    # ----- Lessons -----
    def get_lesson(self, lesson_id: uuid.UUID) -> Lesson:
        lesson = self._lessons.get_by_id(lesson_id)
        if lesson is None:
            raise LookupError(f"Lesson {lesson_id} not found")
        return lesson

    def create_lesson(
        self,
        *,
        course_id: uuid.UUID,
        title: str,
        slug: str,
        order_index: int,
        content: str,
    ) -> Lesson:
        if self._courses.get_by_id(course_id) is None:
            raise LookupError(f"Course {course_id} not found")
        return self._lessons.create(
            course_id=course_id,
            title=title,
            slug=slug,
            order_index=order_index,
            content=content,
        )

    def update_lesson(
        self,
        lesson_id: uuid.UUID,
        *,
        title: str | None,
        slug: str | None,
        order_index: int | None,
        content: str | None,
    ) -> Lesson:
        return self._lessons.update(
            lesson_id,
            title=title,
            slug=slug,
            order_index=order_index,
            content=content,
        )

    def delete_lesson(self, lesson_id: uuid.UUID) -> None:
        self._lessons.delete(lesson_id)
