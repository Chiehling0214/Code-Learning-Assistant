"""Canonical selectable languages.

The single source of truth for which programming languages a learner can pick.
Ensured in the database on startup (see ``app/infrastructure/db/bootstrap.py``,
run by the container entrypoint after migrations), so no separate seed step is
needed. Every slug here must have a Judge0 mapping in
``app/infrastructure/judge0/client.py`` (``LANGUAGE_IDS``).
"""

from __future__ import annotations

from app.domain.repositories import LanguageRepository

# name shown to learners, slug used everywhere (Judge0, routes, tracks).
DEFAULT_LANGUAGES: list[dict[str, str]] = [
    {"name": "Python", "slug": "python"},
    {"name": "C++", "slug": "cpp"},
    {"name": "Java", "slug": "java"},
    {"name": "JavaScript", "slug": "javascript"},
]


def ensure_languages(languages: LanguageRepository) -> list[str]:
    """Create any missing default languages (idempotent). Returns created slugs."""
    created: list[str] = []
    for spec in DEFAULT_LANGUAGES:
        if languages.get_by_slug(spec["slug"]) is None:
            languages.create(name=spec["name"], slug=spec["slug"])
            created.append(spec["slug"])
    return created
