from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

TowerStatus = Literal["real_detected", "real_not_detected", "unavailable"]
VisionBackend = Literal["gemini_vision", "none"]
EsgStatus = Literal["unavailable", "real", "proxy"]
ViabilityCompleteness = Literal["full", "partial"]


class PhysicalAnalysis(BaseModel):
    """
    Catalog roof catchment plus optional live Sentinel-2 + Gemini cooling-tower inference.

    Cooling tower fields are None when ``tower_status`` is ``unavailable`` (no fake/hash fallback).
    """

    roof_catchment_sqft: float = Field(..., description="Catchment area used for rainwater math")
    large_roof: bool = Field(..., description="True if catchment >= 100,000 sq ft")
    roof_confidence: float = Field(
        ...,
        ge=0,
        le=1,
        description="Confidence in catalog catchment sq ft (data lineage), not vision-segmented roof",
    )
    roof_catchment_provenance: str = Field(
        ...,
        description="How catchment area was derived (dataset tag), e.g. microsoft_us_building_footprints",
    )
    tower_status: TowerStatus = Field(
        ...,
        description="real_detected | real_not_detected from Gemini on real imagery, or unavailable",
    )
    cooling_tower_detected: bool | None = Field(
        None,
        description="None when tower inference did not run or failed",
    )
    cooling_tower_confidence: float | None = Field(
        None,
        ge=0,
        le=1,
        description="None when tower inference unavailable",
    )
    tower_unavailable_reason: str | None = Field(
        None,
        description="Human-readable reason when tower_status is unavailable",
    )
    imagery_source: str = Field(..., description="COPERNICUS/S2_SR_HARMONIZED or none")
    vision_backend: VisionBackend = Field(
        ...,
        description="gemini_vision only when model produced a parseable result; else none",
    )
    inference_model: str | None = Field(None, description="Gemini model id when inference succeeded")
    inference_timestamp_utc: str | None = Field(None, description="ISO-8601 UTC when inference completed")
    imagery_date_range: str | None = Field(
        None,
        description="Date range of Sentinel-2 composite used for the chip (GEE filter)",
    )
    imagery_provider: str | None = Field(
        None,
        description="e.g. Google Earth Engine for Sentinel-2",
    )
    selected_roof_source: str = Field(
        ...,
        description="Selected catchment lineage: cv, or catalog baseline (e.g. microsoft_us_building_footprints)",
    )
    selected_cooling_tower_source: str = Field(
        ...,
        description="cv_live | cv_stored | unavailable",
    )
    raw_sources_available: dict[str, object] = Field(
        default_factory=dict,
        description="Catalog vs CV field availability for transparency",
    )


class BuildingRecord(BaseModel):
    """Row from buildings dataset (Postgres or CSV fallback)."""

    id: str
    name: str
    state: str = Field(..., min_length=2, max_length=2, description="US state code, e.g. TX")
    city: str | None = None
    county: str | None = None
    geocode_display_name: str | None = Field(
        None,
        description="Human-readable location from Nominatim reverse geocode (when ingested)",
    )
    roof_area_sqft: float = Field(..., gt=0, description="Effective catchment area (MVP: equals footprint)")
    latitude: float | None = Field(None, description="Map pin; prefer DB + seed when using Postgres")
    longitude: float | None = Field(None, description="Map pin; prefer DB + seed when using Postgres")
    data_source: str | None = Field(
        None,
        description="Optional dataset tag from ingest (e.g. microsoft_us_building_footprints)",
    )
    has_footprint_polygon: bool = Field(
        False,
        description="True when a footprint multipolygon exists (WKT in CSV or PostGIS geom)",
    )
    company_id: str | None = Field(
        None,
        description="FK to companies.id when present (Postgres or buildings.csv); canonical ESG join key",
    )
    # Persisted CV snapshot (Postgres); CSV mode leaves these unset
    roof_area_sqft_cv: float | None = Field(None, description="Vision/ML roof area when stored")
    roof_area_confidence_cv: float | None = Field(None, ge=0, le=1)
    cooling_tower_detected_cv: bool | None = Field(None)
    cooling_tower_confidence_cv: float | None = Field(None, ge=0, le=1)
    cv_inference_at: datetime | None = None
    cv_source: str | None = Field(None, description="e.g. gee_sentinel2_gemini")
    cv_inference_model: str | None = Field(None, description="Gemini model id when applicable")


class BuildingEnriched(BaseModel):
    """API payload for frontend."""

    id: str
    name: str
    state: str
    city: str | None
    company_id: str | None = Field(
        None,
        description="Same as catalog building row; use for company-level ESG join",
    )
    roof_area_sqft: float
    latitude: float | None = None
    longitude: float | None = None
    rainfall_inches_annual: float
    water_price_per_1000_gal_usd: float
    rainwater_potential_gallons: float
    annual_water_savings: float = Field(..., description="USD/year: (gallons/1000) × state water $/1000 gal")
    viability_score: float = Field(..., ge=0, le=100)
    viability_breakdown: dict[str, float] = Field(
        ...,
        description="Normalized pillar scores 0–100; cooling_tower omitted when unavailable",
    )
    viability_completeness: ViabilityCompleteness = Field(
        ...,
        description="full = tower pillar included; partial = tower unavailable (ESG optional either way)",
    )
    viability_missing_components: list[str] = Field(
        default_factory=list,
        description="e.g. cooling_tower when live CV did not produce a result",
    )
    cooling_tower_detected: bool | None = Field(
        None,
        description="Mirrors physical_analysis; None when tower inference unavailable",
    )
    cooling_tower_confidence: float | None = Field(None, ge=0, le=1)
    esg_score: float | None = Field(None, description="0–100 ESG subscore when SBTi/proxy data present")
    esg_source: str | None = Field(None, description="e.g. SBTi, documented_industry_proxy")
    esg_confidence: float | None = Field(None, ge=0, le=1, description="0–1 confidence in ESG subscore")
    esg_status: EsgStatus = Field("unavailable", description="real | proxy | unavailable")
    esg_details: dict[str, object] = Field(default_factory=dict, description="Provenance payload from DB/ingest")
    esg_signal_score: float | None = Field(
        None,
        description="Deprecated mirror of esg_score for older clients",
    )
    esg_unavailable_reason: str | None = Field(
        None,
        description="Why ESG is unavailable for this building",
    )
    physical_analysis: PhysicalAnalysis
    data_notes: str = (
        "Roof catchment uses explicit selection: valid CV snapshot when present, else catalog baseline "
        "(e.g. US Building Footprints), else synthetic lineage (see provenance.physical_selection). "
        "Viability uses state_context rainfall and water price from Postgres or CSV; "
        "cooling tower subscore when live CV or persisted CV snapshot yields real_detected/real_not_detected; "
        "optional ESG weight 0.10 when company_sustainability_profiles has SBTi (or documented proxy)."
    )
    provenance: dict[str, object] = Field(
        default_factory=dict,
        description="Structured source + formula metadata for this response",
    )
