"""Environment-driven flags for Earth Engine + Gemini (optional for local dev)."""

import os
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def live_cv_enabled(settings: "Settings") -> bool:
    """
    Whether the live GEE + Gemini path is allowed when the client sends ``live_cv=true``.

    - ``ENABLE_LIVE_CV=false`` / ``0`` / ``off`` → never live (stay on mock).
    - ``ENABLE_LIVE_CV=true`` / ``1`` / ``on`` → allow live (still needs credentials to succeed).
    - Unset or empty → **auto**: allow live when both ``GEMINI_API_KEY`` and ``GEE_PROJECT_ID`` are set.
    """
    raw = os.environ.get("ENABLE_LIVE_CV")
    if raw is not None and raw.strip() != "":
        v = raw.strip().lower()
        if v in ("0", "false", "no", "off"):
            return False
        if v in ("1", "true", "yes", "on"):
            return True
    return bool(settings.gemini_api_key and settings.gee_project_id)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    gee_project_id: str | None = Field(default=None, description="Google Cloud / Earth Engine project id")
    gemini_api_key: str | None = Field(default=None, description="Google AI Studio / Gemini API key")
    gemini_model: str = Field(default="gemini-2.0-flash")
    # Wider buffer + larger thumb = more context for cooling-plant cues (more Gemini tokens / cost).
    gee_buffer_meters: float = Field(
        default=280.0,
        description="Radius (m) around lat/lon for Sentinel-2 chip bounds",
    )
    gee_thumb_size: int = Field(
        default=1024,
        description="Square PNG edge length (px) from Earth Engine getThumbURL",
    )
    save_gee_thumbnails: bool = Field(
        default=False,
        description="If true, write each fetched GEE PNG under backend/debug_gee_thumbnails/",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
