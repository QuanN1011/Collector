"""Prospecting metadata: which states have building rows in the current dataset."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

from database.db import list_states_with_buildings

router = APIRouter(tags=["prospecting"])


class StatesResponse(BaseModel):
    states: list[str] = Field(
        ...,
        description="USPS state codes with at least one building (sorted).",
    )


@router.get("/states", response_model=StatesResponse)
def get_states_with_buildings() -> StatesResponse:
    """Use this to populate state pickers; only listed codes return non-empty ``GET /buildings``."""
    return StatesResponse(states=list_states_with_buildings())
