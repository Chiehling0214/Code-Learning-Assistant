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
