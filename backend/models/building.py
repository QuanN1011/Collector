from pydantic import BaseModel, Field


class PhysicalAnalysis(BaseModel):
    """Satellite + vision (or mock) outputs for prospecting rubric."""

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
        description="How catchment area was derived, e.g. synthetic_seed, catalog_polygon_footprint",
    )
    cooling_tower_detected: bool
    cooling_tower_confidence: float = Field(..., ge=0, le=1)
    imagery_source: str = Field(..., description="COPERNICUS/S2_SR_HARMONIZED or none")
    vision_backend: str = Field(..., description="gemini_vision | mock")


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
    data_notes: str = (
        "Roof catchment from catalog/footprint data (see physical_analysis.roof_catchment_provenance); "
        "live CV targets cooling-tower cues only, not roof segmentation."
    )
