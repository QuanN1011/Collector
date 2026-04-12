"""
Upsert ``company_sustainability_profiles`` from offline SBTi-style CSV (no live API).

Expected columns (see ``data/sbti/sbti_targets.csv``):
  company_id, organization_name, near_term_status, net_zero_status, snapshot_date

``esg_alignment_score`` is computed deterministically via ``services/sbti_esg.compute_sbti_alignment_subscore``.
By default, ``--merge-from`` points at ``data/company_sustainability_profiles.csv`` (booleans/climate).
Use ``--no-merge-from`` to ingest SBTi columns only.

Usage (from ``backend/``)::

  export DATABASE_URL=postgresql+psycopg://...
  python scripts/ingest_sbti_csv.py --input data/sbti/sbti_targets.csv
"""

from __future__ import annotations

import argparse
import csv
import sys
from datetime import UTC, datetime
from pathlib import Path

_BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

from env_load import load_backend_env

load_backend_env()

from database.engine import get_session_factory, init_db
from database.tables import CompanySustainabilityProfile
from services.sbti_esg import DEFAULT_SBTI_CONFIDENCE, compute_sbti_alignment_subscore


def _parse_snapshot(raw: str | None) -> datetime | None:
    if not raw or not str(raw).strip():
        return None
    s = str(raw).strip()
    if "T" in s:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    y, m, d = s.split("-")[:3]
    return datetime(int(y), int(m), int(d), tzinfo=UTC)


def upsert_row(
    session,
    row: dict[str, str],
    *,
    merge: dict[str, dict[str, str]] | None,
) -> None:
    cid = row["company_id"].strip()
    nt = (row.get("near_term_status") or "").strip()
    nz = (row.get("net_zero_status") or "").strip()
    org = (row.get("organization_name") or "").strip()
    align = compute_sbti_alignment_subscore(nt, nz)
    snap = _parse_snapshot((row.get("snapshot_date") or "").strip() or None)
    details: dict = {
        "near_term_status": nt or None,
        "net_zero_status": nz or None,
        "organization_name": org or None,
        "dataset": "SBTi_offline_csv",
    }
    base = merge.get(cid) if merge else None
    has_esg = True
    has_water = True
    has_sbt = True
    climate = None
    if base:

        def _b(k: str) -> str | None:
            return base.get(k)

        def _tok_bool(raw: str | None) -> bool:
            return (raw or "").strip().lower() in ("true", "1", "yes")

        has_esg = _tok_bool(_b("has_esg_report"))
        has_water = _tok_bool(_b("has_water_target"))
        has_sbt = _tok_bool(_b("has_science_based_target"))
        crs = _b("climate_risk_score")
        if crs and str(crs).strip():
            climate = float(crs)

    existing = session.get(CompanySustainabilityProfile, cid)
    if existing:
        existing.has_esg_report = has_esg
        existing.has_water_target = has_water
        existing.has_science_based_target = has_sbt
        existing.climate_risk_score = climate
        existing.esg_alignment_score = align
        existing.esg_source = "SBTi"
        existing.esg_confidence = DEFAULT_SBTI_CONFIDENCE
        existing.sbti_ingested_at = snap or datetime.now(tz=UTC)
        existing.esg_details = details
    else:
        session.add(
            CompanySustainabilityProfile(
                company_id=cid,
                has_esg_report=has_esg,
                has_water_target=has_water,
                has_science_based_target=has_sbt,
                climate_risk_score=climate,
                esg_alignment_score=align,
                esg_source="SBTi",
                esg_confidence=DEFAULT_SBTI_CONFIDENCE,
                sbti_ingested_at=snap or datetime.now(tz=UTC),
                esg_details=details,
            )
        )


def main() -> None:
    _canonical_profiles = _BACKEND_ROOT / "data" / "company_sustainability_profiles.csv"
    parser = argparse.ArgumentParser(description="Ingest offline SBTi CSV into company_sustainability_profiles.")
    parser.add_argument("--input", type=Path, default=_BACKEND_ROOT / "data" / "sbti" / "sbti_targets.csv")
    parser.add_argument(
        "--merge-from",
        type=Path,
        default=_canonical_profiles,
        help="Full company_sustainability_profiles CSV for boolean/climate (default: checked-in canonical file).",
    )
    parser.add_argument(
        "--no-merge-from",
        action="store_true",
        help="Ignore --merge-from / default and ingest SBTi columns only.",
    )
    args = parser.parse_args()

    init_db()
    merge_map: dict[str, dict[str, str]] = {}
    merge_path = None if args.no_merge_from else args.merge_from
    if merge_path and merge_path.is_file():
        with merge_path.open(newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                merge_map[r["company_id"].strip()] = dict(r)

    SessionLocal = get_session_factory()
    with SessionLocal() as session:
        with args.input.open(newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                upsert_row(session, row, merge=merge_map or None)
        session.commit()
    print(f"Ingest complete: {args.input}")


if __name__ == "__main__":
    main()
