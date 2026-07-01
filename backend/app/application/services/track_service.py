"""Language-track use cases (Sprint 9).

A track is a language the learner has chosen to study; it anchors later
personalization (placement, generated curriculum). The number of concurrent
tracks is capped by the learner's plan (free vs active subscription).
"""

from __future__ import annotations

import uuid
from typing import Any

from app.application.services.subscription_service import SubscriptionService
from app.core.config import Settings
from app.domain.entities import LanguageTrack
from app.domain.repositories import LanguageRepository, LanguageTrackRepository


class DuplicateTrackError(RuntimeError):
    """Raised when the learner already has a track for that language."""


class LanguageLimitError(RuntimeError):
    """Raised when adding a track would exceed the plan's language cap."""


class TrackService:
    def __init__(
        self,
        tracks: LanguageTrackRepository,
        languages: LanguageRepository,
        subscriptions: SubscriptionService,
        settings: Settings,
    ) -> None:
        self._tracks = tracks
        self._languages = languages
        self._subscriptions = subscriptions
        self._settings = settings

    def has_tracks(self, user_id: uuid.UUID) -> bool:
        return self._tracks.count_by_user(user_id) > 0

    def max_languages(self, user_id: uuid.UUID) -> int:
        if self._subscriptions.is_active(user_id):
            return self._settings.paid_max_languages
        return self._settings.free_max_languages

    def list_tracks(self, user_id: uuid.UUID) -> list[dict[str, Any]]:
        """Return the user's tracks enriched with language name/slug."""
        by_id = {lang.id: lang for lang in self._languages.list_all()}
        result: list[dict[str, Any]] = []
        for track in self._tracks.list_by_user(user_id):
            language = by_id.get(track.language_id)
            result.append(
                {
                    "id": track.id,
                    "language_id": track.language_id,
                    "language_name": language.name if language else "",
                    "language_slug": language.slug if language else "",
                    "level": track.level,
                    "status": track.status,
                }
            )
        return result

    def add_track(self, *, user_id: uuid.UUID, language_id: uuid.UUID) -> LanguageTrack:
        if self._languages.get_by_id(language_id) is None:
            raise LookupError(f"Language {language_id} not found")
        if self._tracks.get_by_user_and_language(user_id, language_id) is not None:
            raise DuplicateTrackError("You are already studying this language")
        if self._tracks.count_by_user(user_id) >= self.max_languages(user_id):
            raise LanguageLimitError(
                "You've reached your plan's language limit. Upgrade to add more."
            )
        return self._tracks.create(user_id=user_id, language_id=language_id)

    def remove_track(self, *, user_id: uuid.UUID, track_id: uuid.UUID) -> None:
        track = self._tracks.get_by_id(track_id)
        if track is None or track.user_id != user_id:
            raise LookupError(f"Track {track_id} not found")
        self._tracks.delete(track_id)
