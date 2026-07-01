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
    # Default model for tutoring/feedback and most generation (generous free tier).
    gemini_model: str = "gemini-2.5-flash"
    # Optional higher-quality model for long-form teaching content; defaults to
    # the same model so a single key/quota works out of the box.
    gemini_teacher_model: str = "gemini-2.5-flash"
    # Per-user free-tier guards: requests allowed per rolling minute and per day.
    ai_rate_limit_per_minute: int = 8
    ai_daily_limit: int = 200
    # Number of multiple-choice questions in a placement test (Sprint 10).
    placement_mcq_count: int = 5

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

    # --- Language tracks / entitlements (Sprint 9) ---
    # Max concurrent language tracks. Free users are capped; active subscribers
    # get the higher limit.
    free_max_languages: int = 2
    paid_max_languages: int = 20

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
