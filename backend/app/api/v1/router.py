"""Aggregates all v1 routers under a single APIRouter."""

from fastapi import APIRouter

from app.api.v1.routes import (
    admin_content,
    courses,
    exercises,
    health,
    languages,
    lessons,
    me,
    profile,
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(me.router)
api_router.include_router(profile.router)
api_router.include_router(languages.router)
api_router.include_router(courses.router)
api_router.include_router(lessons.router)
api_router.include_router(admin_content.router)
api_router.include_router(exercises.router)
api_router.include_router(exercises.admin_router)
