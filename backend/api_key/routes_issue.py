"""Issue API keys for verified Auth0 users.

``POST /api/keys/issue`` — **Not** called with ``X-Api-Key``. The SPA sends
``Authorization: Bearer <Auth0 ID token>`` after the user signs in. The backend
verifies the JWT, requires ``email_verified``, then creates or **rotates** one
``api_key`` per Auth0 ``user_sub`` / email. That key is sent on **later** requests
to data routes via the ``X-Api-Key`` header (one key per user, not a new key per HTTP request).
"""

from __future__ import annotations

import os
import secrets
import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient, decode as jwt_decode
from jwt.exceptions import InvalidTokenError
from sqlalchemy import select
from sqlalchemy.orm import Session

from database.api_keys_dataset import ApiKey
from database.config import get_database_url
from database.engine import get_session_factory

router = APIRouter(prefix="/api/keys", tags=["api-keys"])
_bearer = HTTPBearer(auto_error=False)


def _get_db() -> Session:
    if not get_database_url():
        raise HTTPException(status_code=503, detail="DATABASE_URL is not set; cannot issue API keys")
    SessionLocal = get_session_factory()
    return SessionLocal()


def _verify_auth0_id_token(token: str) -> dict:
    domain = os.environ.get("AUTH0_DOMAIN")
    client_id = os.environ.get("AUTH0_CLIENT_ID")
    audience = (os.environ.get("AUTH0_AUDIENCE") or "").strip() or None
    if not domain or not client_id:
        raise HTTPException(
            status_code=503,
            detail="Set AUTH0_DOMAIN and AUTH0_CLIENT_ID in backend/.env to issue keys",
        )
    issuer = f"https://{domain}/"
    jwks_url = f"https://{domain}/.well-known/jwks.json"
    jwks_client = PyJWKClient(jwks_url)
    signing_key = jwks_client.get_signing_key_from_jwt(token)
    # SPA sends ID tokens (aud = client_id). If AUTH0_AUDIENCE is set, try client_id first,
    # then API audience — otherwise verifying with audience-only breaks issue.
    audiences: list[str] = [client_id]
    if audience and audience != client_id:
        audiences.append(audience)
    last_err: InvalidTokenError | None = None
    for aud in audiences:
        try:
            return jwt_decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                audience=aud,
                issuer=issuer,
            )
        except InvalidTokenError as e:
            last_err = e
            continue
    assert last_err is not None
    raise HTTPException(status_code=401, detail=f"Invalid token: {last_err}") from last_err


@router.post("/issue")
def issue_api_key(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> dict[str, str]:
    if not creds or not creds.credentials:
        raise HTTPException(status_code=401, detail="Missing Authorization: Bearer <token>")
    payload = _verify_auth0_id_token(creds.credentials)
    sub = payload.get("sub")
    if not sub or not isinstance(sub, str):
        raise HTTPException(status_code=401, detail="Token missing sub")

    if payload.get("email_verified") is False:
        raise HTTPException(status_code=403, detail="Email must be verified before issuing an API key")

    email = (payload.get("email") or "") or "unknown@unknown"
    email_norm = email[:512]
    raw_key = f"rainuse_{secrets.token_urlsafe(32)}"

    db = _get_db()
    try:
        existing = db.execute(select(ApiKey).where(ApiKey.user_sub == sub)).scalar_one_or_none()
        taken = db.execute(
            select(ApiKey).where(ApiKey.email == email_norm, ApiKey.user_sub != sub)
        ).scalar_one_or_none()
        if taken is not None:
            raise HTTPException(
                status_code=409,
                detail="An API key is already registered for this email",
            )

        now = datetime.now(tz=UTC)
        if existing:
            existing.api_key = raw_key
            existing.email = email_norm
            existing.created_at = now
        else:
            db.add(
                ApiKey(
                    id=str(uuid.uuid4()),
                    user_sub=sub,
                    email=email_norm,
                    api_key=raw_key,
                    created_at=now,
                )
            )
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

    return {"api_key": raw_key}
