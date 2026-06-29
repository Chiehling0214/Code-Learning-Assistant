"""Aggregates all v1 routers under a single APIRouter."""

from fastapi import APIRouter

from app.api.v1.routes import health, me

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(me.router)
