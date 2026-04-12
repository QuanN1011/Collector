"""
Address → Geocode → Static Map → Gemini → rainwater / savings / viability.

``GET /analyze-building?address=...&state=TX``
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from database.db import get_state_context
from services.gemini_service import GeminiOverloadedError, GeminiQuotaError, analyze_building_image
from services.maps.maps_service import get_coordinates, get_satellite_image
from services.rainwater_service import calculate_rainwater
from services.roi import annual_water_savings_usd
from services.viability_service import calculate_viability

router = APIRouter(tags=["building-analysis"])

ROOF_DEFAULT_SQFT: dict[str, float] = {
    "small": 35_000.0,
    "medium": 80_000.0,
    "large": 150_000.0,
}


class AnalyzeBuildingResponse(BaseModel):
    building_name: str = Field(description="Geocoded label or fallback")
    address: str
    lat: float
    lng: float
    satellite_image: str = Field(description="Google Static Maps URL (PNG satellite)")
    roof_estimate: str
    roof_area_sqft: float
    cooling_tower_detected: bool
    cooling_tower_confidence: float
    rainwater_potential_gallons: float
    annual_water_savings: float
    viability_score: float


@router.get("/analyze-building", response_model=AnalyzeBuildingResponse)
def analyze_building(
    address: str = Query(..., min_length=3, description="Street address to geocode"),
    state: str = Query(
        "TX",
        min_length=2,
        max_length=2,
        description="USPS state code for rainfall and water rate (from state_context)",
    ),
) -> AnalyzeBuildingResponse:
    state = state.strip().upper()
    try:
        ctx = get_state_context(state)
    except (KeyError, ValueError) as e:
        raise HTTPException(
            status_code=400,
            detail=f"No state context for {state}. Use a seeded state or fix state_context.",
        ) from e

    try:
        geo = get_coordinates(address)
        lat = float(geo["lat"])
        lng = float(geo["lng"])
        building_name = str(geo.get("formatted_address") or address.strip())
        satellite_url = get_satellite_image(lat, lng)
        vision = analyze_building_image(satellite_url)
    except GeminiQuotaError as e:
        headers = {}
        if e.retry_after is not None:
            headers["Retry-After"] = str(e.retry_after)
        raise HTTPException(status_code=429, detail=str(e), headers=headers or None) from e
    except GeminiOverloadedError as e:
        h: dict[str, str] = {}
        if e.retry_after is not None:
            h["Retry-After"] = str(e.retry_after)
        raise HTTPException(status_code=503, detail=str(e), headers=h if h else None) from e
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e)) from e

    raw_sq = vision.get("roof_area_sqft_estimate")
    if raw_sq is not None and isinstance(raw_sq, (int, float)) and float(raw_sq) > 0:
        roof_sqft = float(raw_sq)
    else:
        roof_sqft = ROOF_DEFAULT_SQFT[vision["roof_estimate"]]

    tower_conf = float(vision["confidence"])
    gallons = calculate_rainwater(roof_sqft, ctx.rainfall_inches_annual)
    savings = annual_water_savings_usd(gallons, ctx.water_price_per_1000_gal_usd)
    viability = calculate_viability(
        {
            "roof_area_sqft": roof_sqft,
            "rainfall_inches_annual": ctx.rainfall_inches_annual,
            "water_price_per_1000_gal_usd": ctx.water_price_per_1000_gal_usd,
            "cooling_tower_detected": vision["cooling_tower_detected"],
            "cooling_tower_confidence": tower_conf,
        }
    )

    return AnalyzeBuildingResponse(
        building_name=building_name,
        address=address.strip(),
        lat=lat,
        lng=lng,
        satellite_image=satellite_url,
        roof_estimate=vision["roof_estimate"],
        roof_area_sqft=roof_sqft,
        cooling_tower_detected=vision["cooling_tower_detected"],
        cooling_tower_confidence=tower_conf,
        rainwater_potential_gallons=round(gallons, 2),
        annual_water_savings=round(savings, 2),
        viability_score=viability,
    )
