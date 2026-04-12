"""
Legacy module: production prospecting uses ``ai.physical_pipeline.get_physical_analysis``.

The seed script previously imported a hash-based tower helper; that path is removed from the
main API. Do not use this module for user-facing scores.
"""

from __future__ import annotations


def detect_cooling_tower(_building_id: str) -> tuple[bool, float]:
    """
    Deprecated. Returns a neutral non-inference placeholder for offline seed scripts only.

    Real cooling-tower state for the API comes from ``get_physical_analysis`` (GEE + Gemini).
    """
    return False, 0.0
