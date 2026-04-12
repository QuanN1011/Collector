#!/usr/bin/env python3
"""
Quick checks for the RainUSE Nexus API (no running server required).

Usage (from repo):
  cd backend
  python scripts/smoke_test.py

Optional (live GEE + Gemini — slow, needs .env + credentials):
  RUN_LIVE_CV=1 python scripts/smoke_test.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Run as: cd backend && python scripts/smoke_test.py
_BACKEND = Path(__file__).resolve().parent.parent
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))
os.chdir(_BACKEND)

from fastapi.testclient import TestClient  # noqa: E402

from database.config import get_database_url  # noqa: E402
from main import app  # noqa: E402


def _auth_headers() -> dict[str, str]:
    key = os.environ.get("RAINUSE_API_KEY", "").strip()
    if key:
        return {"X-Api-Key": key}
    return {}


def main() -> int:
    h = _auth_headers()
    if get_database_url() and not h:
        print(
            "Set RAINUSE_API_KEY when DATABASE_URL is set (smoke tests call protected routes).",
            file=sys.stderr,
        )
        return 1
    c = TestClient(app)

    r = c.get("/health")
    assert r.status_code == 200, r.text
    print("OK  GET /health")

    r = c.get("/states", headers=h)
    assert r.status_code == 200, r.text
    st_payload = r.json()
    assert "states" in st_payload
    states = st_payload["states"]
    for need in ("TX", "AZ", "PA"):
        assert need in states, f"expected {need} in /states, got {states!r}"
    print(f"OK  GET /states ({len(states)} states with buildings)")

    r = c.get("/buildings?state=TEX", headers=h)
    assert r.status_code == 400, r.text
    print("OK  GET /buildings?state=TEX -> 400 (invalid code)")

    r = c.get("/buildings?state=ZZ", headers=h)
    assert r.status_code == 400, r.text
    print("OK  GET /buildings?state=ZZ -> 400 (no state context)")

    r = c.get("/buildings?state=TX", headers=h)
    assert r.status_code == 200, r.text
    data = r.json()
    assert len(data) >= 1
    b0 = data[0]
    for key in (
        "id",
        "physical_analysis",
        "viability_score",
        "rainwater_potential_gallons",
        "annual_water_savings",
    ):
        assert key in b0, f"missing {key}"
    pa = b0["physical_analysis"]
    assert pa["vision_backend"] == "mock"
    assert "roof_catchment_provenance" in pa
    assert 0.0 <= pa["roof_confidence"] <= 1.0
    print(f"OK  GET /buildings?state=TX ({len(data)} buildings)")

    r = c.get("/buildings?state=AZ", headers=h)
    assert r.status_code == 200, r.text
    az = r.json()
    assert len(az) >= 1
    print(f"OK  GET /buildings?state=AZ ({len(az)} buildings)")

    bid = b0["id"]
    r = c.get(f"/building/{bid}", headers=h)
    assert r.status_code == 200, r.text
    print(f"OK  GET /building/{bid}")

    r = c.get("/building/does-not-exist-99999", headers=h)
    assert r.status_code == 404, r.text
    print("OK  GET /building/does-not-exist-99999 -> 404")

    r = c.get("/top-prospects?state=TX&limit=3", headers=h)
    assert r.status_code == 200, r.text
    top = r.json()
    assert len(top) <= 3
    if len(top) >= 2:
        assert top[0]["viability_score"] >= top[1]["viability_score"]
    print("OK  GET /top-prospects?state=TX&limit=3")

    if os.environ.get("RUN_LIVE_CV") == "1":
        r = c.get(f"/building/{bid}?live_cv=true", headers=h)
        assert r.status_code == 200, r.text
        pa = r.json()["physical_analysis"]
        print(
            f"OK  GET /building/{bid}?live_cv=true  "
            f"imagery={pa['imagery_source']!r} backend={pa['vision_backend']!r}"
        )
    else:
        print("SKIP live CV (set RUN_LIVE_CV=1 to exercise Static Maps+Gemini — first call can take 10–60s)")

    print("\nAll smoke checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
