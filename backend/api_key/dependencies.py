"""Require ``X-Api-Key`` on data routes when Postgres is configured (prototype).

No logging of failed keys here (keep noise low); add structured logging / metrics later if needed.
"""

from __future__ import annotations

from collections.abc import Generator

from fastapi import Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from database.api_keys_dataset import ApiKey
from database.config import get_database_url
from database.engine import get_session_factory


def get_db_optional() -> Generator[Session | None, None, None]:
    if not get_database_url():
        yield None
        return
    SessionLocal = get_session_factory()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def require_api_key(
    db: Session | None = Depends(get_db_optional),
    x_api_key: str | None = Header(default=None, alias="X-Api-Key"),
) -> object | None:
    if not get_database_url():
        return None
    if db is None:
        raise HTTPException(status_code=503, detail="Database not configured")
    if not x_api_key or not x_api_key.strip():
        raise HTTPException(status_code=401, detail="Missing X-Api-Key")
    row = db.execute(select(ApiKey).where(ApiKey.api_key == x_api_key.strip())).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return row
