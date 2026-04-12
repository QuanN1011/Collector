from fastapi import APIRouter, HTTPException, Query

from database.db import get_state_context, list_buildings
from models.building import BuildingEnriched
from services.enrichment import enrich_building

router = APIRouter(tags=["prospects"])


@router.get("/top-prospects", response_model=list[BuildingEnriched])
def get_top_prospects(
    state: str = Query(..., description="US state code, e.g. TX"),
    limit: int = Query(10, ge=1, le=1000, description="Top N by viability (default 10 for demos)"),
) -> list[BuildingEnriched]:
    try:
        get_state_context(state)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except KeyError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    enriched = [enrich_building(r, live_cv=False) for r in list_buildings(state)]
    enriched.sort(key=lambda b: b.viability_score, reverse=True)
    return enriched[:limit]
