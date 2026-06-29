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
