from models.building import BuildingEnriched, BuildingRecord
from ai.physical_pipeline import get_physical_analysis
from database.db import StateContext, get_state_context, get_stored_final_viability_standalone
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
    stored_final = get_stored_final_viability_standalone(record.id)
    # Detail with Satellite + AI uses computed score so CV/mock physical can move the headline.
    if stored_final is not None and not live_cv:
        score = stored_final
    esg = mock_esg_subscore(record.id)

    if not live_cv:
        data_notes = (
            "Catalog baseline. Use “Run satellite analysis” (GET /building/{id}?live_cv=true) for "
            "Google Static Maps + Gemini roof and tower signals."
        )
    elif physical.vision_backend == "gemini_vision":
        data_notes = (
            f"Live CV: Static Maps + Gemini. Catchment provenance: {physical.roof_catchment_provenance}. "
            "Compare roof_area_sqft (used for catalog) vs roof_area_estimated_cv."
        )
    else:
        data_notes = (
            "live_cv=true but vision fell back to mock (missing keys, Static Maps error, Gemini failure, or bad JSON). "
            "Check GOOGLE_MAPS_API_KEY, GEMINI_API_KEY, ENABLE_LIVE_CV, and building coordinates."
        )

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
        cooling_tower_detected=physical.cooling_tower_detected,
        cooling_tower_confidence=physical.cooling_tower_confidence,
        esg_signal_score=round(esg, 2),
        physical_analysis=physical,
        roof_area_sqft_catalog=record.roof_area_sqft if live_cv else None,
        roof_area_estimated_cv=physical.roof_area_estimated_cv if live_cv else None,
        cv_reasoning=physical.cv_reasoning if live_cv else None,
        data_notes=data_notes,
    )
