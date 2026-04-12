"""
Physical prospecting signals: roof catchment from catalog + optional CV snapshot; Sentinel-2 + Gemini tower.

- Baseline roof area stays in ``buildings.roof_area_sqft`` (e.g. Microsoft US Building Footprints).
- Optional CV roof/tower snapshots live in separate columns; selection prefers valid CV over baseline.
- Live path: Sentinel-2 chip via Earth Engine + Gemini vision for tower when enabled.
"""

from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock

from ai.gee_imagery import fetch_sentinel2_thumb_png, last_earth_engine_init_error
from ai.gemini_vision import analyze_cooling_tower_from_image
from models.building import BuildingRecord, PhysicalAnalysis
from services.physical_selection import select_roof_catchment, stored_tower_snapshot_valid
from services.settings import get_settings, live_cv_enabled

logger = logging.getLogger(__name__)

SENTINEL2_IMAGERY_DATE_RANGE = "2023-01-01..2024-12-31"
IMAGERY_PROVIDER_LABEL = "Google Earth Engine (Sentinel-2 SR harmonized)"

_DEBUG_THUMB_DIR = Path(__file__).resolve().parent.parent / "debug_gee_thumbnails"

_cache: dict[str, PhysicalAnalysis] = {}
_cache_lock = Lock()


def _safe_thumb_stem(building_id: str) -> str:
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


def _raw_sources_available(record: BuildingRecord) -> dict[str, object]:
    ts = record.cv_inference_at
    return {
        "catalog_roof_area_sqft": record.roof_area_sqft,
        "catalog_data_source": record.data_source,
        "roof_area_sqft_cv": record.roof_area_sqft_cv,
        "roof_area_confidence_cv": record.roof_area_confidence_cv,
        "cooling_tower_detected_cv": record.cooling_tower_detected_cv,
        "cooling_tower_confidence_cv": record.cooling_tower_confidence_cv,
        "cv_inference_at": ts.isoformat() if isinstance(ts, datetime) else ts,
        "cv_source": record.cv_source,
        "cv_inference_model": record.cv_inference_model,
    }


def _physical_from_stored_cv(
    record: BuildingRecord,
    *,
    catchment: float,
    roof_conf: float,
    roof_prov: str,
    selected_roof_source: str,
    roof_detail: dict[str, object],
    large: bool,
) -> PhysicalAnalysis:
    tower_ok = bool(record.cooling_tower_detected_cv)
    tower_conf = float(record.cooling_tower_confidence_cv or 0.0)
    tower_conf = round(max(0.0, min(1.0, tower_conf)), 2)
    status = "real_detected" if tower_ok else "real_not_detected"
    ts = record.cv_inference_at
    ts_str = ts.isoformat() if isinstance(ts, datetime) else (ts if isinstance(ts, str) else None)

    raw = _raw_sources_available(record)
    raw["roof_selection_detail"] = roof_detail

    return PhysicalAnalysis(
        roof_catchment_sqft=catchment,
        large_roof=large,
        roof_confidence=roof_conf,
        roof_catchment_provenance=roof_prov,
        tower_status=status,
        cooling_tower_detected=tower_ok,
        cooling_tower_confidence=tower_conf,
        tower_unavailable_reason=None,
        imagery_source="none",
        vision_backend="none",
        inference_model=record.cv_inference_model,
        inference_timestamp_utc=ts_str,
        imagery_date_range=None,
        imagery_provider=None,
        selected_roof_source=selected_roof_source,
        selected_cooling_tower_source="cv_stored",
        raw_sources_available=raw,
    )


def _catalog_physical(
    record: BuildingRecord,
    *,
    catchment: float,
    roof_conf: float,
    roof_prov: str,
    selected_roof_source: str,
    roof_detail: dict[str, object],
    large: bool,
    tower_reason: str | None = None,
) -> PhysicalAnalysis:
    reason = tower_reason or (
        "Cooling tower inference not run: request live_cv=false or ENABLE_LIVE_CV is not enabled. "
        "Use GET /building/{id}?live_cv=true with Earth Engine + GEMINI_API_KEY for real_detected/real_not_detected."
    )
    raw = _raw_sources_available(record)
    raw["roof_selection_detail"] = roof_detail
    return PhysicalAnalysis(
        roof_catchment_sqft=catchment,
        large_roof=large,
        roof_confidence=roof_conf,
        roof_catchment_provenance=roof_prov,
        tower_status="unavailable",
        cooling_tower_detected=None,
        cooling_tower_confidence=None,
        tower_unavailable_reason=reason,
        imagery_source="none",
        vision_backend="none",
        inference_model=None,
        inference_timestamp_utc=None,
        imagery_date_range=None,
        imagery_provider=None,
        selected_roof_source=selected_roof_source,
        selected_cooling_tower_source="unavailable",
        raw_sources_available=raw,
    )


def _live_physical(
    record: BuildingRecord,
    *,
    catchment: float,
    roof_conf: float,
    roof_prov: str,
    selected_roof_source: str,
    roof_detail: dict[str, object],
    large: bool,
) -> PhysicalAnalysis:
    settings = get_settings()
    raw = _raw_sources_available(record)
    raw["roof_selection_detail"] = roof_detail

    if record.latitude is None or record.longitude is None:
        return _catalog_physical(
            record,
            catchment=catchment,
            roof_conf=roof_conf,
            roof_prov=roof_prov,
            selected_roof_source=selected_roof_source,
            roof_detail=roof_detail,
            large=large,
            tower_reason="Building record is missing latitude/longitude; cannot fetch Sentinel-2 imagery.",
        )

    png = fetch_sentinel2_thumb_png(record.latitude, record.longitude)
    if png:
        _maybe_save_gee_thumb(png, record.id)

    if not png:
        init_err = last_earth_engine_init_error()
        if init_err:
            thumb_reason = (
                "Earth Engine did not initialize; cannot fetch Sentinel-2 thumbnail. "
                f"Detail: {init_err}"
            )
        else:
            thumb_reason = (
                "Sentinel-2 thumbnail unavailable from Earth Engine "
                "(check GEE_PROJECT_ID, credentials, network, or earthengine-api)."
            )
        roof_conf_adj = round(max(0.0, roof_conf - 0.04), 2)
        return PhysicalAnalysis(
            roof_catchment_sqft=catchment,
            large_roof=large,
            roof_confidence=roof_conf_adj,
            roof_catchment_provenance=roof_prov,
            tower_status="unavailable",
            cooling_tower_detected=None,
            cooling_tower_confidence=None,
            tower_unavailable_reason=thumb_reason,
            imagery_source="none",
            vision_backend="none",
            inference_model=None,
            inference_timestamp_utc=None,
            imagery_date_range=SENTINEL2_IMAGERY_DATE_RANGE,
            imagery_provider=IMAGERY_PROVIDER_LABEL,
            selected_roof_source=selected_roof_source,
            selected_cooling_tower_source="unavailable",
            raw_sources_available=raw,
        )

    tower = analyze_cooling_tower_from_image(png)
    ts = datetime.now(timezone.utc).isoformat()
    if tower is None:
        return PhysicalAnalysis(
            roof_catchment_sqft=catchment,
            large_roof=large,
            roof_confidence=roof_conf,
            roof_catchment_provenance=roof_prov,
            tower_status="unavailable",
            cooling_tower_detected=None,
            cooling_tower_confidence=None,
            tower_unavailable_reason=(
                "Gemini vision returned no parseable result (missing GEMINI_API_KEY, API error, or invalid JSON)."
            ),
            imagery_source="COPERNICUS/S2_SR_HARMONIZED",
            vision_backend="none",
            inference_model=settings.gemini_model,
            inference_timestamp_utc=ts,
            imagery_date_range=SENTINEL2_IMAGERY_DATE_RANGE,
            imagery_provider=IMAGERY_PROVIDER_LABEL,
            selected_roof_source=selected_roof_source,
            selected_cooling_tower_source="unavailable",
            raw_sources_available=raw,
        )

    tower_ok, tower_conf = tower
    tower_conf = round(max(0.0, min(1.0, tower_conf)), 2)
    status = "real_detected" if tower_ok else "real_not_detected"

    return PhysicalAnalysis(
        roof_catchment_sqft=catchment,
        large_roof=large,
        roof_confidence=roof_conf,
        roof_catchment_provenance=roof_prov,
        tower_status=status,
        cooling_tower_detected=tower_ok,
        cooling_tower_confidence=tower_conf,
        tower_unavailable_reason=None,
        imagery_source="COPERNICUS/S2_SR_HARMONIZED",
        vision_backend="gemini_vision",
        inference_model=settings.gemini_model,
        inference_timestamp_utc=ts,
        imagery_date_range=SENTINEL2_IMAGERY_DATE_RANGE,
        imagery_provider=IMAGERY_PROVIDER_LABEL,
        selected_roof_source=selected_roof_source,
        selected_cooling_tower_source="cv_live",
        raw_sources_available=raw,
    )


def get_physical_analysis(record: BuildingRecord, *, force_live: bool = False) -> PhysicalAnalysis:
    """
    Roof catchment uses explicit selection (CV when valid, else catalog baseline e.g. US footprints).

    Cooling tower: live Gemini when ``force_live`` and ``live_cv_enabled``; else persisted CV snapshot
    if present; else unavailable (no fabricated negatives).
    """
    settings = get_settings()
    catchment, roof_conf, roof_prov, selected_roof_source, roof_detail = select_roof_catchment(record)
    large = catchment >= 100_000
    key = record.id

    if not force_live or not live_cv_enabled(settings):
        if stored_tower_snapshot_valid(record):
            return _physical_from_stored_cv(
                record,
                catchment=catchment,
                roof_conf=roof_conf,
                roof_prov=roof_prov,
                selected_roof_source=selected_roof_source,
                roof_detail=roof_detail,
                large=large,
            )
        return _catalog_physical(
            record,
            catchment=catchment,
            roof_conf=roof_conf,
            roof_prov=roof_prov,
            selected_roof_source=selected_roof_source,
            roof_detail=roof_detail,
            large=large,
        )

    cache_key = f"{key}:{catchment:.4f}:{selected_roof_source}"
    with _cache_lock:
        if cache_key in _cache:
            return _cache[cache_key]

    try:
        result = _live_physical(
            record,
            catchment=catchment,
            roof_conf=roof_conf,
            roof_prov=roof_prov,
            selected_roof_source=selected_roof_source,
            roof_detail=roof_detail,
            large=large,
        )
    except Exception as e:
        logger.exception("Live physical analysis failed: %s", e)
        result = _catalog_physical(
            record,
            catchment=catchment,
            roof_conf=roof_conf,
            roof_prov=roof_prov,
            selected_roof_source=selected_roof_source,
            roof_detail=roof_detail,
            large=large,
            tower_reason="Live physical analysis raised an exception; see server logs for details.",
        )

    if result.tower_status in ("real_detected", "real_not_detected"):
        with _cache_lock:
            _cache[cache_key] = result
        return result

    if stored_tower_snapshot_valid(record):
        return _physical_from_stored_cv(
            record,
            catchment=catchment,
            roof_conf=roof_conf,
            roof_prov=roof_prov,
            selected_roof_source=selected_roof_source,
            roof_detail=roof_detail,
            large=large,
        )

    return result
