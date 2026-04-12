"""
Fetch satellite image bytes from Google Static Maps API.

Env: ``GOOGLE_MAPS_API_KEY`` (same as Geocoding / Static URL builder).
"""

from __future__ import annotations

import logging
from urllib.parse import urlencode

import httpx

from services.settings import get_settings

logger = logging.getLogger(__name__)

STATIC_MAP_URL = "https://maps.googleapis.com/maps/api/staticmap"


def get_satellite_image(lat: float, lon: float) -> bytes:
    """
    Download a PNG satellite chip centered on ``lat``, ``lon``.

    Uses zoom 19 and 640×640 per RainUSE live CV spec.
    """
    settings = get_settings()
    key = (settings.google_maps_api_key or "").strip()
    if not key:
        raise RuntimeError("GOOGLE_MAPS_API_KEY is not configured")

    query = urlencode(
        {
            "center": f"{lat},{lon}",
            "zoom": "19",
            "size": "640x640",
            "maptype": "satellite",
            "format": "png",
            "key": key,
        }
    )
    url = f"{STATIC_MAP_URL}?{query}"

    with httpx.Client(timeout=45.0) as client:
        response = client.get(url)
        if response.status_code != 200:
            logger.warning("Static Maps HTTP %s for %s,%s", response.status_code, lat, lon)
            response.raise_for_status()
        data = response.content
        if not data or len(data) < 100:
            raise RuntimeError("Static Maps returned empty or trivial response body")
        return data
