"""Tests for the canonical default-languages bootstrap."""

from app.core.languages import DEFAULT_LANGUAGES, ensure_languages
from app.infrastructure.judge0.client import LANGUAGE_IDS

from tests.fakes import FakeLanguageRepository


def test_ensure_languages_creates_all_then_is_idempotent() -> None:
    repo = FakeLanguageRepository()

    created = ensure_languages(repo)
    assert set(created) == {lang["slug"] for lang in DEFAULT_LANGUAGES}
    assert "javascript" in created  # newly added
    assert "java" in created

    # A second run creates nothing (idempotent).
    assert ensure_languages(repo) == []
    slugs = {lang.slug for lang in repo.list_all()}
    assert {"python", "cpp", "java", "javascript"} <= slugs


def test_every_default_language_has_a_judge0_mapping() -> None:
    for lang in DEFAULT_LANGUAGES:
        assert lang["slug"] in LANGUAGE_IDS, f"{lang['slug']} missing a Judge0 id"
