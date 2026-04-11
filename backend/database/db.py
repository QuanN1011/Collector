"""
Persistence layer: Postgres (+ PostGIS) when DATABASE_URL is set; otherwise CSV fallback.

CSV keeps local demos working without Docker; production / team Postgres uses the same API.
"""

from __future__ import annotations

import csv
from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from database.config import use_database
from database.engine import get_session_factory
from database.tables import Building as BuildingRow
from database.tables import BuildingScore as BuildingScoreRow
from database.tables import StateContextRow
from models.building import BuildingRecord

_DATA_DIR = Path(__file__).resolve().parent.parent / "data"


class StateContext(BaseModel):
    state: str = Field(..., min_length=2, max_length=2)
    rainfall_inches_annual: float = Field(..., gt=0)
    water_price_per_1000_gal_usd: float = Field(..., gt=0)


def _row_to_state_context(row: StateContextRow) -> StateContext:
    return StateContext(
        state=row.state_code,
        rainfall_inches_annual=row.rainfall_inches_annual,
        water_price_per_1000_gal_usd=row.water_price_per_1000_gal_usd,
    )


def _row_to_building_record(row: BuildingRow) -> BuildingRecord:
    return BuildingRecord(
        id=row.id,
        name=row.name,
        state=row.state_code,
        city=row.city,
        roof_area_sqft=row.roof_area_sqft,
        latitude=row.latitude,
        longitude=row.longitude,
    )


@lru_cache
def _load_state_context_csv() -> dict[str, StateContext]:
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
def _load_buildings_csv() -> tuple[BuildingRecord, ...]:
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
                    latitude=_parse_optional_float(row.get("latitude")),
                    longitude=_parse_optional_float(row.get("longitude")),
                )
            )
    return tuple(records)


def _parse_optional_float(raw: str | None) -> float | None:
    if raw is None or str(raw).strip() == "":
        return None
    return float(raw)


def get_state_context(state: str) -> StateContext:
    st = state.strip().upper()
    if use_database():
        SessionLocal = get_session_factory()
        with SessionLocal() as session:
            row = session.get(StateContextRow, st)
            if row is None:
                raise KeyError(f"No state context for {st!r}; seed state_context or add a row")
            return _row_to_state_context(row)
    ctx = _load_state_context_csv().get(st)
    if ctx is None:
        raise KeyError(f"No state context for {st!r}; add a row to data/state_context.csv")
    return ctx


def list_buildings(state: str | None = None) -> list[BuildingRecord]:
    if use_database():
        SessionLocal = get_session_factory()
        with SessionLocal() as session:
            q = select(BuildingRow).order_by(BuildingRow.id)
            if state is not None:
                st = state.strip().upper()
                q = q.where(BuildingRow.state_code == st)
            rows = session.scalars(q).all()
            return [_row_to_building_record(r) for r in rows]

    buildings = list(_load_buildings_csv())
    if state is None:
        return buildings
    st = state.strip().upper()
    return [b for b in buildings if b.state == st]


def get_building(building_id: str) -> BuildingRecord | None:
    bid = building_id.strip()
    if use_database():
        SessionLocal = get_session_factory()
        with SessionLocal() as session:
            row = session.get(BuildingRow, bid)
            return _row_to_building_record(row) if row else None
    for b in _load_buildings_csv():
        if b.id == bid:
            return b
    return None


def get_stored_final_viability(session: Session, building_id: str) -> float | None:
    """Optional persisted score from building_scores (filled by pipeline or seed)."""
    row = session.get(BuildingScoreRow, building_id)
    if row is None or row.final_viability_score is None:
        return None
    return float(row.final_viability_score)


def get_stored_final_viability_standalone(building_id: str) -> float | None:
    """Same as get_stored_final_viability without an injected session (OK for MVP list sizes)."""
    if not use_database():
        return None
    SessionLocal = get_session_factory()
    with SessionLocal() as session:
        return get_stored_final_viability(session, building_id)
