"""
API key dataset (isolated from building / scoring schema in ``database.tables``).

Same Postgres database and SQLAlchemy ``Base``; only the **module** is split out so this
file can be merged independently and the ``api_keys`` table is clearly “auth keys only”.

**Columns:** link Auth0 ``user_sub`` + verified **email** to a single **api_key** string.

Prototype decisions (revisit when productizing):
- **No expiry:** keys are valid until replaced or revoked. Time-limited keys can be added later
  (e.g. ``expires_at`` column + cron / middleware check).
- **No rate limits** on ``POST /api/keys/issue`` or data routes here; add middleware / gateway later.
- **Revocation:** delete or null the row in ``api_keys`` via SQL / admin tooling for now; no API yet.

**Audiences (Auth0):** an “audience” is the identifier for a **Resource Server / API** (e.g. your
backend API). ID tokens use ``aud`` = SPA **client id**; access tokens for an API often use
``aud`` = that API’s identifier. Issuance verifies JWTs against JWKS; see ``api_key/routes_issue.py``.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from database.tables import Base


class ApiKey(Base):
    """
    At most one row per Auth0 user (``user_sub``) and at most one row per **email**.

    When a verified user requests a key, we store or rotate ``api_key`` for that identity.
    """

    __tablename__ = "api_keys"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_sub: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    email: Mapped[str] = mapped_column(String(512), nullable=False, unique=True, index=True)
    api_key: Mapped[str] = mapped_column(String(512), nullable=False, unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
