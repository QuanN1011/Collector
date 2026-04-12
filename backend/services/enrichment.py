from models.building import BuildingEnriched, BuildingRecord
from ai.cooling_tower_detection import detect_cooling_tower
from database.db import StateContext, get_state_context, get_stored_final_viability_standalone
from services.rainwater import annual_rainwater_gallons
from services.roi import annual_water_savings_usd
from services.scoring import compute_viability, mock_esg_subscore


def enrich_building(record: BuildingRecord, state_ctx: StateContext | None = None) -> BuildingEnriched:
    ctx = state_ctx or get_state_context(record.state)
    gallons = annual_rainwater_gallons(record.roof_area_sqft, ctx.rainfall_inches_annual)
    savings = annual_water_savings_usd(gallons, ctx.water_price_per_1000_gal_usd)
    tower_ok, tower_conf = detect_cooling_tower(record.id)
    score, breakdown = compute_viability(
        roof_area_sqft=record.roof_area_sqft,
        rainfall_inches_annual=ctx.rainfall_inches_annual,
        water_price_per_1000_gal_usd=ctx.water_price_per_1000_gal_usd,
        cooling_tower_detected=tower_ok,
        cooling_tower_confidence=tower_conf,
        building_id=record.id,
    )
    stored_final = get_stored_final_viability_standalone(record.id)
    if stored_final is not None:
        score = stored_final
    esg = mock_esg_subscore(record.id)

    return BuildingEnriched(
        id=record.id,
        name=record.name,
        state=record.state,
        city=record.city,
        roof_area_sqft=record.roof_area_sqft,
        latitude=record.latitude,
        longitude=record.longitude,
        rainfall_inches_annual=ctx.rainfall_inches_annual,
        water_price_per_1000_gal_usd=ctx.water_price_per_1000_gal_usd,
        rainwater_potential_gallons=round(gallons, 2),
        annual_water_savings=round(savings, 2),
        viability_score=score,
        viability_breakdown=breakdown,
        cooling_tower_detected=tower_ok,
        cooling_tower_confidence=tower_conf,
        esg_signal_score=round(esg, 2),
    )
