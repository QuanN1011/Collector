"""
Physical prospecting signals: roof catchment (catalog + >100k flag), cooling tower (mock or Gemini+GEE).

- Catalog roof sq ft comes from the building dataset (Open Buildings / footprints style).
- Live path: Sentinel-2 chip via Earth Engine + Gemini vision for tower likelihood.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from threading import Lock

from ai.gee_imagery import fetch_sentinel2_thumb_png
from ai.gemini_vision import analyze_cooling_tower_from_image
from models.building import BuildingRecord, PhysicalAnalysis
from services.settings import get_settings, live_cv_enabled

logger = logging.getLogger(__name__)

# Visible folder name (no leading dot) so it shows up in Finder / IDE sidebars.
_DEBUG_THUMB_DIR = Path(__file__).resolve().parent.parent / "debug_gee_thumbnails"

_cache: dict[str, PhysicalAnalysis] = {}
_cache_lock = Lock()


def _safe_thumb_stem(building_id: str) -> str:
    """Filesystem-safe name for debug PNGs."""
    s = re.sub(r"[^a-zA-Z0-9._-]+", "_", building_id.strip())
    return s[:200] if s else "unknown"


def _maybe_save_gee_thumb(png: bytes, building_id: str) -> None:
    settings = get_settings()
    if not settings.save_gee_thumbnails or not png:
        return
    try:
        _DEBUG_THUMB_DIR.mkdir(parents=True, exist_ok=True)
        path = _DEBUG_THUMB_DIR / f"{_safe_thumb_stem(building_id)}.png"
        path.write_bytes(png)
        logger.info("Saved GEE thumbnail for Gemini to %s", path)
    except OSError as e:
        logger.warning("Could not save GEE debug thumbnail: %s", e)


def _mock_tower(building_id: str) -> tuple[bool, float]:
    h = abs(hash(building_id)) % (2**31)
    detected = (h % 5) != 0
    confidence = 0.55 + (h % 45) / 100.0
    return detected, round(confidence, 2)


def _roof_lineage(record: BuildingRecord) -> tuple[float, str]:
    """
    Confidence and provenance for **catalog** roof catchment (not vision-segmented).

    Higher confidence when area comes from surveyed footprints (e.g. Microsoft Buildings);
    lower for synthetic demo seeds (square footprint derived from area only).
    """
    ds = (record.data_source or "").strip().lower()
    if ds == "microsoft_us_building_footprints" or "microsoft" in ds:
        return 0.88, "microsoft_us_building_footprints"
    if ds == "synthetic_commercial_seed":
        return 0.72, "synthetic_commercial_seed"
    if ds == "synthetic_polygon_from_area":
        return 0.74, "synthetic_polygon_from_area"
    if record.id.startswith("bru-"):
        return 0.72, "synthetic_commercial_seed"
    if record.has_footprint_polygon:
        return 0.84, "catalog_polygon_footprint"
    return 0.68, "catalog_area_only"


def _mock_physical(record: BuildingRecord) -> PhysicalAnalysis:
    catchment = float(record.roof_area_sqft)
    tower_ok, tower_conf = _mock_tower(record.id)
    roof_conf, provenance = _roof_lineage(record)
    return PhysicalAnalysis(
        roof_catchment_sqft=catchment,
        large_roof=catchment >= 100_000,
        roof_confidence=roof_conf,
        roof_catchment_provenance=provenance,
        cooling_tower_detected=tower_ok,
        cooling_tower_confidence=tower_conf,
        imagery_source="none",
        vision_backend="mock",
    )


def _live_physical(record: BuildingRecord) -> PhysicalAnalysis:
    catchment = float(record.roof_area_sqft)
    large = catchment >= 100_000
    roof_conf, provenance = _roof_lineage(record)

    if record.latitude is None or record.longitude is None:
        return _mock_physical(record)

    png = fetch_sentinel2_thumb_png(record.latitude, record.longitude)
    if png:
        _maybe_save_gee_thumb(png, record.id)
    if not png:
        p = _mock_physical(record)
        return p.model_copy(
            update={
                "roof_confidence": round(max(0.0, roof_conf - 0.04), 2),
                "roof_catchment_provenance": provenance,
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

    return PhysicalAnalysis(
        roof_catchment_sqft=catchment,
        large_roof=large,
        roof_confidence=roof_conf,
        roof_catchment_provenance=provenance,
        cooling_tower_detected=tower_ok,
        cooling_tower_confidence=round(max(0.0, min(1.0, tower_note_conf)), 2),
        imagery_source="COPERNICUS/S2_SR_HARMONIZED",
        vision_backend=vision_backend,
    )


def get_physical_analysis(record: BuildingRecord, *, force_live: bool = False) -> PhysicalAnalysis:
    """
    If force_live and live CV is allowed (see ``live_cv_enabled``), run GEE+Gemini (cached per building id).
    Otherwise return fast mock (still uses catalog roof area and >100k flag).
    """
    settings = get_settings()
    key = record.id
    if not force_live or not live_cv_enabled(settings):
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
