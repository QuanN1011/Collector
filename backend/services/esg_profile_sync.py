"""
Canonical ESG profile construction from checked-in CSV (single source for seed + refresh + verify).

Rules:
- ``esg_alignment_score`` is **always** derived from ``near_term_status`` + ``net_zero_status``
  via ``compute_sbti_alignment_subscore`` — never taken from a legacy numeric column.
- ``esg_source`` defaults to ``SBTi`` when present in CSV (trimmed).
- Booleans and ``climate_risk_score`` come from the CSV as authoritative non-ESG fields.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from database.tables import CompanySustainabilityProfile
from services.sbti_esg import DEFAULT_SBTI_CONFIDENCE, compute_sbti_alignment_subscore


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


def _parse_sbti_ingested_at(raw: str | None) -> datetime | None:
    if raw is None or str(raw).strip() == "":
        return None
    return datetime.fromisoformat(str(raw).strip().replace("Z", "+00:00"))


def company_sustainability_profile_from_csv_row(row: dict[str, str]) -> CompanySustainabilityProfile:
    """
    Build an ORM object from one row of ``company_sustainability_profiles.csv``.

    Column expectations match ``backend/data/company_sustainability_profiles.csv``.
    """
    cid = row["company_id"].strip()
    nt = (row.get("near_term_status") or "").strip()
    nz = (row.get("net_zero_status") or "").strip()
    align = compute_sbti_alignment_subscore(nt, nz)
    conf = _parse_opt_float(row.get("esg_confidence"))
    if conf is None:
        conf = DEFAULT_SBTI_CONFIDENCE
    src = (row.get("esg_source") or "").strip() or "SBTi"
    ingested = _parse_sbti_ingested_at(row.get("sbti_ingested_at"))
    details: dict = {
        "near_term_status": nt or None,
        "net_zero_status": nz or None,
        "dataset": "SBTi_offline_seed",
    }
    return CompanySustainabilityProfile(
        company_id=cid,
        has_esg_report=_parse_bool(row.get("has_esg_report")),
        has_water_target=_parse_bool(row.get("has_water_target")),
        has_science_based_target=_parse_bool(row.get("has_science_based_target")),
        climate_risk_score=_parse_opt_float(row.get("climate_risk_score")),
        esg_alignment_score=align,
        esg_source=src,
        esg_confidence=conf,
        sbti_ingested_at=ingested,
        esg_details=details,
    )


def expected_alignment_from_row(row: dict[str, str]) -> float:
    nt = (row.get("near_term_status") or "").strip()
    nz = (row.get("net_zero_status") or "").strip()
    return compute_sbti_alignment_subscore(nt, nz)


def esg_details_equivalent(a: dict | None, b: dict | None) -> bool:
    """Compare near_term / net_zero only (dataset tag may differ until refresh)."""
    if a is None and b is None:
        return True
    if not isinstance(a, dict) or not isinstance(b, dict):
        return False
    return (a.get("near_term_status") or None) == (b.get("near_term_status") or None) and (
        (a.get("net_zero_status") or None) == (b.get("net_zero_status") or None)
    )


def refresh_profiles_from_csv(csv_path: Path) -> int:
    """
    Upsert every row from the canonical CSV into ``company_sustainability_profiles``.
    Idempotent; safe to rerun after updating the CSV or scoring rules.
    """
    import csv

    from database.engine import get_session_factory, init_db
    from database.tables import CompanySustainabilityProfile

    init_db()
    with csv_path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    SessionLocal = get_session_factory()
    n = 0
    with SessionLocal() as session:
        for row in rows:
            if not (row.get("company_id") or "").strip():
                continue
            fresh = company_sustainability_profile_from_csv_row(row)
            existing = session.get(CompanySustainabilityProfile, fresh.company_id)
            if existing is None:
                session.add(fresh)
            else:
                existing.has_esg_report = fresh.has_esg_report
                existing.has_water_target = fresh.has_water_target
                existing.has_science_based_target = fresh.has_science_based_target
                existing.climate_risk_score = fresh.climate_risk_score
                existing.esg_alignment_score = fresh.esg_alignment_score
                existing.esg_source = fresh.esg_source
                existing.esg_confidence = fresh.esg_confidence
                existing.sbti_ingested_at = fresh.sbti_ingested_at
                existing.esg_details = fresh.esg_details
            n += 1
        session.commit()
    return n
