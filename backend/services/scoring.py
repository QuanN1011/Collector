"""
Viability score 0–100: weighted blend of state context, optional cooling-tower inference, optional ESG.

- Rainfall and water price: ``state_context`` (Postgres or CSV).
- Cooling tower: only when live CV returns real_detected/real_not_detected.
- ESG: fixed weight 0.10 when ``esg_subscore`` is provided (SBTi / documented proxy in DB); omitted otherwise.

Base weights (before omitting optional pillars): rainfall 0.35, water_price 0.25, cooling_tower 0.25,
esg 0.10. Omitted pillars are excluded and remaining weights renormalized to sum to 1.0.
"""

from __future__ import annotations

import math
from typing import Literal

from models.building import TowerStatus

# Reference scales for normalization (continental US–typical ranges)
RAINFALL_REF_INCHES = 50.0  # ~wet Gulf Coast
WATER_PRICE_REF_USD_PER_1000_GAL = 9.0  # high retail-ish municipal water
# Roof catchment scale for seed / physical-fit pillar (not used in API viability blend)
ROOF_AREA_REF_SQFT = 250_000.0

WEIGHT_RAINFALL = 0.35
WEIGHT_WATER_PRICE = 0.25
WEIGHT_COOLING_TOWER = 0.25
WEIGHT_ESG = 0.10


def _clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))


def rainfall_subscore(rainfall_inches_annual: float) -> float:
    """0–100; linear vs reference wet climate."""
    return 100.0 * _clamp01(rainfall_inches_annual / RAINFALL_REF_INCHES)


def water_price_subscore(water_price_per_1000_gal_usd: float) -> float:
    """0–100; higher price → higher score."""
    return 100.0 * _clamp01(water_price_per_1000_gal_usd / WATER_PRICE_REF_USD_PER_1000_GAL)


def roof_subscore(roof_area_sqft: float) -> float:
    """0–100 from footprint / catchment area (seed pipeline + physical_fit_pillar; saturating vs ref)."""
    if roof_area_sqft <= 0:
        return 0.0
    return 100.0 * _clamp01(math.sqrt(roof_area_sqft / ROOF_AREA_REF_SQFT))


def cooling_tower_subscore(detected: bool, confidence: float) -> float:
    """0–100 from real vision output (not used when tower unavailable)."""
    if not detected:
        return 15.0
    return 40.0 + 60.0 * _clamp01(confidence)


def esg_subscore_from_alignment(esg_alignment_0_100: float) -> float:
    """0–100; profile score is already on viability scale."""
    return max(0.0, min(100.0, float(esg_alignment_0_100)))


def compute_viability(
    *,
    rainfall_inches_annual: float,
    water_price_per_1000_gal_usd: float,
    tower_status: TowerStatus,
    cooling_tower_detected: bool | None,
    cooling_tower_confidence: float | None,
    esg_subscore: float | None = None,
) -> tuple[float, dict[str, float], list[str], Literal["full", "partial"], dict[str, float]]:
    """
    Returns (score, breakdown, missing_components, completeness, weights_applied).

    ``completeness`` remains **full** when the cooling-tower pillar is included; **partial** when
    tower inference is unavailable. Missing ESG does not flip this flag (ESG is optional).
    """
    rain = rainfall_subscore(rainfall_inches_annual)
    price = water_price_subscore(water_price_per_1000_gal_usd)

    missing: list[str] = []
    breakdown: dict[str, float] = {
        "rainfall": round(rain, 2),
        "water_price": round(price, 2),
    }

    include_tower = tower_status in ("real_detected", "real_not_detected") and (
        cooling_tower_detected is not None and cooling_tower_confidence is not None
    )
    include_esg = esg_subscore is not None

    if not include_esg:
        missing.append("esg")

    w_r = WEIGHT_RAINFALL
    w_p = WEIGHT_WATER_PRICE
    w_t = WEIGHT_COOLING_TOWER if include_tower else 0.0
    w_e = WEIGHT_ESG if include_esg else 0.0

    if include_tower:
        tower = cooling_tower_subscore(bool(cooling_tower_detected), float(cooling_tower_confidence))
        breakdown["cooling_tower"] = round(tower, 2)
        completeness: Literal["full", "partial"] = "full"
    else:
        missing.append("cooling_tower")
        completeness = "partial"

    if include_esg:
        breakdown["esg"] = round(esg_subscore_from_alignment(float(esg_subscore)), 2)

    s = w_r + w_p + w_t + w_e
    weights = {
        "rainfall": w_r / s,
        "water_price": w_p / s,
    }
    if include_tower:
        weights["cooling_tower"] = w_t / s
    if include_esg:
        weights["esg"] = w_e / s

    total = sum(breakdown[k] * weights[k] for k in weights)
    score = round(min(100.0, max(0.0, total)), 2)
    return score, breakdown, missing, completeness, weights
