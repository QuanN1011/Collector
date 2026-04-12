from fastapi import APIRouter, HTTPException, Query

from database.db import get_state_context, list_buildings
from models.building import BuildingEnriched
from services.enrichment import enrich_building
from services.geo_ranking import sort_by_viability_and_proximity

router = APIRouter(tags=["prospects"])


@router.get("/top-prospects", response_model=list[BuildingEnriched])
def get_top_prospects(
    state: str = Query(..., description="US state code, e.g. TX"),
    limit: int = Query(10, ge=1, le=1000, description="Top N by viability (default 10 for demos)"),
    origin_lat: float | None = Query(
        None,
        description="Optional reference latitude (e.g. from Google Places). Blends with viability when origin_lng set.",
    ),
    origin_lng: float | None = Query(
        None,
        description="Optional reference longitude. Both required to enable location-aware ranking.",
    ),
    location_weight: float = Query(
        0.35,
        ge=0.0,
        le=1.0,
        description="0 = sort by viability only; 1 = sort mostly by proximity to origin (haversine).",
    ),
) -> list[BuildingEnriched]:
    try:
        get_state_context(state)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except KeyError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    enriched = [enrich_building(r, live_cv=False) for r in list_buildings(state)]

    if origin_lat is not None and origin_lng is not None:
        if not (-90 <= origin_lat <= 90) or not (-180 <= origin_lng <= 180):
            raise HTTPException(status_code=400, detail="origin_lat must be [-90,90] and origin_lng [-180,180]")
        enriched = sort_by_viability_and_proximity(
            enriched,
            origin_lat=origin_lat,
            origin_lng=origin_lng,
            location_weight=location_weight,
        )
    else:
        enriched.sort(key=lambda b: b.viability_score, reverse=True)

    return enriched[:limit]
