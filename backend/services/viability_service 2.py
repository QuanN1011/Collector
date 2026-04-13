"""
Viability 0–100 from roof size, rainfall, cooling tower, and water price (no mock ESG).
"""

from __future__ import annotations

from typing import Any

from services.scoring import (
    cooling_tower_subscore,
    rainfall_subscore,
    roof_subscore,
    water_price_subscore,
)


def calculate_viability(building: dict[str, Any]) -> float:
    """
    Required keys: roof_area_sqft, rainfall_inches_annual, water_price_per_1000_gal_usd,
    cooling_tower_detected, cooling_tower_confidence.
    """
    roof = float(building["roof_area_sqft"])
    rain_in = float(building["rainfall_inches_annual"])
    price = float(building["water_price_per_1000_gal_usd"])
    tower_ok = bool(building["cooling_tower_detected"])
    tower_conf = float(building["cooling_tower_confidence"])

    r_score = roof_subscore(roof)
    rain_score = rainfall_subscore(rain_in)
    price_score = water_price_subscore(price)
    tower_score = cooling_tower_subscore(tower_ok, tower_conf)

    total = 0.25 * r_score + 0.25 * rain_score + 0.25 * price_score + 0.25 * tower_score
    return round(min(100.0, max(0.0, total)), 2)
