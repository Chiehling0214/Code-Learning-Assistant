"""Plan entitlements endpoint (Sprint 13)."""

from fastapi import APIRouter

from app.api.deps import CurrentDbUser, EntitlementServiceDep
from app.schemas.entitlements import EntitlementsResponse

router = APIRouter(tags=["entitlements"])


@router.get("/me/entitlements", response_model=EntitlementsResponse)
def get_entitlements(
    current_user: CurrentDbUser, service: EntitlementServiceDep
) -> EntitlementsResponse:
    e = service.snapshot(current_user.id)
    return EntitlementsResponse(
        plan=e.plan,
        max_languages=e.max_languages,
        tutor_daily=e.tutor_daily,
        generations_daily=e.generations_daily,
        languages_used=e.languages_used,
        tutor_used_today=e.tutor_used_today,
        generations_used_today=e.generations_used_today,
    )
