"""
OpenStreetMap Nominatim reverse geocoding with on-disk JSON cache.

Usage policy: https://operations.osmfoundation.org/policies/nominatim/
— max ~1 request/second; identify via User-Agent; cache responses.
"""

from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass
from pathlib import Path

import httpx

NOMINATIM_REVERSE_URL = "https://nominatim.openstreetmap.org/reverse"
USER_AGENT = "RainUSE-Nexus/1.0 (https://github.com/; building footprint ingest)"

# Full state/DC names as returned by Nominatim "address.state" → USPS code
US_STATE_NAME_TO_CODE: dict[str, str] = {
    "Alabama": "AL",
    "Alaska": "AK",
    "Arizona": "AZ",
    "Arkansas": "AR",
    "California": "CA",
    "Colorado": "CO",
    "Connecticut": "CT",
    "Delaware": "DE",
    "Florida": "FL",
    "Georgia": "GA",
    "Hawaii": "HI",
    "Idaho": "ID",
    "Illinois": "IL",
    "Indiana": "IN",
    "Iowa": "IA",
    "Kansas": "KS",
    "Kentucky": "KY",
    "Louisiana": "LA",
    "Maine": "ME",
    "Maryland": "MD",
    "Massachusetts": "MA",
    "Michigan": "MI",
    "Minnesota": "MN",
    "Mississippi": "MS",
    "Missouri": "MO",
    "Montana": "MT",
    "Nebraska": "NE",
    "Nevada": "NV",
    "New Hampshire": "NH",
    "New Jersey": "NJ",
    "New Mexico": "NM",
    "New York": "NY",
    "North Carolina": "NC",
    "North Dakota": "ND",
    "Ohio": "OH",
    "Oklahoma": "OK",
    "Oregon": "OR",
    "Pennsylvania": "PA",
    "Rhode Island": "RI",
    "South Carolina": "SC",
    "South Dakota": "SD",
    "Tennessee": "TN",
    "Texas": "TX",
    "Utah": "UT",
    "Vermont": "VT",
    "Virginia": "VA",
    "Washington": "WA",
    "West Virginia": "WV",
    "Wisconsin": "WI",
    "Wyoming": "WY",
    "District of Columbia": "DC",
}


@dataclass(frozen=True)
class ReverseGeocodeResult:
    city: str
    county: str
    display_name: str
    state_matches_expected: bool


def _cache_key_path(lat: float, lon: float, cache_dir: Path) -> Path:
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir / f"{lat:.5f}_{lon:.5f}.json"


def _extract_city(addr: dict[str, str]) -> str:
    for k in ("city", "town", "village", "hamlet", "municipality", "suburb"):
        v = addr.get(k)
        if v and str(v).strip():
            return str(v).strip()
    return ""


def _state_code_from_address(addr: dict[str, object]) -> str | None:
    iso = addr.get("ISO3166-2-lvl4") or ""
    m = re.match(r"^US-([A-Z]{2})$", str(iso).strip().upper())
    if m:
        return m.group(1)
    st_name = str(addr.get("state") or "").strip()
    if not st_name:
        return None
    if len(st_name) == 2 and st_name.isalpha():
        return st_name.upper()
    return US_STATE_NAME_TO_CODE.get(st_name)


def reverse_geocode(
    lat: float,
    lon: float,
    *,
    expect_state_code: str,
    cache_dir: Path,
    http_timeout: float = 30.0,
    delay_after_request_sec: float = 1.1,
) -> ReverseGeocodeResult:
    """
    Reverse-geocode a point; validate state against expected USPS code (Microsoft stem state).
    Cached per rounded lat/lon to respect Nominatim rate limits.
    """
    expect = expect_state_code.strip().upper()
    key = _cache_key_path(lat, lon, cache_dir)
    if key.is_file():
        try:
            raw = json.loads(key.read_text(encoding="utf-8"))
            addr = raw.get("address") or {}
            if not isinstance(addr, dict):
                addr = {}
            disp = str(raw.get("display_name") or "").strip()
            city = str(raw.get("_city") or "").strip() or _extract_city(addr)
            county = str(addr.get("county") or "").strip()
            sc = _state_code_from_address(addr)
            ok = sc == expect if sc else False
            return ReverseGeocodeResult(
                city=city,
                county=county,
                display_name=disp,
                state_matches_expected=ok,
            )
        except (json.JSONDecodeError, OSError):
            pass

    params = {
        "lat": lat,
        "lon": lon,
        "format": "json",
        "addressdetails": 1,
        "zoom": 18,
    }
    headers = {"User-Agent": USER_AGENT, "Accept-Language": "en"}
    with httpx.Client(timeout=http_timeout) as client:
        r = client.get(NOMINATIM_REVERSE_URL, params=params, headers=headers)
        r.raise_for_status()
        data = r.json()
    time.sleep(delay_after_request_sec)

    addr_raw = data.get("address") or {}
    addr = addr_raw if isinstance(addr_raw, dict) else {}
    disp = str(data.get("display_name") or "").strip()
    city = _extract_city(addr)
    county = str(addr.get("county") or "").strip()
    sc = _state_code_from_address(addr)
    ok = sc == expect if sc else False

    try:
        to_store = dict(data)
        to_store["_city"] = city
        key.write_text(json.dumps(to_store, ensure_ascii=False), encoding="utf-8")
    except OSError:
        pass

    return ReverseGeocodeResult(
        city=city,
        county=county,
        display_name=disp,
        state_matches_expected=ok,
    )
