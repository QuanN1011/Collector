"""Environment-driven flags for live CV (Static Maps + Gemini) and optional Earth Engine utilities."""

import os
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def live_cv_enabled(settings: "Settings") -> bool:
    """
    Whether live CV is allowed when the client sends ``live_cv=true``.

    Live CV uses **Google Static Maps** + **Gemini** (not Earth Engine).

    - ``ENABLE_LIVE_CV=false`` / ``0`` / ``off`` → never live (stay on mock).
    - ``ENABLE_LIVE_CV=true`` / ``1`` / ``on`` → allow live (still needs credentials to succeed).
    - Unset or empty → **auto**: allow when ``GEMINI_API_KEY`` and ``GOOGLE_MAPS_API_KEY`` are set.
    """
    raw = os.environ.get("ENABLE_LIVE_CV")
    if raw is not None and raw.strip() != "":
        v = raw.strip().lower()
        if v in ("0", "false", "no", "off"):
            return False
        if v in ("1", "true", "yes", "on"):
            return True
    return bool(settings.gemini_api_key and settings.google_maps_api_key)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    google_maps_api_key: str | None = Field(
        default=None,
        description="Maps Platform key: Geocoding + Static Maps for GET /analyze-building",
    )
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
