"""
Load CSV fixtures into Postgres (+ PostGIS) and populate related MVP tables.

Requires DATABASE_URL and a running PostGIS instance (see docker-compose.yml).

Data notes
----------
- **Buildings:** default ``data/buildings_catalog.csv`` merges **Microsoft US Building Footprints** (preferred:
  ``buildings_microsoft_nationwide.csv`` from ``ingest_ms_buildings.py --all-states``, else ``buildings_microsoft.csv``
  or ``buildings_microsoft_tx_sample.csv``) with **synthetic** ``bru-*`` rows only for states **not** covered by
  the Microsoft file (see ``merge_buildings_catalog.py --auto-exclude-synthetic``). Legacy ``data/buildings.csv``
  is synthetic-only input. See ``docs/DATABASE_SEED_DATA.md``.
- **State context:** default ``state_context.csv``; optional **rainfall** via ``ingest_state_precip_open_meteo.py``
  (Open-Meteo API). **Water price** is preserved from the merge file until you replace it from an authoritative source.
- City water/wastewater/stormwater overrides live in ``services/seed_scoring.py``.
- CV seed rows use fixed placeholder tower values for demo table completeness; the prospecting API uses
  ``ai.physical_pipeline`` (GEE + Gemini) and does not read these seed CV rows for scores.

Usage (from backend/)::

  # DATABASE_URL in .env (see .env.example) or exported in the shell
  export DATABASE_URL=postgresql+psycopg://rainuse:rainuse@localhost:5432/rainuse
  python scripts/seed_database.py
  python scripts/seed_database.py --buildings-csv data/buildings_catalog.csv

"""

from __future__ import annotations

import argparse
import csv
import sys
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

# Running `python scripts/seed_database.py` puts `scripts/` on sys.path first, not `backend/`.
_BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

from env_load import load_backend_env

load_backend_env()

from geoalchemy2.elements import WKTElement
from sqlalchemy import delete, select
from sqlalchemy.exc import OperationalError

from database.engine import get_session_factory, init_db
from database.tables import (
    Building,
    BuildingScore,
    Company,
    CompanyDocument,
    CompanySustainabilityProfile,
    CvDetection,
    ImageryAsset,
    PhysicalFeature,
    PolicyDriver,
    StateContextRow,
    UtilityProfile,
    WaterYieldEstimate,
)
from services.roi import annual_water_savings_usd
from services.seed_scoring import (
    DEFAULT_RUNOFF_COEFFICIENT,
    DEFAULT_SYSTEM_EFFICIENCY_PCT,
    bounding_polygon_wkt,
    climate_risk_pillar,
    corporate_esg_pillar,
    detection_confidence_pillar,
    effective_annual_harvest_gallons,
    final_viability_from_pillars,
    footprint_multipolygon_wkt,
    imagery_stub,
    monthly_harvest_json,
    opportunity_tier,
    physical_fit_pillar,
    policies_for_state,
    regulatory_pillar,
    resolve_utility_rates,
    roi_pillar,
    utility_cost_pillar,
    water_yield_pillar,
)

_DATA = _BACKEND_ROOT / "data"

# Fallback centers if lat/lon omitted in CSV (legacy jitter).
_STATE_CENTERS: dict[str, tuple[float, float]] = {
    "TX": (31.97, -99.90),
    "AZ": (34.27, -111.66),
    "PA": (41.00, -77.75),
}


def _jitter(building_id: str) -> tuple[float, float]:
    h = abs(hash(building_id + ":geo")) % 10_000
    dx = (h % 200 - 100) / 500.0
    dy = ((h // 200) % 200 - 100) / 500.0
    return dx, dy


def _parse_bool(raw: str | None) -> bool | None:
    if raw is None or str(raw).strip() == "":
        return None
    s = str(raw).strip().lower()
    if s in ("true", "1", "yes"):
        return True
    if s in ("false", "0", "no"):
        return False
    return None


def _parse_opt_float(raw: str | None) -> float | None:
    if raw is None or str(raw).strip() == "":
        return None
    return float(raw)


from services.esg_profile_sync import company_sustainability_profile_from_csv_row as _sustain_profile_from_row


def _load_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def seed(
    state_context_csv: Path | None = None,
    buildings_csv: Path | None = None,
    companies_csv: Path | None = None,
    company_sustainability_csv: Path | None = None,
    company_documents_csv: Path | None = None,
) -> None:
    init_db()
    SessionLocal = get_session_factory()

    sc_path = state_context_csv or (_DATA / "state_context.csv")
    _catalog = _DATA / "buildings_catalog.csv"
    b_path = buildings_csv or (_catalog if _catalog.is_file() else (_DATA / "buildings.csv"))
    co_path = companies_csv or (_DATA / "companies.csv")
    su_path = company_sustainability_csv or (_DATA / "company_sustainability_profiles.csv")
    do_path = company_documents_csv or (_DATA / "company_documents.csv")

    state_rows = _load_csv(sc_path)
    building_rows = _load_csv(b_path)
    company_rows = _load_csv(co_path)
    sust_rows = _load_csv(su_path)
    doc_rows = _load_csv(do_path)

    company_sustain: dict[str, CompanySustainabilityProfile] = {}
    for row in sust_rows:
        p = _sustain_profile_from_row(row)
        company_sustain[p.company_id] = p

    ctx_map: dict[str, StateContextRow] = {}
    for row in state_rows:
        st = row["state"].strip().upper()
        ctx_map[st] = StateContextRow(
            state_code=st,
            rainfall_inches_annual=float(row["rainfall_inches_annual"]),
            water_price_per_1000_gal_usd=float(row["water_price_per_1000_gal_usd"]),
        )

    with SessionLocal() as session:
        session.execute(delete(CvDetection))
        session.execute(delete(ImageryAsset))
        session.execute(delete(PolicyDriver))
        session.execute(delete(PhysicalFeature))
        session.execute(delete(WaterYieldEstimate))
        session.execute(delete(UtilityProfile))
        session.execute(delete(BuildingScore))
        session.execute(delete(Building))
        session.execute(delete(CompanyDocument))
        session.execute(delete(CompanySustainabilityProfile))
        session.execute(delete(Company))
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

        for row in company_rows:
            session.add(
                Company(
                    id=row["id"].strip(),
                    company_name=row["company_name"].strip(),
                    ticker=(row.get("ticker") or "").strip() or None,
                    cik=(row.get("cik") or "").strip() or None,
                    industry=(row.get("industry") or "").strip() or None,
                    website=(row.get("website") or "").strip() or None,
                    hq_state=(row.get("hq_state") or "").strip() or None,
                )
            )

        for row in sust_rows:
            session.add(_sustain_profile_from_row(row))

        for row in doc_rows:
            fd = row.get("filing_date") or ""
            filing_date = None
            if fd.strip():
                parts = fd.strip().split("-")
                if len(parts) == 3:
                    filing_date = date(int(parts[0]), int(parts[1]), int(parts[2]))
            session.add(
                CompanyDocument(
                    id=row["id"].strip(),
                    company_id=row["company_id"].strip(),
                    document_type=(row.get("document_type") or "").strip() or None,
                    filing_date=filing_date,
                    source_url=(row.get("source_url") or "").strip() or None,
                    storage_uri=None,
                    content_hash=None,
                    byte_length=None,
                    excerpt=(row.get("excerpt") or "").strip() or None,
                    parsed_json=None,
                )
            )

        for row in building_rows:
            bid = row["id"].strip()
            st = row["state"].strip().upper()
            ctx = ctx_map[st]
            lat_raw = (row.get("latitude") or "").strip()
            lon_raw = (row.get("longitude") or "").strip()
            if lat_raw and lon_raw:
                lat = float(lat_raw)
                lon = float(lon_raw)
            else:
                center = _STATE_CENTERS.get(st, (39.83, -98.58))
                dx, dy = _jitter(bid)
                lat = center[0] + dy
                lon = center[1] + dx

            roof = float(row["roof_area_sqft"])
            cid = (row.get("company_id") or "").strip() or None
            fp_wkt_raw = (row.get("footprint_wkt") or "").strip()
            if fp_wkt_raw:
                fp_wkt = fp_wkt_raw
            else:
                fp_wkt = footprint_multipolygon_wkt(lat, lon, roof)
            ds_raw = (row.get("data_source") or "").strip() or None
            if ds_raw is None:
                data_source = (
                    "microsoft_us_building_footprints"
                    if fp_wkt_raw
                    else "synthetic_commercial_seed"
                )
            else:
                data_source = ds_raw
            session.add(
                Building(
                    id=bid,
                    name=row["name"].strip(),
                    state_code=st,
                    city=(row.get("city") or "").strip() or None,
                    county=(row.get("county") or "").strip() or None,
                    geocode_display_name=(row.get("geocode_display_name") or "").strip() or None,
                    roof_area_sqft=roof,
                    company_id=cid,
                    building_type=(row.get("building_type") or "").strip() or None,
                    land_use_type=(row.get("land_use_type") or "").strip() or None,
                    latitude=lat,
                    longitude=lon,
                    data_source=data_source,
                    footprint_geom=WKTElement(fp_wkt, srid=4326),
                )
            )
        session.commit()

    now = datetime.now(UTC)

    with SessionLocal() as session:
        buildings = session.scalars(select(Building)).all()
        ctx_by_state = {r.state_code: r for r in session.scalars(select(StateContextRow)).all()}

        for b in buildings:
            ctx = ctx_by_state[b.state_code]
            rainfall = ctx.rainfall_inches_annual
            # Placeholder for seed/demo CvDetection rows only (not used by GET /building enrichment).
            tower_ok, tower_conf = False, 0.0

            w_kgal, ww_kgal, storm_mo = resolve_utility_rates(
                b.state_code,
                b.city,
                ctx.water_price_per_1000_gal_usd,
            )

            harvest = effective_annual_harvest_gallons(
                b.roof_area_sqft,
                rainfall,
                DEFAULT_RUNOFF_COEFFICIENT,
                DEFAULT_SYSTEM_EFFICIENCY_PCT,
            )
            savings = annual_water_savings_usd(harvest, w_kgal)

            sust = company_sustain.get(b.company_id) if b.company_id else None
            esg_align = sust.esg_alignment_score if sust else None
            has_sbt = sust.has_science_based_target if sust else None
            has_water = sust.has_water_target if sust else None

            phys = physical_fit_pillar(b.roof_area_sqft, tower_ok, tower_conf)
            wy = water_yield_pillar(harvest)
            util = utility_cost_pillar(w_kgal, ww_kgal, storm_mo)
            clim = climate_risk_pillar(b.state_code)
            corp = corporate_esg_pillar(esg_align, has_sbt, has_water)

            obstruction_ratio = round(0.06 + (abs(hash(b.id + ":obs")) % 17) / 100.0, 3)
            eff_catch = round(b.roof_area_sqft * (1.0 - obstruction_ratio), 2)

            capture_d = date(2023, 1, 1) + timedelta(days=abs(hash(b.id + ":cap")) % 700)
            prov, img_url, res_m, cloud_pct, _ = imagery_stub(b.id, capture_d)
            img_id = f"img-{b.id}-s2"
            session.add(
                ImageryAsset(
                    image_id=img_id,
                    building_id=b.id,
                    provider=prov,
                    capture_date=capture_d,
                    resolution_meters=res_m,
                    cloud_cover_pct=cloud_pct,
                    image_url=img_url,
                    bounding_geom=WKTElement(bounding_polygon_wkt(b.latitude or 0.0, b.longitude or 0.0), srid=4326),
                    qa_score=round(0.82 + (abs(hash(b.id)) % 17) / 100.0, 2),
                )
            )

            confidences: list[float] = []
            roof_conf = round(0.78 + (abs(hash(b.id + ":roof")) % 18) / 100.0, 2)
            obs_conf = round(0.52 + (abs(hash(b.id + ":obsd")) % 33) / 100.0, 2)
            confidences.extend([roof_conf, tower_conf, obs_conf])

            session.add(
                CvDetection(
                    detection_id=f"det-{b.id}-roof",
                    building_id=b.id,
                    image_id=img_id,
                    detection_type="roof_boundary",
                    confidence_score=roof_conf,
                    bbox_geom=None,
                    mask_geom=None,
                )
            )
            session.add(
                CvDetection(
                    detection_id=f"det-{b.id}-tower",
                    building_id=b.id,
                    image_id=img_id,
                    detection_type="cooling_tower",
                    confidence_score=tower_conf,
                    bbox_geom=None,
                    mask_geom=None,
                )
            )
            session.add(
                CvDetection(
                    detection_id=f"det-{b.id}-obs",
                    building_id=b.id,
                    image_id=img_id,
                    detection_type="obstruction",
                    confidence_score=obs_conf,
                    bbox_geom=None,
                    mask_geom=None,
                )
            )

            det_score = detection_confidence_pillar(confidences)

            session.add(
                PhysicalFeature(
                    building_id=b.id,
                    roof_catchment_sqft=b.roof_area_sqft,
                    effective_catchment_sqft=eff_catch,
                    cooling_tower_present=tower_ok,
                    cooling_tower_count_est=2.0 if tower_ok else 0.0,
                    roof_obstruction_ratio=obstruction_ratio,
                    physical_fit_score=phys,
                )
            )

            session.add(
                WaterYieldEstimate(
                    building_id=b.id,
                    avg_annual_rainfall_in=rainfall,
                    runoff_coefficient=DEFAULT_RUNOFF_COEFFICIENT,
                    system_efficiency_pct=DEFAULT_SYSTEM_EFFICIENCY_PCT,
                    annual_harvest_gallons=round(harvest, 2),
                    monthly_harvest_json=monthly_harvest_json(harvest),
                    water_yield_score=wy,
                )
            )

            session.add(
                UtilityProfile(
                    building_id=b.id,
                    water_cost_per_kgal=w_kgal,
                    wastewater_cost_per_kgal=ww_kgal,
                    stormwater_fee_monthly=storm_mo,
                    utility_cost_pressure_score=util,
                )
            )

            tpls = policies_for_state(b.state_code)
            strengths: list[float] = []
            for i, (jur, ptype, pname, est_val, strength) in enumerate(tpls):
                strengths.append(strength)
                session.add(
                    PolicyDriver(
                        id=f"pol-{b.id}-{i}",
                        building_id=b.id,
                        jurisdiction_name=jur,
                        policy_type=ptype,
                        policy_name=pname,
                        estimated_value_usd=est_val,
                        driver_strength_score=strength,
                    )
                )
            reg = regulatory_pillar(strengths)

            roi = roi_pillar(savings)

            pillars = {
                "physical_fit_score": phys,
                "water_yield_score": wy,
                "utility_cost_score": util,
                "regulatory_score": reg,
                "corporate_esg_score": corp,
                "climate_risk_score": clim,
                "detection_confidence_score": det_score,
                "roi_score": roi,
            }
            final = final_viability_from_pillars(pillars)

            session.add(
                BuildingScore(
                    building_id=b.id,
                    physical_fit_score=phys,
                    water_yield_score=wy,
                    utility_cost_score=util,
                    regulatory_score=reg,
                    corporate_esg_score=corp,
                    climate_risk_score=clim,
                    detection_confidence_score=det_score,
                    roi_score=roi,
                    final_viability_score=final,
                    opportunity_tier=opportunity_tier(final),
                    computed_at=now,
                )
            )

        session.commit()

    print(
        "Seed complete: state_context, companies (+ profiles, documents), buildings (PostGIS footprints), "
        "imagery_assets, cv_detections, physical_features, water_yield_estimates, utility_profiles, "
        "policy_drivers, building_scores.\n"
        "ESG: after changing company_sustainability_profiles.csv or fixing legacy DB rows, run "
        "python scripts/refresh_esg_profiles.py && python scripts/verify_esg_profiles.py"
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Seed RainUSE Postgres from CSV fixtures + derived rows.")
    p.add_argument("--state-context-csv", type=Path, default=None, help="Default: data/state_context.csv")
    p.add_argument(
        "--buildings-csv",
        type=Path,
        default=None,
        help="Default: data/buildings_catalog.csv if present, else data/buildings.csv",
    )
    p.add_argument("--companies-csv", type=Path, default=None)
    p.add_argument("--company-sustainability-csv", type=Path, default=None)
    p.add_argument("--company-documents-csv", type=Path, default=None)
    args = p.parse_args()
    try:
        seed(
            state_context_csv=args.state_context_csv,
            buildings_csv=args.buildings_csv,
            companies_csv=args.companies_csv,
            company_sustainability_csv=args.company_sustainability_csv,
            company_documents_csv=args.company_documents_csv,
        )
    except OperationalError as exc:
        print(
            "\nCould not connect to PostgreSQL (check DATABASE_URL in backend/.env). "
            "Connection refused usually means no server on that host:port.\n"
            "  • Repo root: docker compose up -d   (needs Docker installed; see docker-compose.yml)\n"
            "  • Or install/run PostGIS locally and match DATABASE_URL.\n",
            file=sys.stderr,
        )
        raise SystemExit(1) from exc
