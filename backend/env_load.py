"""Load environment variables for the backend (one place for FastAPI, Alembic, and scripts)."""

from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv


def load_backend_env() -> None:
    """Load repo root ``.env`` then ``backend/.env``; backend file wins on duplicate keys."""
    backend_dir = Path(__file__).resolve().parent
    repo_root = backend_dir.parent
    load_dotenv(repo_root / ".env")
    load_dotenv(backend_dir / ".env", override=True)
