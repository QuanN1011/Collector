"""
Google Geocoding API and Static Maps API.

Env: ``GOOGLE_MAPS_API_KEY`` (``Settings.google_maps_api_key``).
"""

from __future__ import annotations

import logging
from typing import Any
from urllib.parse import urlencode

import httpx

from services.settings import get_settings

logger = logging.getLogger(__name__)

GEOCODE_URL = "https://maps.googleapis.com/maps/api/geocode/json"
STATIC_MAP_BASE = "https://maps.googleapis.com/maps/api/staticmap"


def get_coordinates(address: str) -> dict[str, Any]:
    """
    Geocode a free-text address.

    Returns ``{"lat": float, "lng": float, "formatted_address": str}``.
    """
    settings = get_settings()
    key = settings.google_maps_api_key
    if not key or not key.strip():
        raise RuntimeError("GOOGLE_MAPS_API_KEY is not configured")

    params = {"address": address.strip(), "key": key.strip()}
    with httpx.Client(timeout=30.0) as client:
        r = client.get(GEOCODE_URL, params=params)
        r.raise_for_status()
        data: dict[str, Any] = r.json()

    status = data.get("status")
    if status != "OK":
        msg = data.get("error_message") or status or "geocode failed"
        raise RuntimeError(f"Geocoding API: {msg}")

    results = data.get("results") or []
    if not results:
        raise RuntimeError("Geocoding returned no results for this address")

    first = results[0]
    loc = first.get("geometry", {}).get("location") or {}
    lat, lng = loc.get("lat"), loc.get("lng")
    if lat is None or lng is None:
        raise RuntimeError("Geocoding response missing lat/lng")

    formatted = (first.get("formatted_address") or address.strip()).strip()

    return {"lat": float(lat), "lng": float(lng), "formatted_address": formatted}


def get_satellite_image(lat: float, lng: float) -> str:
    """
    Google Static Maps URL: satellite, zoom 20, 600×600 PNG (key in query string).

    Fetch server-side before sending bytes to Gemini.
    """
    settings = get_settings()
    key = settings.google_maps_api_key
    if not key or not key.strip():
        raise RuntimeError("GOOGLE_MAPS_API_KEY is not configured")

    query = urlencode(
        {
            "center": f"{lat},{lng}",
            "zoom": "20",
            "size": "600x600",
            "maptype": "satellite",
            "format": "png",
            "key": key.strip(),
        }
    )
    return f"{STATIC_MAP_BASE}?{query}"
