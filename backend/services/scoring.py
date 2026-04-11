"""
Viability score 0–100: weighted blend of physical fit, water economics, and mock signals.

Weights (must sum to 1.0):
- roof: 0.35  — large commercial roofs (>100k sq ft) score highest
- rainfall: 0.25 — more annual precipitation → more harvest
- water_price: 0.15 — higher utility cost → stronger ROI proxy
- cooling_tower: 0.15 — towers increase evaporative load / reuse value (mock)
- esg: 0.10 — optional corporate sustainability signal (mock)
"""

from __future__ import annotations

# Reference scales for normalization (continental US–typical ranges)
ROOF_AREA_TARGET_SQFT = 100_000.0
RAINFALL_REF_INCHES = 50.0  # ~wet Gulf Coast
WATER_PRICE_REF_USD_PER_1000_GAL = 9.0  # high retail-ish municipal water


def _clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))


def roof_subscore(roof_area_sqft: float) -> float:
    """0–100; >=100k sq ft → 100."""
    return 100.0 * _clamp01(roof_area_sqft / ROOF_AREA_TARGET_SQFT)


def rainfall_subscore(rainfall_inches_annual: float) -> float:
    """0–100; linear vs reference wet climate."""
    return 100.0 * _clamp01(rainfall_inches_annual / RAINFALL_REF_INCHES)


def water_price_subscore(water_price_per_1000_gal_usd: float) -> float:
    """0–100; higher price → higher score."""
    return 100.0 * _clamp01(water_price_per_1000_gal_usd / WATER_PRICE_REF_USD_PER_1000_GAL)


def cooling_tower_subscore(detected: bool, confidence: float) -> float:
    """0–100; mock vision output."""
    if not detected:
        return 15.0
    return 40.0 + 60.0 * _clamp01(confidence)


def mock_esg_subscore(building_id: str) -> float:
    """0–100 placeholder until SEC / SBTi ingestion exists."""
    h = abs(hash(building_id + ":esg")) % (2**31)
    return float(h % 101)


def compute_viability(
    roof_area_sqft: float,
    rainfall_inches_annual: float,
    water_price_per_1000_gal_usd: float,
    cooling_tower_detected: bool,
    cooling_tower_confidence: float,
    building_id: str,
) -> tuple[float, dict[str, float]]:
    r = roof_subscore(roof_area_sqft)
    rain = rainfall_subscore(rainfall_inches_annual)
    price = water_price_subscore(water_price_per_1000_gal_usd)
    tower = cooling_tower_subscore(cooling_tower_detected, cooling_tower_confidence)
    esg = mock_esg_subscore(building_id)

    total = (
        0.35 * r
        + 0.25 * rain
        + 0.15 * price
        + 0.15 * tower
        + 0.10 * esg
    )
    breakdown = {
        "roof": round(r, 2),
        "rainfall": round(rain, 2),
        "water_price": round(price, 2),
        "cooling_tower": round(tower, 2),
        "esg_mock": round(esg, 2),
    }
    return round(min(100.0, max(0.0, total)), 2), breakdown
