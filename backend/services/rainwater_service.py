"""Annual rainwater capture (gallons) — hackathon Maps + Gemini pipeline."""

from __future__ import annotations

# Same coefficient as ``services.rainwater`` (DOE-style factor).
_RAINFALL_COEFFICIENT = 0.623


def calculate_rainwater(roof_area_sqft: float, rainfall_inches: float) -> float:
    """``rainwater_gallons = roof_area_sqft * rainfall_inches * 0.623``."""
    return roof_area_sqft * rainfall_inches * _RAINFALL_COEFFICIENT
