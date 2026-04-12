from models.building import BuildingEnriched, BuildingRecord
from ai.physical_pipeline import get_physical_analysis
from database.db import StateContext, get_state_context
from services.rainwater import annual_rainwater_gallons
from services.roi import annual_water_savings_usd
from services.scoring import compute_viability, mock_esg_subscore


def enrich_building(record: BuildingRecord, state_ctx: StateContext | None = None, *, live_cv: bool = False) -> BuildingEnriched:
    ctx = state_ctx or get_state_context(record.state)
    physical = get_physical_analysis(record, force_live=live_cv)
    catchment = physical.roof_catchment_sqft

    gallons = annual_rainwater_gallons(catchment, ctx.rainfall_inches_annual)
    savings = annual_water_savings_usd(gallons, ctx.water_price_per_1000_gal_usd)
    score, breakdown = compute_viability(
        roof_area_sqft=catchment,
        rainfall_inches_annual=ctx.rainfall_inches_annual,
        water_price_per_1000_gal_usd=ctx.water_price_per_1000_gal_usd,
        cooling_tower_detected=physical.cooling_tower_detected,
        cooling_tower_confidence=physical.cooling_tower_confidence,
        building_id=record.id,
    )
    esg = mock_esg_subscore(record.id)

    return BuildingEnriched(
        id=record.id,
        name=record.name,
        state=record.state,
        city=record.city,
        roof_area_sqft=record.roof_area_sqft,
        rainfall_inches_annual=ctx.rainfall_inches_annual,
        water_price_per_1000_gal_usd=ctx.water_price_per_1000_gal_usd,
        rainwater_potential_gallons=round(gallons, 2),
        annual_water_savings=round(savings, 2),
        viability_score=score,
        viability_breakdown=breakdown,
        cooling_tower_detected=physical.cooling_tower_detected,
        cooling_tower_confidence=physical.cooling_tower_confidence,
        esg_signal_score=round(esg, 2),
        physical_analysis=physical,
    )
