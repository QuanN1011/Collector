from datetime import datetime, timezone

from models.building import BuildingEnriched, BuildingRecord
from ai.physical_pipeline import get_physical_analysis
from database.db import (
    StateContext,
    get_company_sustainability_profile,
    get_state_context,
    state_context_source_label,
)
from services.rainwater import annual_rainwater_gallons
from services.roi import annual_water_savings_usd
from services.scoring import compute_viability
from services.sbti_esg import (
    DEFAULT_SBTI_CONFIDENCE,
    api_esg_status,
    esg_applies_to_viability,
    merge_esg_details,
)


def enrich_building(record: BuildingRecord, state_ctx: StateContext | None = None, *, live_cv: bool = False) -> BuildingEnriched:
    ctx = state_ctx or get_state_context(record.state)
    physical = get_physical_analysis(record, force_live=live_cv)
    catchment = physical.roof_catchment_sqft

    gallons = annual_rainwater_gallons(catchment, ctx.rainfall_inches_annual)
    savings = annual_water_savings_usd(gallons, ctx.water_price_per_1000_gal_usd)

    profile = (
        get_company_sustainability_profile(record.company_id)
        if record.company_id
        else None
    )

    esg_subscore: float | None = None
    esg_score: float | None = None
    esg_source: str | None = None
    esg_confidence: float | None = None
    esg_details: dict[str, object] = {}
    esg_status = api_esg_status(profile)
    esg_reason: str | None = None

    if not record.company_id:
        esg_status = "unavailable"
        esg_reason = "Building has no company_id; cannot join company_sustainability_profiles."
    elif profile is None:
        esg_status = "unavailable"
        esg_reason = "No company_sustainability_profiles row for this company_id (use DB seed or ingest_sbti_csv.py)."
    elif not esg_applies_to_viability(profile):
        esg_status = "unavailable"
        esg_reason = (
            "Company profile exists but esg_source is not SBTi or a documented proxy; "
            "ESG omitted from scoring."
        )
    else:
        assert profile.esg_alignment_score is not None
        esg_subscore = float(profile.esg_alignment_score)
        esg_score = round(float(profile.esg_alignment_score), 2)
        esg_source = profile.esg_source
        esg_confidence = (
            float(profile.esg_confidence)
            if profile.esg_confidence is not None
            else DEFAULT_SBTI_CONFIDENCE
        )
        esg_details = {k: v for k, v in merge_esg_details(profile).items()}

    score, breakdown, missing, completeness, weights_applied = compute_viability(
        rainfall_inches_annual=ctx.rainfall_inches_annual,
        water_price_per_1000_gal_usd=ctx.water_price_per_1000_gal_usd,
        tower_status=physical.tower_status,
        cooling_tower_detected=physical.cooling_tower_detected,
        cooling_tower_confidence=physical.cooling_tower_confidence,
        esg_subscore=esg_subscore,
    )

    computed_at = datetime.now(timezone.utc).isoformat()

    provenance: dict[str, object] = {
        "state_context": {
            "source": state_context_source_label(),
            "state": record.state,
            "rainfall_inches_annual": ctx.rainfall_inches_annual,
            "water_price_per_1000_gal_usd": ctx.water_price_per_1000_gal_usd,
        },
        "rainwater": {
            "formula": "annual_rainwater_gallons(catchment_sqft, rainfall_inches_annual)",
            "catchment_sqft": catchment,
            "catchment_source": physical.roof_catchment_provenance,
        },
        "annual_water_savings_usd": {
            "formula": "annual_water_savings_usd(gallons, water_price_per_1000_gal_usd)",
        },
        "viability": {
            "computed_at_utc": computed_at,
            "completeness": completeness,
            "missing_components": missing,
            "weights_applied": weights_applied,
            "formula": (
                "Weighted sum: rainfall, water_price, optional cooling_tower, optional esg (0.10 when present); "
                "see services/scoring.py"
            ),
        },
        "cooling_tower": {
            "tower_status": physical.tower_status,
            "vision_backend": physical.vision_backend,
            "imagery_source": physical.imagery_source,
            "imagery_provider": physical.imagery_provider,
            "imagery_date_range": physical.imagery_date_range,
            "inference_model": physical.inference_model,
            "inference_timestamp_utc": physical.inference_timestamp_utc,
            "unavailable_reason": physical.tower_unavailable_reason,
            "selected_cooling_tower_source": physical.selected_cooling_tower_source,
        },
        "physical_selection": {
            "selected_roof_source": physical.selected_roof_source,
            "selected_cooling_tower_source": physical.selected_cooling_tower_source,
            "roof_confidence": physical.roof_confidence,
            "cooling_tower_confidence": physical.cooling_tower_confidence,
            "raw_sources_available": physical.raw_sources_available,
        },
        "esg": {
            "company_id": record.company_id,
            "status": esg_status,
            "source": esg_source,
            "confidence": esg_confidence,
            "sbti_ingested_at": profile.sbti_ingested_at.isoformat() if profile and profile.sbti_ingested_at else None,
            "reason": esg_reason,
        },
    }

    return BuildingEnriched(
        id=record.id,
        name=record.name,
        state=record.state,
        city=record.city,
        company_id=record.company_id,
        roof_area_sqft=physical.roof_catchment_sqft,
        latitude=record.latitude,
        longitude=record.longitude,
        rainfall_inches_annual=ctx.rainfall_inches_annual,
        water_price_per_1000_gal_usd=ctx.water_price_per_1000_gal_usd,
        rainwater_potential_gallons=round(gallons, 2),
        annual_water_savings=round(savings, 2),
        viability_score=score,
        viability_breakdown=breakdown,
        viability_completeness=completeness,
        viability_missing_components=missing,
        cooling_tower_detected=physical.cooling_tower_detected,
        cooling_tower_confidence=physical.cooling_tower_confidence,
        esg_score=esg_score,
        esg_source=esg_source,
        esg_confidence=esg_confidence,
        esg_status=esg_status,
        esg_details=esg_details,
        esg_signal_score=esg_score,
        esg_unavailable_reason=esg_reason,
        physical_analysis=physical,
        provenance=provenance,
    )
