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
        data_source=row.data_source,
        has_footprint_polygon=row.footprint_geom is not None,
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
            ds = (row.get("data_source") or "").strip() or None
            fp_wkt = (row.get("footprint_wkt") or "").strip()
            records.append(
                BuildingRecord(
                    id=row["id"].strip(),
                    name=row["name"].strip(),
                    state=row["state"].strip().upper(),
                    city=(row.get("city") or "").strip() or None,
                    roof_area_sqft=float(row["roof_area_sqft"]),
                    latitude=_parse_optional_float(row.get("latitude")),
                    longitude=_parse_optional_float(row.get("longitude")),
                    data_source=ds,
                    has_footprint_polygon=bool(fp_wkt),
                )
            )
    return tuple(records)


def _parse_optional_float(raw: str | None) -> float | None:
    if raw is None or str(raw).strip() == "":
        return None
    return float(raw)


def parse_state_code(state: str) -> str:
    """
    Normalize and validate a USPS-style state code for prospecting APIs.

    Raises ``ValueError`` if not exactly two ASCII letters (e.g. ``TEX`` or ``9X``).
    """
    st = state.strip().upper()
    if len(st) != 2 or not st.isalpha():
        raise ValueError(
            f"Invalid state code {state!r}: expected exactly 2 letters (e.g. TX, AZ)."
        )
    return st


def get_state_context(state: str) -> StateContext:
    st = parse_state_code(state)
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
    st_filter: str | None = None
    if state is not None:
        st_filter = parse_state_code(state)

    if use_database():
        SessionLocal = get_session_factory()
        with SessionLocal() as session:
            q = select(BuildingRow).order_by(BuildingRow.id)
            if st_filter is not None:
                q = q.where(BuildingRow.state_code == st_filter)
            rows = session.scalars(q).all()
            return [_row_to_building_record(r) for r in rows]

    buildings = list(_load_buildings_csv())
    if st_filter is None:
        return buildings
    return [b for b in buildings if b.state == st_filter]


def list_states_with_buildings() -> list[str]:
    """Sorted USPS codes that have at least one building (Postgres or CSV)."""
    if use_database():
        SessionLocal = get_session_factory()
        with SessionLocal() as session:
            q = (
                select(BuildingRow.state_code)
                .distinct()
                .order_by(BuildingRow.state_code)
            )
            rows = session.execute(q).all()
            return [r[0] for r in rows]

    return sorted({b.state for b in _load_buildings_csv()})


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
