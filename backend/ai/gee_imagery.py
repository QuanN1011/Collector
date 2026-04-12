"""
Google Earth Engine: export a Sentinel-2 RGB thumbnail around a building.

Sentinel-2 is ~10 m/px; thumbnails are a trade-off: small = cheap/fast for Gemini but
harder to see fine structure. Tune ``gee_thumb_size`` and ``gee_buffer_meters`` in settings.

Requires: Earth Engine enabled on a GCP project, authentication (e.g.
`earthengine authenticate` or GOOGLE_APPLICATION_CREDENTIALS), and
GEE_PROJECT_ID in the environment when calling Initialize.
"""

from __future__ import annotations

import logging
import httpx

from services.settings import get_settings

logger = logging.getLogger(__name__)

_ee = None
_ee_initialized = False
# Set when ``ee.Initialize`` fails so callers can surface the real reason (e.g. IAM) in API payloads.
_last_ee_init_error: str | None = None


def last_earth_engine_init_error() -> str | None:
    """Human-readable message from the last failed ``ee.Initialize``, or None if none / success."""
    return _last_ee_init_error


def _ensure_ee():
    global _ee
    if _ee is not None:
        return _ee
    try:
        import ee  # type: ignore

        _ee = ee
    except ImportError:
        logger.warning("earthengine-api not installed; GEE imagery disabled")
        return None
    return _ee


def _init_ee() -> bool:
    global _ee_initialized, _last_ee_init_error
    if _ee_initialized:
        return True
    _last_ee_init_error = None
    ee = _ensure_ee()
    if ee is None:
        _last_ee_init_error = "earthengine-api import failed"
        return False
    settings = get_settings()
    if not settings.gee_project_id:
        logger.info("GEE_PROJECT_ID not set; skipping Earth Engine init")
        _last_ee_init_error = "GEE_PROJECT_ID is not set"
        return False
    try:
        ee.Initialize(project=settings.gee_project_id)
        _ee_initialized = True
        _last_ee_init_error = None
        return True
    except Exception as e:
        msg = str(e).strip()
        _last_ee_init_error = msg[:800] if msg else "Earth Engine Initialize failed"
        logger.warning("Earth Engine Initialize failed: %s", e)
        return False


def fetch_sentinel2_thumb_png(lat: float, lon: float) -> bytes | None:
    """
    Median composite of Sentinel-2 SR (harmonized), cloud-screened, RGB thumbnail.
    Returns PNG bytes or None if GEE/network fails.
    """
    ee = _ensure_ee()
    if ee is None or not _init_ee():
        return None

    settings = get_settings()
    try:
        point = ee.Geometry.Point([float(lon), float(lat)])
        region = point.buffer(float(settings.gee_buffer_meters)).bounds()
        start = ee.Date("2023-01-01")
        end = ee.Date("2024-12-31")
        col = (
            ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
            .filterBounds(point)
            .filterDate(start, end)
            .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 40))
        )
        img = col.median().select(["B4", "B3", "B2"])
        vis = {"min": 0, "max": 3500, "dimensions": settings.gee_thumb_size, "region": region}
        url = img.getThumbURL(vis)
        with httpx.Client(timeout=60.0) as client:
            r = client.get(url)
            r.raise_for_status()
            return r.content
    except Exception as e:
        logger.warning("GEE thumb fetch failed: %s", e)
        return None
