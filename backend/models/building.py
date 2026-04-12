from pydantic import BaseModel, Field


class PhysicalAnalysis(BaseModel):
    """Satellite + vision (or mock) outputs for prospecting rubric."""

    roof_catchment_sqft: float = Field(..., description="Catchment area used for rainwater math")
    large_roof: bool = Field(..., description="True if catchment >= 100,000 sq ft")
    roof_confidence: float = Field(
        ...,
        ge=0,
        le=1,
        description="Confidence in catchment (catalog lineage or Gemini roof estimate)",
    )
    roof_catchment_provenance: str = Field(
        ...,
        description="How catchment was derived, e.g. gemini_static_maps_satellite, catalog_area_only",
    )
    cooling_tower_detected: bool
    cooling_tower_confidence: float = Field(..., ge=0, le=1)
    imagery_source: str = Field(
        ...,
        description="google_static_maps | none (legacy EE chips are no longer used for live_cv)",
    )
    vision_backend: str = Field(..., description="gemini_vision | mock")
    roof_area_estimated_cv: float | None = Field(
        default=None,
        description="Raw Gemini estimated roof sq ft before fallback to catalog",
    )
    cv_reasoning: str | None = Field(default=None, description="Short model rationale when live CV ran")


class BuildingRecord(BaseModel):
    """Row from buildings dataset (Postgres or CSV fallback)."""

    id: str
    name: str
    state: str = Field(..., min_length=2, max_length=2, description="US state code, e.g. TX")
    city: str | None = None
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


class BuildingEnriched(BaseModel):
    """API payload for frontend."""

    id: str
    name: str
    state: str
    city: str | None
    roof_area_sqft: float
    latitude: float | None = None
    longitude: float | None = None
    rainfall_inches_annual: float
    water_price_per_1000_gal_usd: float
    rainwater_potential_gallons: float
    annual_water_savings: float = Field(..., description="USD/year proxy: (gallons/1000) × state water $/1000 gal")
    viability_score: float = Field(..., ge=0, le=100)
    viability_breakdown: dict[str, float]
    cooling_tower_detected: bool
    cooling_tower_confidence: float = Field(..., ge=0, le=1)
    esg_signal_score: float = Field(..., ge=0, le=100, description="Mock ESG / sustainability signal 0–100")
    physical_analysis: PhysicalAnalysis
    roof_area_sqft_catalog: float | None = Field(
        default=None,
        description="Original catalog roof_area_sqft; set when live_cv was requested for comparison",
    )
    roof_area_estimated_cv: float | None = Field(
        default=None,
        description="Gemini roof estimate from Static Maps chip (may match physical_analysis.roof_area_estimated_cv)",
    )
    cv_reasoning: str | None = Field(default=None, description="Gemini reasoning when live CV succeeded")
    data_notes: str = "See GET /building/{id} and optional ?live_cv=true for Static Maps + Gemini."
