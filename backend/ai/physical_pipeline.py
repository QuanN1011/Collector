"""
Physical prospecting signals: roof catchment (catalog + >100k flag), cooling tower (mock or Gemini+GEE).

- Catalog roof sq ft comes from the building dataset (Open Buildings / footprints style).
- Live path: Sentinel-2 chip via Earth Engine + Gemini vision for tower likelihood.
"""

from __future__ import annotations

import logging
from threading import Lock

from ai.gee_imagery import fetch_sentinel2_thumb_png
from ai.gemini_vision import analyze_cooling_tower_from_image
from models.building import BuildingRecord, PhysicalAnalysis
from services.settings import get_settings

logger = logging.getLogger(__name__)

_cache: dict[str, PhysicalAnalysis] = {}
_cache_lock = Lock()


def _mock_tower(building_id: str) -> tuple[bool, float]:
    h = abs(hash(building_id)) % (2**31)
    detected = (h % 5) != 0
    confidence = 0.55 + (h % 45) / 100.0
    return detected, round(confidence, 2)


def _mock_physical(record: BuildingRecord) -> PhysicalAnalysis:
    catchment = float(record.roof_area_sqft)
    tower_ok, tower_conf = _mock_tower(record.id)
    return PhysicalAnalysis(
        roof_catchment_sqft=catchment,
        large_roof=catchment >= 100_000,
        roof_confidence=0.72,
        cooling_tower_detected=tower_ok,
        cooling_tower_confidence=tower_conf,
        imagery_source="none",
        vision_backend="mock",
    )


def _live_physical(record: BuildingRecord) -> PhysicalAnalysis:
    catchment = float(record.roof_area_sqft)
    large = catchment >= 100_000

    if record.latitude is None or record.longitude is None:
        return _mock_physical(record)

    png = fetch_sentinel2_thumb_png(record.latitude, record.longitude)
    if not png:
        p = _mock_physical(record)
        return p.model_copy(
            update={
                "roof_confidence": 0.68,
                "vision_backend": "mock",
                "imagery_source": "none",
            }
        )

    tower = analyze_cooling_tower_from_image(png)
    if tower is None:
        tower_ok, tower_conf = _mock_tower(record.id)
        vision_backend = "mock"
        tower_note_conf = tower_conf
    else:
        tower_ok, tower_conf = tower
        vision_backend = "gemini_vision"
        tower_note_conf = tower_conf

    roof_conf = min(0.95, 0.78 + 0.17)

    return PhysicalAnalysis(
        roof_catchment_sqft=catchment,
        large_roof=large,
        roof_confidence=round(roof_conf, 2),
        cooling_tower_detected=tower_ok,
        cooling_tower_confidence=round(max(0.0, min(1.0, tower_note_conf)), 2),
        imagery_source="COPERNICUS/S2_SR_HARMONIZED",
        vision_backend=vision_backend,
    )


def get_physical_analysis(record: BuildingRecord, *, force_live: bool = False) -> PhysicalAnalysis:
    """
    If force_live and settings.enable_live_cv, run GEE+Gemini (cached per building id).
    Otherwise return fast mock (still uses catalog roof area and >100k flag).
    """
    settings = get_settings()
    key = record.id
    if not force_live or not settings.enable_live_cv:
        return _mock_physical(record)

    with _cache_lock:
        if key in _cache:
            return _cache[key]

    try:
        result = _live_physical(record)
    except Exception as e:
        logger.exception("Live physical analysis failed: %s", e)
        result = _mock_physical(record)

    with _cache_lock:
        _cache[key] = result
    return result
