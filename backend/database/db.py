"""
Persistence layer: Postgres (+ PostGIS) when DATABASE_URL is set; otherwise CSV fallback.

CSV keeps local demos working without Docker; production / team Postgres uses the same API.
"""

from __future__ import annotations

import csv
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from database.config import use_database
from database.engine import get_session_factory
from database.tables import Building as BuildingRow
from database.tables import BuildingScore as BuildingScoreRow
from database.tables import CompanySustainabilityProfile as CompanySustainabilityProfileRow
from database.tables import StateContextRow
from models.building import BuildingRecord

_DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def _buildings_csv_path() -> Path:
    """Prefer merged Microsoft + synthetic catalog when present (see merge_buildings_catalog.py)."""
    catalog = _DATA_DIR / "buildings_catalog.csv"
    if catalog.is_file():
        return catalog
    return _DATA_DIR / "buildings.csv"


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
        county=row.county,
        geocode_display_name=row.geocode_display_name,
        roof_area_sqft=row.roof_area_sqft,
        latitude=row.latitude,
        longitude=row.longitude,
        data_source=row.data_source,
        has_footprint_polygon=row.footprint_geom is not None,
        company_id=row.company_id,
        roof_area_sqft_cv=row.roof_area_sqft_cv,
        roof_area_confidence_cv=row.roof_area_confidence_cv,
        cooling_tower_detected_cv=row.cooling_tower_detected_cv,
        cooling_tower_confidence_cv=row.cooling_tower_confidence_cv,
        cv_inference_at=row.cv_inference_at,
        cv_source=row.cv_source,
        cv_inference_model=row.cv_inference_model,
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
    path = _buildings_csv_path()
    records: list[BuildingRecord] = []
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            ds = (row.get("data_source") or "").strip() or None
            fp_wkt = (row.get("footprint_wkt") or "").strip()
            cid = (row.get("company_id") or "").strip() or None
            records.append(
                BuildingRecord(
                    id=row["id"].strip(),
                    name=row["name"].strip(),
                    state=row["state"].strip().upper(),
                    city=(row.get("city") or "").strip() or None,
                    county=(row.get("county") or "").strip() or None,
                    geocode_display_name=(row.get("geocode_display_name") or "").strip() or None,
                    roof_area_sqft=float(row["roof_area_sqft"]),
                    latitude=_parse_optional_float(row.get("latitude")),
                    longitude=_parse_optional_float(row.get("longitude")),
                    data_source=ds,
                    has_footprint_polygon=bool(fp_wkt),
                    company_id=cid,
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


def state_context_source_label() -> str:
    """Human-readable source for provenance (Postgres table vs bundled CSV)."""
    if use_database():
        return "postgres:state_context"
    return "csv:backend/data/state_context.csv"


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


def list_states_from_state_context() -> list[str]:
    """
    Sorted USPS codes present in ``state_context`` (rainfall + water price).

    This is the source of truth for ``GET /states`` so the UI can show nationwide
    coverage; states without buildings still appear and return empty ``GET /buildings``.
    """
    if use_database():
        SessionLocal = get_session_factory()
        with SessionLocal() as session:
            q = select(StateContextRow.state_code).order_by(StateContextRow.state_code)
            return list(session.scalars(q).all())
    return sorted(_load_state_context_csv().keys())


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
    """
    Persisted score from ``building_scores`` (seed or offline pipeline).

    Not used by ``enrich_building`` / GET ``/buildings`` — headline viability is always computed
    from current state context + physical analysis (see ``services/enrichment.py``).
    """
    row = session.get(BuildingScoreRow, building_id)
    if row is None or row.final_viability_score is None:
        return None
    return float(row.final_viability_score)


def get_company_sustainability_profile(company_id: str) -> CompanySustainabilityProfileRow | None:
    """Load persisted company ESG row (SBTi ingest). CSV-only mode returns None."""
    cid = company_id.strip()
    if not cid or not use_database():
        return None
    SessionLocal = get_session_factory()
    with SessionLocal() as session:
        return session.get(CompanySustainabilityProfileRow, cid)


def get_stored_final_viability_standalone(building_id: str) -> float | None:
    """Same as ``get_stored_final_viability`` without an injected session (offline tools only)."""
    if not use_database():
        return None
    SessionLocal = get_session_factory()
    with SessionLocal() as session:
        return get_stored_final_viability(session, building_id)


def persist_building_cv_snapshot(
    building_id: str,
    *,
    cooling_tower_detected: bool,
    cooling_tower_confidence: float,
    inference_model: str | None,
    cv_source: str = "gee_sentinel2_gemini",
) -> None:
    """
    Persist live CV cooling-tower outcome without touching catalog ``roof_area_sqft`` / ``data_source``.
    """
    if not use_database():
        return
    bid = building_id.strip()
    SessionLocal = get_session_factory()
    with SessionLocal() as session:
        row = session.get(BuildingRow, bid)
        if row is None:
            return
        row.cooling_tower_detected_cv = cooling_tower_detected
        row.cooling_tower_confidence_cv = float(cooling_tower_confidence)
        row.cv_inference_model = inference_model
        row.cv_source = cv_source
        row.cv_inference_at = datetime.now(timezone.utc)
        session.commit()
