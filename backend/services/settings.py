"""Environment-driven flags for Earth Engine + Gemini (optional for local dev)."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    enable_live_cv: bool = Field(default=False, description="If true, allows GEE+Gemini when keys are set")
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
