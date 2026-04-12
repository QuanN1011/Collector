"""Catalog building routes. Address → Maps → Gemini pipeline: ``routes/analyze_building`` (``GET /analyze-building``)."""

from fastapi import APIRouter, HTTPException, Query

from database.db import get_state_context, get_building, list_buildings
from models.building import BuildingEnriched
from services.enrichment import enrich_building

router = APIRouter(prefix="/buildings", tags=["buildings"])


@router.get("", response_model=list[BuildingEnriched])
def get_buildings(state: str | None = Query(None, description="US state code, e.g. TX")) -> list[BuildingEnriched]:
    if state is not None:
        try:
            get_state_context(state)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e)) from e
        except KeyError as e:
            raise HTTPException(status_code=400, detail=str(e)) from e
    records = list_buildings(state)
    return [enrich_building(r, live_cv=False) for r in records]


# Mounted at /building (singular) in main.py to match spec GET /building/{id}
single_router = APIRouter(prefix="/building", tags=["buildings"])


@single_router.get("/{building_id}", response_model=BuildingEnriched)
def get_one_building(
    building_id: str,
    live_cv: bool = Query(
        False,
        description="If true, fetch Static Maps satellite + Gemini roof/tower analysis (requires ENABLE_LIVE_CV, "
        "GOOGLE_MAPS_API_KEY, GEMINI_API_KEY). Cached in building_cv_analysis.",
    ),
) -> BuildingEnriched:
    record = get_building(building_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Building not found")
    return enrich_building(record, live_cv=live_cv)
