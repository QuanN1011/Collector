"""Deprecated: use `ai.physical_pipeline.get_physical_analysis`. Kept for import stability."""

from ai.physical_pipeline import _mock_tower


def detect_cooling_tower(building_id: str) -> tuple[bool, float]:
    return _mock_tower(building_id)
