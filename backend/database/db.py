from __future__ import annotations

import csv
from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel, Field

from models.building import BuildingRecord

_DATA_DIR = Path(__file__).resolve().parent.parent / "data"


class StateContext(BaseModel):
    state: str = Field(..., min_length=2, max_length=2)
    rainfall_inches_annual: float = Field(..., gt=0)
    water_price_per_1000_gal_usd: float = Field(..., gt=0)


@lru_cache
def _load_state_context() -> dict[str, StateContext]:
    path = _DATA_DIR / "state_context.csv"
    out: dict[str, StateContext] = {}
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            st = row["state"].strip().upper()
            out[st] = StateContext(
                state=st,
                rainfall_inches_annual=float(row["rainfall_inches_annual"]),
                water_price_per_1000_gal_usd=float(row["water_price_per_1000_gal_usd"]),
            )
    return out


@lru_cache
def _load_buildings() -> tuple[BuildingRecord, ...]:
    path = _DATA_DIR / "buildings.csv"
    records: list[BuildingRecord] = []
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            records.append(
                BuildingRecord(
                    id=row["id"].strip(),
                    name=row["name"].strip(),
                    state=row["state"].strip().upper(),
                    city=(row.get("city") or "").strip() or None,
                    roof_area_sqft=float(row["roof_area_sqft"]),
                )
            )
    return tuple(records)


def get_state_context(state: str) -> StateContext:
    st = state.strip().upper()
    ctx = _load_state_context().get(st)
    if ctx is None:
        raise KeyError(f"No state context for {st!r}; add a row to data/state_context.csv")
    return ctx


def list_buildings(state: str | None = None) -> list[BuildingRecord]:
    buildings = list(_load_buildings())
    if state is None:
        return buildings
    st = state.strip().upper()
    return [b for b in buildings if b.state == st]


def get_building(building_id: str) -> BuildingRecord | None:
    bid = building_id.strip()
    for b in _load_buildings():
        if b.id == bid:
            return b
    return None
