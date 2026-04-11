"""
Load CSV fixtures into Postgres and persist computed viability + climate placeholders.

Requires DATABASE_URL and a running PostGIS instance (see repo docker-compose.yml).

Usage (from backend/):
  export DATABASE_URL=postgresql+psycopg://rainuse:rainuse@localhost:5432/rainuse
  python scripts/seed_database.py
"""

from __future__ import annotations

import csv
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import delete, select

from ai.cooling_tower_detection import detect_cooling_tower
from database.engine import get_session_factory, init_db
from database.tables import Building, BuildingScore, StateContextRow
from services.scoring import compute_viability

_DATA = Path(__file__).resolve().parent.parent / "data"

# Approximate state centers (WGS84) for demo pins; jitter per building in main().
_STATE_CENTERS: dict[str, tuple[float, float]] = {
    "TX": (31.97, -99.90),
    "AZ": (34.27, -111.66),
    "PA": (41.00, -77.75),
    "CA": (36.78, -119.42),
    "FL": (27.66, -81.52),
    "GA": (32.99, -83.64),
    "IL": (40.06, -89.40),
    "OH": (40.39, -82.79),
    "NY": (43.30, -75.50),
    "WA": (47.40, -121.08),
    "CO": (39.11, -105.31),
    "NC": (35.63, -79.81),
}


def _jitter(building_id: str) -> tuple[float, float]:
    h = abs(hash(building_id + ":geo")) % 10_000
    dx = (h % 200 - 100) / 500.0
    dy = ((h // 200) % 200 - 100) / 500.0
    return dx, dy


def seed() -> None:
    init_db()
    SessionLocal = get_session_factory()

    state_rows: list[dict[str, str]] = []
    with (_DATA / "state_context.csv").open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            state_rows.append(row)

    building_rows: list[dict[str, str]] = []
    with (_DATA / "buildings.csv").open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            building_rows.append(row)

    with SessionLocal() as session:
        session.execute(delete(BuildingScore))
        session.execute(delete(Building))
        session.execute(delete(StateContextRow))
        session.commit()

    with SessionLocal() as session:
        for row in state_rows:
            st = row["state"].strip().upper()
            session.add(
                StateContextRow(
                    state_code=st,
                    rainfall_inches_annual=float(row["rainfall_inches_annual"]),
                    water_price_per_1000_gal_usd=float(row["water_price_per_1000_gal_usd"]),
                )
            )

        for row in building_rows:
            bid = row["id"].strip()
            st = row["state"].strip().upper()
            center = _STATE_CENTERS.get(st, (39.83, -98.58))
            dx, dy = _jitter(bid)
            lat = center[0] + dy
            lon = center[1] + dx
            session.add(
                Building(
                    id=bid,
                    name=row["name"].strip(),
                    state_code=st,
                    city=(row.get("city") or "").strip() or None,
                    roof_area_sqft=float(row["roof_area_sqft"]),
                    latitude=lat,
                    longitude=lon,
                    footprint_geom=None,
                )
            )
        session.commit()

    with SessionLocal() as session:
        buildings = session.scalars(select(Building)).all()
        ctx_map = {r.state_code: r for r in session.scalars(select(StateContextRow)).all()}
        now = datetime.now(UTC)
        for b in buildings:
            ctx = ctx_map[b.state_code]
            tower_ok, tower_conf = detect_cooling_tower(b.id)
            final, _breakdown = compute_viability(
                roof_area_sqft=b.roof_area_sqft,
                rainfall_inches_annual=ctx.rainfall_inches_annual,
                water_price_per_1000_gal_usd=ctx.water_price_per_1000_gal_usd,
                cooling_tower_detected=tower_ok,
                cooling_tower_confidence=tower_conf,
                building_id=b.id,
            )
            climate = float(abs(hash(b.id + ":climate")) % 100)
            session.add(
                BuildingScore(
                    building_id=b.id,
                    final_viability_score=final,
                    climate_risk_score=climate,
                    corporate_esg_score=None,
                    detection_confidence_score=None,
                    computed_at=now,
                )
            )
        session.commit()

    print("Seed complete: state_context, buildings (lat/lon), building_scores (computed final + climate placeholder).")


if __name__ == "__main__":
    seed()
