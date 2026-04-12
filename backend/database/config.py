"""Runtime configuration for the database layer."""

from __future__ import annotations

import os


def get_database_url() -> str | None:
    """PostgreSQL connection URL, e.g. postgresql+psycopg://user:pass@localhost:5432/rainuse."""
    return os.environ.get("DATABASE_URL")


def use_database() -> bool:
    """When True, persistence uses Postgres (+ PostGIS). When False, CSV fallback (dev without Docker)."""
    return bool(get_database_url())
