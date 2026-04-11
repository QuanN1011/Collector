from pydantic import BaseModel, Field


class BuildingRecord(BaseModel):
    """Row from buildings dataset (Postgres or CSV fallback)."""

    id: str
    name: str
    state: str = Field(..., min_length=2, max_length=2, description="US state code, e.g. TX")
    city: str | None = None
    roof_area_sqft: float = Field(..., gt=0, description="Effective catchment area (MVP: equals footprint)")
    latitude: float | None = Field(None, description="Map pin; prefer DB + seed when using Postgres")
    longitude: float | None = Field(None, description="Map pin; prefer DB + seed when using Postgres")


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
    data_notes: str = "MVP: footprint used as roof; water price and rainfall are state averages."
