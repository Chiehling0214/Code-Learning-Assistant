"""Language-track use cases (Sprint 9).

A track is a language the learner has chosen to study; it anchors later
personalization (placement, generated curriculum). The number of concurrent
tracks is capped by the learner's plan (free vs active subscription).
"""

from __future__ import annotations

import uuid
from typing import Any

from app.application.services.entitlement_service import EntitlementService
from app.domain.entities import LanguageTrack
from app.domain.repositories import (
    CourseRepository,
    LanguageRepository,
    LanguageTrackRepository,
    PlacementRepository,
)


class DuplicateTrackError(RuntimeError):
    """Raised when the learner already has a track for that language."""


class LanguageLimitError(RuntimeError):
    """Raised when adding a track would exceed the plan's language cap."""


class TrackSetupIncompleteError(RuntimeError):
    """Raised when another language still needs placement or course setup."""


class TrackService:
    def __init__(
        self,
        tracks: LanguageTrackRepository,
        languages: LanguageRepository,
        entitlements: EntitlementService,
        placements: PlacementRepository,
        courses: CourseRepository,
    ) -> None:
        self._tracks = tracks
        self._languages = languages
        self._entitlements = entitlements
        self._placements = placements
        self._courses = courses

    def has_tracks(self, user_id: uuid.UUID) -> bool:
        return self._tracks.count_by_user(user_id) > 0

    def max_languages(self, user_id: uuid.UUID) -> int:
        return self._entitlements.max_languages(user_id)

    def list_tracks(self, user_id: uuid.UUID) -> list[dict[str, Any]]:
        """Return the user's tracks enriched with language name/slug."""
        by_id = {lang.id: lang for lang in self._languages.list_all()}
        tracks = self._tracks.list_by_user(user_id)
        course_track_ids = {
            course.track_id
            for course in self._courses.list_by_track_ids([track.id for track in tracks])
            if course.track_id is not None and course.kind != "practice"
        }
        result: list[dict[str, Any]] = []
        for track in tracks:
            language = by_id.get(track.language_id)
            placement = self._placements.get_by_track(track.id)
            result.append(
                {
                    "id": track.id,
                    "language_id": track.language_id,
                    "language_name": language.name if language else "",
                    "language_slug": language.slug if language else "",
                    "level": track.level,
                    "status": track.status,
                    "placement_status": placement.status if placement else None,
                    "has_course": track.id in course_track_ids,
                }
            )
        return result

    def add_track(self, *, user_id: uuid.UUID, language_id: uuid.UUID) -> LanguageTrack:
        if self._languages.get_by_id(language_id) is None:
            raise LookupError(f"Language {language_id} not found")
        if self._tracks.get_by_user_and_language(user_id, language_id) is not None:
            raise DuplicateTrackError("You are already studying this language")
        existing_tracks = self._tracks.list_by_user(user_id)
        existing_course_track_ids = {
            course.track_id
            for course in self._courses.list_by_track_ids([track.id for track in existing_tracks])
            if course.track_id is not None and course.kind != "practice"
        }
        incomplete = next(
            (
                track
                for track in existing_tracks
                if (placement := self._placements.get_by_track(track.id)) is None
                or placement.status != "completed"
                or track.id not in existing_course_track_ids
            ),
            None,
        )
        if incomplete is not None:
            raise TrackSetupIncompleteError(
                "Finish the current language's placement and course setup before adding another."
            )
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
