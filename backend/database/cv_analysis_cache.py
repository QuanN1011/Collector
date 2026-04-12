"""
Persisted cache for Static Maps + Gemini roof analysis (``GET /building/{id}?live_cv=true``).

Uses Postgres table ``building_cv_analysis`` when ``DATABASE_URL`` is set; otherwise an in-process dict.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from database.config import use_database
from database.engine import get_session_factory
from database.tables import BuildingCvAnalysis as BuildingCvAnalysisRow

_memory: dict[str, "CvAnalysisSnapshot"] = {}


@dataclass(frozen=True)
class CvAnalysisSnapshot:
    building_id: str
    roof_estimated_sqft: float
    roof_large_flag: bool
    cooling_tower_detected: bool
    roof_confidence: float
    cooling_tower_confidence: float
    reasoning: str
    created_at: datetime


def _row_to_snapshot(row: BuildingCvAnalysisRow) -> CvAnalysisSnapshot:
    return CvAnalysisSnapshot(
        building_id=row.building_id,
        roof_estimated_sqft=float(row.roof_estimated_sqft),
        roof_large_flag=bool(row.roof_large_flag),
        cooling_tower_detected=bool(row.cooling_tower_detected),
        roof_confidence=float(row.roof_confidence),
        cooling_tower_confidence=float(row.cooling_tower_confidence),
        reasoning=(row.reasoning or "").strip(),
        created_at=row.created_at,
    )


def get_cached_cv_analysis(building_id: str) -> CvAnalysisSnapshot | None:
    bid = building_id.strip()
    if use_database():
        SessionLocal = get_session_factory()
        with SessionLocal() as session:
            row = session.get(BuildingCvAnalysisRow, bid)
            return _row_to_snapshot(row) if row else None
    return _memory.get(bid)


def save_cached_cv_analysis(
    building_id: str,
    *,
    roof_estimated_sqft: float,
    roof_large_flag: bool,
    cooling_tower_detected: bool,
    roof_confidence: float,
    cooling_tower_confidence: float,
    reasoning: str,
    session: Session | None = None,
) -> None:
    bid = building_id.strip()
    now = datetime.now(timezone.utc)
    reasoning_clean = (reasoning or "").strip()[:8000]

    if use_database():
        if session is not None:
            _save_session(
                session,
                bid,
                roof_estimated_sqft,
                roof_large_flag,
                cooling_tower_detected,
                roof_confidence,
                cooling_tower_confidence,
                reasoning_clean,
                now,
            )
            return
        SessionLocal = get_session_factory()
        with SessionLocal() as s:
            _save_session(
                s,
                bid,
                roof_estimated_sqft,
                roof_large_flag,
                cooling_tower_detected,
                roof_confidence,
                cooling_tower_confidence,
                reasoning_clean,
                now,
            )
            s.commit()
        return

    _memory[bid] = CvAnalysisSnapshot(
        building_id=bid,
        roof_estimated_sqft=roof_estimated_sqft,
        roof_large_flag=roof_large_flag,
        cooling_tower_detected=cooling_tower_detected,
        roof_confidence=roof_confidence,
        cooling_tower_confidence=cooling_tower_confidence,
        reasoning=reasoning_clean,
        created_at=now,
    )


def _save_session(
    session: Session,
    bid: str,
    roof_estimated_sqft: float,
    roof_large_flag: bool,
    cooling_tower_detected: bool,
    roof_confidence: float,
    cooling_tower_confidence: float,
    reasoning: str,
    now: datetime,
) -> None:
    row = session.get(BuildingCvAnalysisRow, bid)
    if row is None:
        row = BuildingCvAnalysisRow(building_id=bid)
        session.add(row)
    row.roof_estimated_sqft = roof_estimated_sqft
    row.roof_large_flag = roof_large_flag
    row.cooling_tower_detected = cooling_tower_detected
    row.roof_confidence = roof_confidence
    row.cooling_tower_confidence = cooling_tower_confidence
    row.reasoning = reasoning
    row.created_at = now
