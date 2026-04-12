"""
Deterministic SBTi-aligned ESG subscores for company-level sustainability (phase 1).

Source of truth: offline CSV ingested into ``company_sustainability_profiles`` (see
``scripts/ingest_sbti_csv.py``). No live SBTi API calls in request paths.

Alignment score 0–100 is derived from public SBTi-style commitment labels using the
mapping below (same inputs → same score, reproducible).
"""

from __future__ import annotations

import re
from typing import Any, Literal

# Confidence for rows matched from a checked-in SBTi snapshot CSV (not a statistical estimate).
DEFAULT_SBTI_CONFIDENCE = 0.88

EsgStatus = Literal["real", "proxy", "unavailable"]


def _norm(s: str | None) -> str:
    return re.sub(r"\s+", " ", (s or "").strip().lower())


def compute_sbti_alignment_subscore(near_term_status: str, net_zero_status: str) -> float:
    """
    Map SBTi dashboard-style status strings to a single 0–100 subscore.

    Rules (documented, deterministic):
    - If **net-zero** column indicates commitment / target set → base high tier.
    - Else if **near-term** column indicates targets set / committed → mid tier.
    - Else → lower tier (ingest should normally only include companies with targets).

    Matching is keyword-based on normalized lowercase strings (no ML).
    """
    nt = _norm(near_term_status)
    nz = _norm(net_zero_status)

    def _nz_committed() -> bool:
        if not nz:
            return False
        return any(
            k in nz
            for k in (
                "committed",
                "commitment",
                "target set",
                "targets set",
                "approved",
                "net-zero",
                "net zero",
            )
        )

    def _nt_committed() -> bool:
        if not nt:
            return False
        return any(
            k in nt
            for k in (
                "committed",
                "commitment",
                "target set",
                "targets set",
                "approved",
            )
        )

    if _nz_committed() and _nt_committed():
        return 95.0
    if _nz_committed():
        return 90.0
    if _nt_committed():
        return 78.0
    if nt or nz:
        return 62.0
    return 45.0


def esg_applies_to_viability(profile: Any) -> bool:
    """True when profile should contribute the 0.10 ESG weight (SBTi or documented proxy only)."""
    if profile is None or profile.esg_alignment_score is None:
        return False
    src = (profile.esg_source or "").strip().lower()
    if not src:
        return False
    if src == "sbti" or src.startswith("sbti"):
        return True
    if src in ("documented_industry_proxy", "documented_proxy"):
        return True
    return False


def api_esg_status(profile: Any) -> EsgStatus:
    if profile is None or profile.esg_alignment_score is None:
        return "unavailable"
    src = (profile.esg_source or "").strip().lower()
    if not src:
        return "unavailable"
    if src == "sbti" or src.startswith("sbti"):
        return "real"
    if src in ("documented_industry_proxy", "documented_proxy"):
        return "proxy"
    return "unavailable"


def merge_esg_details(profile: Any) -> dict[str, Any]:
    base: dict[str, Any] = {}
    if profile and profile.esg_details and isinstance(profile.esg_details, dict):
        base.update(profile.esg_details)
    if profile and profile.esg_source:
        base.setdefault("primary_source", profile.esg_source)
    return base
