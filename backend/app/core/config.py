"""Application configuration loaded from the environment.

Centralizes all settings using ``pydantic-settings`` so the rest of the code
never reads ``os.environ`` directly. Access via :func:`get_settings`.
"""

from functools import lru_cache
from typing import Annotated

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- App ---
    app_name: str = "codepath-api"
    environment: str = "development"
    log_level: str = "INFO"
    api_v1_prefix: str = "/api/v1"

    # --- Database ---
    database_url: str = "postgresql+psycopg2://codepath:codepath@localhost:5432/codepath"

    # --- CORS ---
    # NoDecode disables pydantic-settings' default JSON parsing for this complex
    # type so a plain comma-separated env string reaches the validator below.
    cors_origins: Annotated[list[str], NoDecode] = ["http://localhost:5173"]

    # --- Firebase / Auth ---
    firebase_project_id: str | None = None
    firebase_credentials_file: str | None = None
    auth_stub_enabled: bool = True

    # --- Judge0 (code execution, Sprint 4) ---
    # Base URL of the Judge0 instance. For self-hosted use the in-cluster URL;
    # for RapidAPI leave this and set judge0_rapidapi_key (the client then targets
    # the RapidAPI host below automatically).
    judge0_url: str = "http://judge0:2358"
    # Self-hosted auth token (sent as X-Auth-Token). Ignored in RapidAPI mode.
    judge0_auth_token: str | None = None
    # RapidAPI mode: when a key is set the client switches to the hosted Judge0 CE
    # endpoint and RapidAPI headers — no local Judge0 containers needed.
    judge0_rapidapi_key: str | None = None
    judge0_rapidapi_host: str = "judge0-ce.p.rapidapi.com"
    # Seconds to wait for a single Judge0 execution before giving up.
    judge0_timeout: float = 20.0

    # --- AI (Gemini, Sprint 6) ---
    # API key from Google AI Studio. When empty the AI features are disabled and
    # the endpoints return a friendly "not configured" error (503).
    gemini_api_key: str | None = None
    # Default model for tutoring/feedback and generation. flash-lite has a much
    # higher free-tier request quota and is plenty for these structured tasks.
    gemini_model: str = "gemini-2.5-flash-lite"
    # Model for teaching / content generation; same as above by default so one
    # key/quota works out of the box (override to gemini-2.5-pro for richer text).
    gemini_teacher_model: str = "gemini-2.5-flash-lite"
    # Per-user free-tier guards: requests allowed per rolling minute and per day.
    ai_rate_limit_per_minute: int = 8
    ai_daily_limit: int = 200
    # Number of multiple-choice questions in a placement test (Sprint 10).
    placement_mcq_count: int = 5
    # AI curriculum generation (Sprint 11).
    curriculum_lesson_count: int = 6
    curriculum_exercises_per_lesson: int = 2
    curriculum_quiz_questions: int = 3
    # Lessons generated per AI request (a whole batch in one call) — fewer, larger
    # requests conserve the free-tier daily request quota. 6 lessons / 3 = 2 calls.
    curriculum_batch_size: int = 3
    # Pause between batches (helps the per-minute limit when there are >1 batches).
    curriculum_batch_pause_seconds: float = 30.0
    # Self-verify generated exercises via Judge0 (advisory only — logs a warning
    # but never drops; off by default to save Judge0 quota and speed generation).
    curriculum_self_verify: bool = False
    # On a provider rate-limit (429) during generation, wait this many seconds
    # and retry the lesson (the free tier's per-minute cap resets in ~60s).
    curriculum_retry_delay_seconds: float = 20.0
    curriculum_retry_attempts: int = 3
    # Continuous learning (Sprint 12): default lessons added per "Learn more" /
    # chat request, the upper bound the learner may request, and the completion
    # ratio at which the "Learn more" hint appears.
    curriculum_extend_count: int = 2
    curriculum_extend_max: int = 5
    curriculum_extend_threshold: float = 0.8

    # --- Billing (Stripe, Sprint 8) ---
    # When billing is disabled (default), premium gating is a no-op — every
    # authenticated user is entitled. Enable it in production once Stripe is set.
    billing_enabled: bool = False
    stripe_api_key: str | None = None
    stripe_webhook_secret: str | None = None
    stripe_price_id: str | None = None
    # Where Stripe redirects after checkout (frontend URLs).
    checkout_success_url: str = "http://localhost:5173/subscription?status=success"
    checkout_cancel_url: str = "http://localhost:5173/subscription?status=cancel"

    # --- Language tracks / entitlements (Sprint 9 / 13) ---
    # Max concurrent language tracks. Free users are capped; active subscribers
    # get the higher limit.
    free_max_languages: int = 2
    paid_max_languages: int = 20
    # Plan-aware daily caps (Sprint 13). AI Tutor hints and curriculum
    # generation/extend requests per rolling 24h, by plan. Over-limit → 402.
    free_tutor_daily: int = 5
    paid_tutor_daily: int = 100
    free_generations_daily: int = 10
    paid_generations_daily: int = 100

    # --- Hardening (Sprint 8) ---
    # Simple in-process per-client rate limit (off by default so dev/tests are
    # unaffected; enabled in the production compose file).
    rate_limit_enabled: bool = False
    rate_limit_per_minute: int = 120

    @property
    def ai_enabled(self) -> bool:
        return bool(self.gemini_api_key)

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_cors(cls, value: object) -> object:
        """Allow a comma-separated string from the environment."""
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    """Return a cached :class:`Settings` instance."""
    return Settings()
