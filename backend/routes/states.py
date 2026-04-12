"""Prospecting metadata: states with state_context (nationwide picker)."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

from database.db import list_states_from_state_context

router = APIRouter(tags=["prospecting"])


class StatesResponse(BaseModel):
    states: list[str] = Field(
        ...,
        description="USPS state codes that have state_context rows (sorted); includes states with no buildings.",
    )


@router.get("/states", response_model=StatesResponse)
def get_states() -> StatesResponse:
    """Populate state pickers from ``state_context`` (backend source of truth). Empty ``GET /buildings`` is valid."""
    return StatesResponse(states=list_states_from_state_context())
