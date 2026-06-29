"""Public read endpoints for programming languages."""

from fastapi import APIRouter

from app.api.deps import ContentServiceDep
from app.schemas.content import LanguageResponse

router = APIRouter(tags=["content"])


@router.get("/languages", response_model=list[LanguageResponse])
def list_languages(service: ContentServiceDep) -> list[LanguageResponse]:
    return [
        LanguageResponse(id=lang.id, name=lang.name, slug=lang.slug)
        for lang in service.list_languages()
    ]
