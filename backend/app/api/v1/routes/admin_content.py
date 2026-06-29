"""Admin CRUD endpoints for content (languages, courses, lessons).

The whole router requires an admin user via the ``require_admin`` dependency,
so non-admins receive ``403`` on every endpoint here.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import ContentServiceDep, require_admin
from app.schemas.content import (
    CourseCreate,
    CourseResponse,
    CourseUpdate,
    LanguageCreate,
    LanguageResponse,
    LanguageUpdate,
    LessonCreate,
    LessonResponse,
    LessonUpdate,
)

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])


def _not_found(exc: LookupError) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


# --------------------------------------------------------------------------- #
# Languages
# --------------------------------------------------------------------------- #


@router.post("/languages", response_model=LanguageResponse, status_code=status.HTTP_201_CREATED)
def create_language(payload: LanguageCreate, service: ContentServiceDep) -> LanguageResponse:
    lang = service.create_language(name=payload.name, slug=payload.slug)
    return LanguageResponse(id=lang.id, name=lang.name, slug=lang.slug)


@router.put("/languages/{language_id}", response_model=LanguageResponse)
def update_language(
    language_id: uuid.UUID, payload: LanguageUpdate, service: ContentServiceDep
) -> LanguageResponse:
    try:
        lang = service.update_language(language_id, name=payload.name, slug=payload.slug)
    except LookupError as exc:
        raise _not_found(exc) from exc
    return LanguageResponse(id=lang.id, name=lang.name, slug=lang.slug)


@router.delete("/languages/{language_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_language(language_id: uuid.UUID, service: ContentServiceDep) -> None:
    try:
        service.delete_language(language_id)
    except LookupError as exc:
        raise _not_found(exc) from exc


# --------------------------------------------------------------------------- #
# Courses
# --------------------------------------------------------------------------- #


@router.post("/courses", response_model=CourseResponse, status_code=status.HTTP_201_CREATED)
def create_course(payload: CourseCreate, service: ContentServiceDep) -> CourseResponse:
    try:
        course = service.create_course(
            language_id=payload.language_id,
            title=payload.title,
            slug=payload.slug,
            description=payload.description,
        )
    except LookupError as exc:
        raise _not_found(exc) from exc
    return CourseResponse(
        id=course.id,
        language_id=course.language_id,
        title=course.title,
        slug=course.slug,
        description=course.description,
    )


@router.put("/courses/{course_id}", response_model=CourseResponse)
def update_course(
    course_id: uuid.UUID, payload: CourseUpdate, service: ContentServiceDep
) -> CourseResponse:
    try:
        course = service.update_course(
            course_id,
            title=payload.title,
            slug=payload.slug,
            description=payload.description,
        )
    except LookupError as exc:
        raise _not_found(exc) from exc
    return CourseResponse(
        id=course.id,
        language_id=course.language_id,
        title=course.title,
        slug=course.slug,
        description=course.description,
    )


@router.delete("/courses/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_course(course_id: uuid.UUID, service: ContentServiceDep) -> None:
    try:
        service.delete_course(course_id)
    except LookupError as exc:
        raise _not_found(exc) from exc


# --------------------------------------------------------------------------- #
# Lessons
# --------------------------------------------------------------------------- #


def _lesson_response(lesson) -> LessonResponse:  # noqa: ANN001 - domain entity
    return LessonResponse(
        id=lesson.id,
        course_id=lesson.course_id,
        title=lesson.title,
        slug=lesson.slug,
        order_index=lesson.order_index,
        content=lesson.content,
    )


@router.post("/lessons", response_model=LessonResponse, status_code=status.HTTP_201_CREATED)
def create_lesson(payload: LessonCreate, service: ContentServiceDep) -> LessonResponse:
    try:
        lesson = service.create_lesson(
            course_id=payload.course_id,
            title=payload.title,
            slug=payload.slug,
            order_index=payload.order_index,
            content=payload.content,
        )
    except LookupError as exc:
        raise _not_found(exc) from exc
    return _lesson_response(lesson)


@router.put("/lessons/{lesson_id}", response_model=LessonResponse)
def update_lesson(
    lesson_id: uuid.UUID, payload: LessonUpdate, service: ContentServiceDep
) -> LessonResponse:
    try:
        lesson = service.update_lesson(
            lesson_id,
            title=payload.title,
            slug=payload.slug,
            order_index=payload.order_index,
            content=payload.content,
        )
    except LookupError as exc:
        raise _not_found(exc) from exc
    return _lesson_response(lesson)


@router.delete("/lessons/{lesson_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_lesson(lesson_id: uuid.UUID, service: ContentServiceDep) -> None:
    try:
        service.delete_lesson(lesson_id)
    except LookupError as exc:
        raise _not_found(exc) from exc
