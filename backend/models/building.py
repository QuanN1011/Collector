from pydantic import BaseModel, Field


class PhysicalAnalysis(BaseModel):
    """Satellite + vision (or mock) outputs for prospecting rubric."""

    roof_catchment_sqft: float = Field(..., description="Catchment area used for rainwater math")
    large_roof: bool = Field(..., description="True if catchment >= 100,000 sq ft")
    roof_confidence: float = Field(..., ge=0, le=1)
    cooling_tower_detected: bool
    cooling_tower_confidence: float = Field(..., ge=0, le=1)
    imagery_source: str = Field(..., description="COPERNICUS/S2_SR_HARMONIZED or none")
    vision_backend: str = Field(..., description="gemini_vision | mock")


class BuildingRecord(BaseModel):
    """Row from buildings dataset (CSV → DB later)."""

    id: str
    name: str
    state: str = Field(..., min_length=2, max_length=2, description="US state code, e.g. TX")
    city: str | None = None
    roof_area_sqft: float = Field(..., gt=0, description="Catalog footprint / catchment (Open Buildings–style)")
    latitude: float | None = Field(default=None, description="WGS84 for GEE chip center")
    longitude: float | None = Field(default=None, description="WGS84 for GEE chip center")


class BuildingEnriched(BaseModel):
    """API payload for frontend."""

    id: str
    name: str
    state: str
    city: str | None
    roof_area_sqft: float
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
        "Roof area from building dataset; optional live CV uses GEE Sentinel-2 + Gemini when enabled in .env."
    )
