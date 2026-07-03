"""Placement-test use cases (Sprint 10).

Generates a per-track assessment (multiple-choice + two coding tasks) via the AI
provider, self-verifies the coding tasks against the Judge0 path, grades a
submission, and maps the weighted score to a level stored on the track and
profile. Answer keys and reference solutions live only in ``items`` and are
stripped before serving (see ``schemas/placement.py`` + the route).
"""

from __future__ import annotations

import uuid
from typing import Any

from app.application.ports.ai_provider import AIProvider, GeneratePlacementRequest
from app.application.services.ai_usage import AIUsageGuard
from app.application.services.execution_service import ExecutionService
from app.core.config import Settings
from app.domain.entities import PlacementAssessment
from app.domain.repositories import (
    LanguageRepository,
    LanguageTrackRepository,
    PlacementRepository,
    StudentProfileRepository,
)

# Coding tasks weigh more than MCQs in the score.
_MCQ_WEIGHT = 1
_CODING_WEIGHT = 3


def _level_for(percent: int) -> str:
    if percent < 40:
        return "beginner"
    if percent > 75:
        return "advanced"
    return "intermediate"


class PlacementService:
    def __init__(
        self,
        provider: AIProvider,
        placements: PlacementRepository,
        tracks: LanguageTrackRepository,
        languages: LanguageRepository,
        profiles: StudentProfileRepository,
        execution: ExecutionService,
        usage: AIUsageGuard,
        settings: Settings,
    ) -> None:
        self._provider = provider
        self._placements = placements
        self._tracks = tracks
        self._languages = languages
        self._profiles = profiles
        self._execution = execution
        self._usage = usage
        self._settings = settings

    # ----- helpers -----

    def _owned_track(self, user_id: uuid.UUID, track_id: uuid.UUID):
        track = self._tracks.get_by_id(track_id)
        if track is None or track.user_id != user_id:
            raise LookupError(f"Track {track_id} not found")
        return track

    def _language_slug(self, language_id: uuid.UUID) -> str:
        language = self._languages.get_by_id(language_id)
        return language.slug if language else "python"

    def _build_items(self, generated, language: str) -> dict[str, Any]:
        mcqs = []
        for m in generated.mcqs:
            choices = [
                {
                    "id": str(uuid.uuid4()),
                    "text": str(c.get("text", "")),
                    "is_correct": bool(c.get("is_correct")),
                }
                for c in (m.get("choices") or [])
            ]
            mcqs.append(
                {
                    "id": str(uuid.uuid4()),
                    "prompt": str(m.get("prompt", "")),
                    "choices": choices,
                    "explanation": str(m.get("explanation", "")),
                }
            )

        coding = []
        for t in generated.coding:
            coding.append(
                {
                    "id": str(uuid.uuid4()),
                    "prompt": str(t.get("prompt", "")),
                    "language": language,
                    "starter_code": str(t.get("starter_code", "")),
                    "test_spec": t.get("test_spec") or {},
                    "reference_solution": str(t.get("reference_solution", "")),
                }
            )
        return {"mcqs": mcqs, "coding": coding}

    def _self_verify(self, coding: list[dict]) -> list[dict]:
        """Filter coding tasks by self-verification, but never lose them all.

        A task is dropped only when its reference solution *ran and produced the
        wrong output* (``failed``). Tasks are kept when they pass, and also when
        the grader is unavailable (``error`` — Judge0 quota/outage/compile), so a
        flaky sandbox doesn't strip the placement's coding section. If every task
        would be dropped, we keep them all rather than serve an MCQ-only test.
        """
        kept = []
        for task in coding:
            spec = task.get("test_spec") or {}
            if not spec.get("cases"):
                kept.append(task)
                continue
            verdict, _ = self._execution.grade(
                code=task["reference_solution"], language=task["language"], test_spec=spec
            )
            if verdict != "failed":
                kept.append(task)
        return kept or coding

    # ----- use cases -----

    def generate(self, *, user_id: uuid.UUID, track_id: uuid.UUID) -> PlacementAssessment:
        track = self._owned_track(user_id, track_id)
        existing = self._placements.get_by_track(track_id)
        if existing is not None:
            return existing  # idempotent: one placement per track

        language = self._language_slug(track.language_id)
        self._usage.check(user_id)
        generated = self._provider.generate_placement(
            GeneratePlacementRequest(
                language=language, mcq_count=self._settings.placement_mcq_count
            )
        )
        items = self._build_items(generated, language)
        items["coding"] = self._self_verify(items["coding"])
        assessment = self._placements.create(track_id=track_id, user_id=user_id, items=items)
        # Tagged "placement" (not "generate") so the placement test doesn't consume
        # the learner's daily content-generation quota.
        self._usage.record(
            user_id, kind="placement", model=generated.model, total_tokens=generated.total_tokens
        )
        return assessment

    def get(self, *, user_id: uuid.UUID, track_id: uuid.UUID) -> PlacementAssessment:
        self._owned_track(user_id, track_id)
        placement = self._placements.get_by_track(track_id)
        if placement is None:
            raise LookupError("Placement not generated yet")
        return placement

    def submit(
        self,
        *,
        user_id: uuid.UUID,
        track_id: uuid.UUID,
        mcq_answers: dict[str, str],
        code: dict[str, str],
    ) -> tuple[str, int, dict[str, Any]]:
        """Grade a submission; return ``(level, percent, breakdown)``."""
        placement = self.get(user_id=user_id, track_id=track_id)
        items = placement.items or {}

        mcq_results = []
        correct_mcq = 0
        for mcq in items.get("mcqs", []):
            correct_choice = next((c for c in mcq["choices"] if c.get("is_correct")), None)
            correct_id = correct_choice["id"] if correct_choice else None
            selected = mcq_answers.get(mcq["id"])
            ok = selected is not None and selected == correct_id
            correct_mcq += 1 if ok else 0
            # The test is over, so it's safe to reveal the full question, the answer
            # key, and the explanation for the review screen.
            mcq_results.append(
                {
                    "id": mcq["id"],
                    "prompt": mcq.get("prompt", ""),
                    "choices": [
                        {"id": c["id"], "text": c["text"], "is_correct": bool(c.get("is_correct"))}
                        for c in mcq["choices"]
                    ],
                    "selected_choice_id": selected,
                    "correct_choice_id": correct_id,
                    "correct": ok,
                    "explanation": mcq.get("explanation", ""),
                }
            )

        coding_results = []
        passed_coding = 0
        for task in items.get("coding", []):
            source = code.get(task["id"], "")
            passed = False
            passed_cases = 0
            total_cases = len((task.get("test_spec") or {}).get("cases") or [])
            if source.strip():
                verdict, detail = self._execution.grade(
                    code=source, language=task["language"], test_spec=task.get("test_spec") or {}
                )
                passed = verdict == "passed"
                passed_cases = int(detail.get("passed", 0))
                total_cases = int(detail.get("total", total_cases))
            passed_coding += 1 if passed else 0
            coding_results.append(
                {
                    "id": task["id"],
                    "prompt": task.get("prompt", ""),
                    "passed": passed,
                    "passed_cases": passed_cases,
                    "total_cases": total_cases,
                }
            )

        n_mcq = len(items.get("mcqs", []))
        n_coding = len(items.get("coding", []))
        total = n_mcq * _MCQ_WEIGHT + n_coding * _CODING_WEIGHT
        earned = correct_mcq * _MCQ_WEIGHT + passed_coding * _CODING_WEIGHT
        percent = round(earned / total * 100) if total else 0
        level = _level_for(percent)

        breakdown = {
            "percent": percent,
            "correct_mcqs": correct_mcq,
            "total_mcqs": n_mcq,
            "passed_coding": passed_coding,
            "total_coding": n_coding,
            "mcqs": mcq_results,
            "coding": coding_results,
        }
        self._placements.save_result(
            placement.id, result=breakdown, score=percent, level=level
        )
        self._tracks.set_level(track_id, level)
        self._set_profile_level(user_id, level)
        return level, percent, breakdown

    def _set_profile_level(self, user_id: uuid.UUID, level: str) -> None:
        if self._profiles.get_by_user_id(user_id) is None:
            self._profiles.create(user_id=user_id, skill_level=level)
        else:
            self._profiles.update_skill_level(user_id, level)
