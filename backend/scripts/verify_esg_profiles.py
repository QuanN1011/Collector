"""
Verify ``company_sustainability_profiles`` against the canonical CSV and building coverage.

Compares DB rows to ``backend/data/company_sustainability_profiles.csv`` (same construction as
``services.esg_profile_sync.company_sustainability_profile_from_csv_row``).

Exit codes:
  0 — no mismatches, no incomplete rows, no orphans (unless only orphans with --fail-on-orphans off)
  1 — problems found (dry-run)
  2 — bad args / no DATABASE_URL

Usage::

  python scripts/verify_esg_profiles.py [--csv PATH] [--fix] [--fail-on-orphans]
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path
from typing import Any

_BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

from env_load import load_backend_env

load_backend_env()

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from database.config import get_database_url
from database.engine import get_session_factory, init_db
from database.tables import Building, CompanySustainabilityProfile
from services.esg_profile_sync import (
    company_sustainability_profile_from_csv_row,
    esg_details_equivalent,
    expected_alignment_from_row,
)
from services.sbti_esg import esg_applies_to_viability


def _load_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _fclose(a: float | None, b: float | None, eps: float = 1e-5) -> bool:
    if a is None and b is None:
        return True
    if a is None or b is None:
        return False
    return abs(float(a) - float(b)) < eps


def _src_ok(s: str | None) -> bool:
    if not s or not str(s).strip():
        return False
    sl = str(s).strip().lower()
    return sl == "sbti" or sl.startswith("sbti") or sl in ("documented_industry_proxy", "documented_proxy")


def _compare_profile(db: CompanySustainabilityProfile, row: dict[str, str]) -> list[str]:
    issues: list[str] = []
    exp = company_sustainability_profile_from_csv_row(row)
    if not _fclose(db.esg_alignment_score, exp.esg_alignment_score):
        issues.append(
            f"esg_alignment_score db={db.esg_alignment_score} expected={exp.esg_alignment_score} "
            f"(recomputed from near_term/net_zero)"
        )
    dbs = (db.esg_source or "").strip().lower()
    exs = (exp.esg_source or "").strip().lower()
    if dbs != exs:
        issues.append(f"esg_source db={db.esg_source!r} expected={exp.esg_source!r}")
    if not _fclose(db.esg_confidence, exp.esg_confidence):
        issues.append(f"esg_confidence db={db.esg_confidence} expected={exp.esg_confidence}")
    if (db.sbti_ingested_at is None) != (exp.sbti_ingested_at is None):
        issues.append(f"sbti_ingested_at presence mismatch db={db.sbti_ingested_at} expected={exp.sbti_ingested_at}")
    elif db.sbti_ingested_at and exp.sbti_ingested_at:
        if db.sbti_ingested_at.replace(microsecond=0) != exp.sbti_ingested_at.replace(microsecond=0):
            issues.append(f"sbti_ingested_at db={db.sbti_ingested_at} expected={exp.sbti_ingested_at}")
    if not esg_details_equivalent(db.esg_details, exp.esg_details):
        issues.append(f"esg_details near_term/net_zero differ db={db.esg_details} expected={exp.esg_details}")
    if db.has_esg_report != exp.has_esg_report:
        issues.append(f"has_esg_report db={db.has_esg_report} expected={exp.has_esg_report}")
    if db.has_water_target != exp.has_water_target:
        issues.append(f"has_water_target db={db.has_water_target} expected={exp.has_water_target}")
    if db.has_science_based_target != exp.has_science_based_target:
        issues.append(
            f"has_science_based_target db={db.has_science_based_target} expected={exp.has_science_based_target}"
        )
    if not _fclose(db.climate_risk_score, exp.climate_risk_score):
        issues.append(f"climate_risk_score db={db.climate_risk_score} expected={exp.climate_risk_score}")
    return issues


def _incomplete_row(db: CompanySustainabilityProfile) -> list[str]:
    bad: list[str] = []
    if db.esg_alignment_score is not None:
        if not (db.esg_source and str(db.esg_source).strip()):
            bad.append("esg_alignment_score set but esg_source empty")
        if db.esg_confidence is None:
            bad.append("esg_confidence null")
        if db.sbti_ingested_at is None and _src_ok(db.esg_source):
            bad.append("sbti_ingested_at null (SBTi rows should have snapshot time)")
        if db.esg_details is None or not isinstance(db.esg_details, dict):
            bad.append("esg_details missing or not object")
        elif not (
            db.esg_details.get("near_term_status") is not None or db.esg_details.get("net_zero_status") is not None
        ):
            if _src_ok(db.esg_source):
                bad.append("esg_details missing near_term/net_zero for SBTi row")
    return bad


def _building_report(session: Session) -> dict[str, Any]:
    total = session.scalar(select(func.count()).select_from(Building)) or 0
    with_cid = (
        session.scalar(select(func.count()).select_from(Building).where(Building.company_id.is_not(None))) or 0
    )
    missing_prof: list[tuple[str, str | None, str | None]] = []
    non_qual: list[tuple[str, str | None, str]] = []
    qual: list[str] = []
    for b in session.scalars(select(Building)).all():
        if not b.company_id:
            continue
        p = session.get(CompanySustainabilityProfile, b.company_id)
        if p is None:
            missing_prof.append((b.id, b.name, b.company_id))
            continue
        if esg_applies_to_viability(p):
            qual.append(b.id)
        else:
            non_qual.append((b.id, b.name, "profile does not qualify (esg_source or score)"))

    return {
        "total_buildings": total,
        "buildings_with_company_id": with_cid,
        "buildings_qualifying_esg": len(qual),
        "buildings_non_qualifying_esg": len(non_qual),
        "buildings_missing_company_profile": len(missing_prof),
        "sample_missing_profile": missing_prof[:5],
        "sample_non_qual": non_qual[:5],
    }


def _analyze(
    canonical_rows: list[dict[str, str]],
    db_profiles: dict[str, CompanySustainabilityProfile],
) -> tuple[int, list[tuple[str, list[str]]], list[tuple[str, list[str]]], list[str]]:
    canon_ids = {r["company_id"].strip() for r in canonical_rows if (r.get("company_id") or "").strip()}
    mismatched: list[tuple[str, list[str]]] = []
    incomplete: list[tuple[str, list[str]]] = []
    ok = 0

    for row in canonical_rows:
        cid = (row.get("company_id") or "").strip()
        if not cid:
            continue
        exp_score = expected_alignment_from_row(row)
        db = db_profiles.get(cid)
        if db is None:
            mismatched.append((cid, [f"missing row in DB (expected alignment {exp_score})"]))
            continue
        probs = _compare_profile(db, row)
        inc = _incomplete_row(db)
        if inc:
            incomplete.append((cid, inc))
        if probs:
            mismatched.append((cid, probs))
        if not probs and not inc:
            ok += 1

    orphans = [cid for cid in db_profiles if cid not in canon_ids]
    return ok, mismatched, incomplete, orphans


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify ESG profiles vs canonical CSV.")
    parser.add_argument("--csv", type=Path, default=_BACKEND_ROOT / "data" / "company_sustainability_profiles.csv")
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Run refresh_profiles_from_csv then re-verify.",
    )
    parser.add_argument(
        "--fail-on-orphans",
        action="store_true",
        help="Treat DB profiles whose company_id is not in canonical CSV as errors.",
    )
    args = parser.parse_args()

    if not get_database_url():
        print("ERROR: DATABASE_URL not set", file=sys.stderr)
        return 2
    if not args.csv.is_file():
        print(f"ERROR: canonical CSV not found: {args.csv}", file=sys.stderr)
        return 2

    init_db()
    canonical_rows = _load_csv(args.csv)

    SessionLocal = get_session_factory()

    def load_profiles() -> dict[str, CompanySustainabilityProfile]:
        with SessionLocal() as session:
            return {p.company_id: p for p in session.scalars(select(CompanySustainabilityProfile)).all()}

    if args.fix:
        from services.esg_profile_sync import refresh_profiles_from_csv

        print("Running refresh_profiles_from_csv...")
        refresh_profiles_from_csv(args.csv)
        print("Refresh committed.\n")

    db_profiles = load_profiles()
    ok, mismatched, incomplete, orphans = _analyze(canonical_rows, db_profiles)

    print("## ESG verification report")
    print(f"Canonical CSV: {args.csv}")
    print(f"OK rows (match canonical): {ok}")
    print(f"Mismatched / missing canonical rows: {len(mismatched)}")
    print(f"Incomplete (guardrail) rows: {len(incomplete)}")
    print(f"Orphan DB profiles (not in canonical): {len(orphans)}")
    for cid, probs in mismatched[:15]:
        print(f"  - {cid}: {probs}")
    if len(mismatched) > 15:
        print(f"  ... and {len(mismatched) - 15} more")
    for cid, inc in incomplete[:10]:
        print(f"  incomplete {cid}: {inc}")
    for o in orphans[:10]:
        print(f"  orphan: {o}")

    with SessionLocal() as session:
        br = _building_report(session)
    print("\n## Building ESG coverage")
    for k, v in br.items():
        print(f"  {k}: {v}")

    bad = len(mismatched) + len(incomplete)
    if args.fail_on_orphans:
        bad += len(orphans)

    if bad > 0:
        print(f"\nExit 1: {bad} issue group(s)")
        return 1
    if orphans and not args.fail_on_orphans:
        print("\nNote: orphan profiles present; use --fail-on-orphans to fail CI on them.")
    print("\nExit 0: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
