"""Router dependency for data routes.

API key **enforcement** is disabled: requests do not need ``X-Api-Key``.
Issuing keys via ``POST /api/keys/issue`` (Auth0) remains available if you want
to use keys from other clients later.
"""

from __future__ import annotations


def require_api_key() -> None:
    return None
