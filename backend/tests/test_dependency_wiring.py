"""Regression tests for the production dependency composition root."""

from unittest.mock import MagicMock

from app.api.deps import (
    get_admin_review_service,
    get_content_report_service,
    get_lesson_adjustment_service,
)
from app.application.services.admin_review_service import AdminReviewService
from app.application.services.content_report_service import ContentReportService
from app.application.services.lesson_adjustment_service import LessonAdjustmentService
from app.core.config import Settings
from sqlalchemy.orm import Session


def test_admin_review_service_dependency_is_constructible() -> None:
    service = get_admin_review_service(MagicMock(spec=Session))

    assert isinstance(service, AdminReviewService)


def test_content_report_service_dependency_is_constructible() -> None:
    service = get_content_report_service(
        MagicMock(spec=Session),
        Settings(gemini_api_key="test-key"),
    )

    assert isinstance(service, ContentReportService)


def test_lesson_adjustment_service_dependency_is_constructible() -> None:
    service = get_lesson_adjustment_service(
        MagicMock(spec=Session),
        Settings(gemini_api_key="test-key"),
    )

    assert isinstance(service, LessonAdjustmentService)
