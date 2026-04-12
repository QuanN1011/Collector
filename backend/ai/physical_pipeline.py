"""
Physical prospecting signals for catalog buildings.

- Default: catalog roof area + mock cooling signal (fast).
- ``live_cv=true`` (when enabled): Google **Static Maps** satellite chip + **Gemini** roof/tower
  analysis; results cached in ``building_cv_analysis`` (Postgres) or in-memory (CSV mode).
"""

from __future__ import annotations

import logging
from typing import Any

from ai.gemini_roof_analysis import analyze_building_satellite
from database.cv_analysis_cache import CvAnalysisSnapshot, get_cached_cv_analysis, save_cached_cv_analysis
from models.building import BuildingRecord, PhysicalAnalysis
from services.settings import get_settings, live_cv_enabled
from services.satellite import get_satellite_image

logger = logging.getLogger(__name__)

_MIN_TRUSTED_SQFT = 5_000.0


def _mock_tower(building_id: str) -> tuple[bool, float]:
    h = abs(hash(building_id)) % (2**31)
    detected = (h % 5) != 0
    confidence = 0.55 + (h % 45) / 100.0
    return detected, round(confidence, 2)


def _roof_lineage(record: BuildingRecord) -> tuple[float, str]:
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
        roof_area_estimated_cv=None,
        cv_reasoning=None,
    )


def _catchment_from_cv(catalog: float, analyzed: dict[str, Any]) -> tuple[float, str, float | None]:
    """Choose catchment sq ft and provenance; return (sqft, provenance, estimated_cv or None)."""
    est = float(analyzed.get("estimated_roof_sqft") or 0.0)
    if est >= _MIN_TRUSTED_SQFT:
        return est, "gemini_static_maps_satellite", est
    return catalog, "catalog_fallback_low_cv_confidence", est if est > 0 else None


def _physical_from_snapshot(record: BuildingRecord, snap: CvAnalysisSnapshot) -> PhysicalAnalysis:
    catalog = float(record.roof_area_sqft)
    analyzed = {
        "roof_large": snap.roof_large_flag,
        "cooling_tower_detected": snap.cooling_tower_detected,
        "roof_confidence": snap.roof_confidence,
        "cooling_tower_confidence": snap.cooling_tower_confidence,
        "estimated_roof_sqft": snap.roof_estimated_sqft,
        "reasoning": snap.reasoning,
    }
    return _build_physical(record, analyzed)


def _build_physical(record: BuildingRecord, analyzed: dict[str, Any]) -> PhysicalAnalysis:
    catalog = float(record.roof_area_sqft)
    catchment, provenance, est_cv = _catchment_from_cv(catalog, analyzed)
    large = bool(analyzed.get("roof_large")) or catchment >= 100_000
    tower_ok = bool(analyzed.get("cooling_tower_detected"))
    tower_conf = float(analyzed.get("cooling_tower_confidence", 0.5))
    tower_conf = round(max(0.0, min(1.0, tower_conf)), 2)
    roof_conf = float(analyzed.get("roof_confidence", 0.5))
    roof_conf = round(max(0.0, min(1.0, roof_conf)), 2)
    reasoning = (analyzed.get("reasoning") or "").strip() or None

    return PhysicalAnalysis(
        roof_catchment_sqft=catchment,
        large_roof=large,
        roof_confidence=roof_conf,
        roof_catchment_provenance=provenance,
        cooling_tower_detected=tower_ok,
        cooling_tower_confidence=tower_conf,
        imagery_source="google_static_maps",
        vision_backend="gemini_vision",
        roof_area_estimated_cv=est_cv,
        cv_reasoning=reasoning,
    )


def _live_physical(record: BuildingRecord) -> PhysicalAnalysis:
    cached = get_cached_cv_analysis(record.id)
    if cached is not None:
        return _physical_from_snapshot(record, cached)

    if record.latitude is None or record.longitude is None:
        logger.info("Live CV skipped: no coordinates for %s", record.id)
        return _mock_physical(record)

    try:
        png = get_satellite_image(float(record.latitude), float(record.longitude))
    except Exception as e:
        logger.warning("Static Maps fetch failed for %s: %s", record.id, e)
        return _mock_physical(record)

    analyzed = analyze_building_satellite(png)
    if analyzed is None:
        logger.info("Gemini roof analysis returned no result for %s", record.id)
        p = _mock_physical(record)
        return p.model_copy(
            update={
                "imagery_source": "google_static_maps",
                "vision_backend": "mock",
            }
        )

    catalog = float(record.roof_area_sqft)
    _, _, est_cv = _catchment_from_cv(catalog, analyzed)
    store_sqft = float(analyzed.get("estimated_roof_sqft") or 0.0)
    if store_sqft < _MIN_TRUSTED_SQFT:
        store_sqft = catalog

    try:
        save_cached_cv_analysis(
            record.id,
            roof_estimated_sqft=store_sqft,
            roof_large_flag=bool(analyzed.get("roof_large")),
            cooling_tower_detected=bool(analyzed.get("cooling_tower_detected")),
            roof_confidence=float(analyzed.get("roof_confidence", 0.5)),
            cooling_tower_confidence=float(analyzed.get("cooling_tower_confidence", 0.5)),
            reasoning=str(analyzed.get("reasoning") or ""),
        )
    except Exception as e:
        logger.warning("Could not persist CV cache for %s: %s", record.id, e)

    return _build_physical(record, analyzed)


def get_physical_analysis(record: BuildingRecord, *, force_live: bool = False) -> PhysicalAnalysis:
    """
    If ``force_live`` and live CV is allowed, run Static Maps + Gemini (cached per building id).
    Otherwise return fast mock (catalog roof area and mock tower).
    """
    settings = get_settings()
    if not force_live or not live_cv_enabled(settings):
        return _mock_physical(record)

    try:
        return _live_physical(record)
    except Exception as e:
        logger.exception("Live physical analysis failed: %s", e)
        return _mock_physical(record)
