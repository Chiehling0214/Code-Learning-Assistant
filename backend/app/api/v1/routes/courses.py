"""Public read endpoints for courses."""

from fastapi import APIRouter, HTTPException, status

from app.api.deps import ContentServiceDep
from app.schemas.content import CourseDetailResponse, CourseResponse, LessonSummary

router = APIRouter(tags=["content"])


@router.get("/courses", response_model=list[CourseResponse])
def list_courses(service: ContentServiceDep) -> list[CourseResponse]:
    return [
        CourseResponse(
            id=c.id,
            language_id=c.language_id,
            title=c.title,
            slug=c.slug,
            description=c.description,
        )
        for c in service.list_courses()
    ]


@router.get("/courses/{slug}", response_model=CourseDetailResponse)
def get_course(slug: str, service: ContentServiceDep) -> CourseDetailResponse:
    try:
        course = service.get_course_by_slug(slug)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    lessons = service.list_lessons_for_course(course.id)
    return CourseDetailResponse(
        id=course.id,
        language_id=course.language_id,
        title=course.title,
        slug=course.slug,
        description=course.description,
        lessons=[
            LessonSummary(id=ln.id, title=ln.title, slug=ln.slug, order_index=ln.order_index)
            for ln in lessons
        ],
    )
