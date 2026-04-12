"""
Explicit source selection for roof catchment and cooling tower (catalog / US footprints vs CV snapshot).

Catalog ``roof_area_sqft`` and ``data_source`` are never overwritten; CV values live in separate columns.
"""

from __future__ import annotations

from typing import Any

from models.building import BuildingRecord

# CV roof must clear confidence and pass crude plausibility before overriding Microsoft/catalog baseline.
MIN_ROOF_CV_CONFIDENCE = 0.6
MIN_ROOF_SQFT = 1_000.0
MAX_ROOF_SQFT = 50_000_000.0


def roof_lineage_catalog(record: BuildingRecord) -> tuple[float, str]:
    """
    Confidence and provenance label for **baseline** roof catchment (catalog / footprints), not vision roof.
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


def select_roof_catchment(record: BuildingRecord) -> tuple[float, float, str, str, dict[str, Any]]:
    """
    Returns:
        catchment_sqft, roof_confidence, roof_catchment_provenance string,
        selected_roof_source key, detail dict for provenance.
    """
    baseline = float(record.roof_area_sqft)
    cv_sqft = record.roof_area_sqft_cv
    cv_conf = record.roof_area_confidence_cv

    base_conf, base_prov = roof_lineage_catalog(record)
    raw: dict[str, Any] = {
        "catalog_roof_area_sqft": baseline,
        "catalog_lineage": base_prov,
        "cv_roof_area_sqft": cv_sqft,
        "cv_roof_confidence": cv_conf,
    }

    if (
        cv_sqft is not None
        and cv_conf is not None
        and cv_conf >= MIN_ROOF_CV_CONFIDENCE
        and MIN_ROOF_SQFT <= cv_sqft <= MAX_ROOF_SQFT
    ):
        raw["selected"] = "cv"
        raw["reject_reason"] = None
        return (
            float(cv_sqft),
            float(cv_conf),
            f"cv:{record.cv_source or 'vision'}",
            "cv",
            raw,
        )

    reject: str | None = None
    if cv_sqft is not None or cv_conf is not None:
        if cv_sqft is None or cv_conf is None:
            reject = "cv_partial_or_missing"
        elif cv_conf < MIN_ROOF_CV_CONFIDENCE:
            reject = "cv_confidence_below_threshold"
        elif not (MIN_ROOF_SQFT <= cv_sqft <= MAX_ROOF_SQFT):
            reject = "cv_value_failed_range_check"
        raw["reject_reason"] = reject

    raw["selected"] = base_prov
    return baseline, base_conf, base_prov, base_prov, raw


def stored_tower_snapshot_valid(record: BuildingRecord) -> bool:
    """True when a completed CV tower snapshot exists (no fabricated negatives)."""
    if record.cooling_tower_detected_cv is None:
        return False
    if record.cooling_tower_confidence_cv is None:
        return False
    c = float(record.cooling_tower_confidence_cv)
    return 0.0 <= c <= 1.0
