"""
Pillar scores and lookups for the database seed pipeline (MVP demo data).

All pillar scores are 0–100 unless noted. ``final_viability_score`` is a weighted blend of pillars.
Formulas align with ``services/scoring.py`` subscores where possible (roof, rainfall, water price, tower).
"""

from __future__ import annotations

import math
from datetime import date
from typing import Any

from services.rainwater import annual_rainwater_gallons
from services.scoring import (
    cooling_tower_subscore,
    roof_subscore,
    water_price_subscore,
)

# --- Geography / economics (MVP: curated public-style averages; not live API data) ---------------

# City-level overrides ($/1,000 gal water, $/1,000 gal wastewater, $/mo stormwater fee) for pilot metros.
# Sources: typical municipal retail/industrial summaries & state averages (World Population Review / open data–style).
CITY_UTILITY_OVERRIDES: dict[tuple[str, str], tuple[float, float, float]] = {
    ("TX", "Dallas"): (6.20, 7.10, 120.0),
    ("TX", "Austin"): (6.80, 7.60, 95.0),
    ("TX", "Houston"): (5.90, 6.80, 110.0),
    ("TX", "Mesquite"): (6.10, 7.00, 85.0),
    ("AZ", "Phoenix"): (5.40, 6.20, 88.0),
    ("AZ", "Tucson"): (5.10, 5.90, 72.0),
    ("PA", "Philadelphia"): (7.80, 9.20, 140.0),
}

# Drought / water-stress proxy for climate pillar (higher = more stress / driver for alternative water).
STATE_CLIMATE_STRESS: dict[str, float] = {
    "TX": 74.0,
    "AZ": 90.0,
    "PA": 42.0,
    "CA": 78.0,
    "NV": 85.0,
    "NM": 82.0,
    "FL": 48.0,
    "GA": 52.0,
    "IL": 50.0,
    "OH": 44.0,
    "NY": 40.0,
    "WA": 46.0,
    "CO": 58.0,
    "NC": 50.0,
}


def resolve_utility_rates(
    state: str,
    city: str | None,
    state_water_per_1k: float,
) -> tuple[float, float, float]:
    """Return (water_cost_per_kgal, wastewater_cost_per_kgal, stormwater_fee_monthly)."""
    st = state.strip().upper()
    c = (city or "").strip()
    if c and (st, c) in CITY_UTILITY_OVERRIDES:
        return CITY_UTILITY_OVERRIDES[(st, c)]
    # State average: approximate wastewater as 1.15× potable; modest stormwater placeholder.
    w = state_water_per_1k
    ww = round(w * 1.15, 2)
    storm = 65.0 + (100.0 - min(100.0, w * 8.0))
    return (w, ww, round(storm, 2))


def climate_risk_pillar(state: str) -> float:
    st = state.strip().upper()
    return STATE_CLIMATE_STRESS.get(st, 55.0)


def utility_cost_pillar(water_per_kgal: float, ww_per_kgal: float, storm_monthly: float) -> float:
    """0–100: higher combined utility + storm fees → higher score (stronger savings case)."""
    potable = water_price_subscore(water_per_kgal)
    ww_s = water_price_subscore(ww_per_kgal)
    storm_component = min(25.0, storm_monthly / 8.0)  # up to ~25 pts from storm fees
    combined = 0.45 * potable + 0.35 * ww_s + storm_component
    return min(100.0, max(0.0, combined))


def water_yield_pillar(annual_harvest_gallons: float) -> float:
    """0–100 from harvest volume (sqrt curve vs ~15M gal/year reference)."""
    ref = 15_000_000.0
    if annual_harvest_gallons <= 0:
        return 0.0
    return min(100.0, 100.0 * math.sqrt(annual_harvest_gallons / ref))


def physical_fit_pillar(roof_area_sqft: float, cooling_tower_detected: bool, tower_confidence: float) -> float:
    """Blend roof size and cooling tower signal (0–100)."""
    r = roof_subscore(roof_area_sqft)
    t = cooling_tower_subscore(cooling_tower_detected, tower_confidence)
    return min(100.0, 0.62 * r + 0.38 * t)


def regulatory_pillar(driver_strengths: list[float]) -> float:
    if not driver_strengths:
        return 35.0
    return min(100.0, sum(driver_strengths) / len(driver_strengths))


def roi_pillar(annual_savings_usd: float) -> float:
    """0–100 from proxy annual water-cost offset (saturating curve)."""
    if annual_savings_usd <= 0:
        return 10.0
    return min(100.0, 100.0 * (1.0 - math.exp(-annual_savings_usd / 185_000.0)))


def detection_confidence_pillar(confidences: list[float]) -> float:
    if not confidences:
        return 40.0
    return min(100.0, 100.0 * (sum(confidences) / len(confidences)))


def corporate_esg_pillar(
    esg_alignment: float | None,
    has_sbt: bool | None,
    has_water: bool | None,
) -> float:
    """0–100 from company sustainability row with fallbacks."""
    base = float(esg_alignment) if esg_alignment is not None else 45.0
    if has_sbt:
        base = min(100.0, base + 12.0)
    if has_water:
        base = min(100.0, base + 8.0)
    return min(100.0, max(0.0, base))


def opportunity_tier(final: float) -> str:
    if final >= 78.0:
        return "Tier 1"
    if final >= 58.0:
        return "Tier 2"
    return "Tier 3"


# Weights for final rollup (sum = 1.0).
FINAL_WEIGHTS: dict[str, float] = {
    "physical_fit_score": 0.20,
    "water_yield_score": 0.18,
    "utility_cost_score": 0.12,
    "regulatory_score": 0.12,
    "corporate_esg_score": 0.08,
    "climate_risk_score": 0.08,
    "detection_confidence_score": 0.10,
    "roi_score": 0.12,
}


def final_viability_from_pillars(pillars: dict[str, float]) -> float:
    total = 0.0
    for k, w in FINAL_WEIGHTS.items():
        total += w * float(pillars.get(k, 0.0))
    return round(min(100.0, max(0.0, total)), 2)


# --- Geometry helpers (WGS84, axis-aligned square ~ roof area) -----------------------------------


def footprint_multipolygon_wkt(latitude: float, longitude: float, roof_area_sqft: float) -> str:
    """
    Approximate building footprint as a square in geographic coordinates.
    MVP stand-in for Microsoft US Building Footprints polygons (not bundled in repo).
    """
    half_side_ft = math.sqrt(max(roof_area_sqft, 1.0)) / 2.0
    ft_per_deg_lat = 364_000.0
    ft_per_deg_lon = 364_000.0 * math.cos(math.radians(latitude))
    dlat = half_side_ft / ft_per_deg_lat
    dlon = half_side_ft / ft_per_deg_lon
    lon0, lat0 = longitude, latitude
    ring = (
        f"{lon0 - dlon} {lat0 - dlat}, "
        f"{lon0 + dlon} {lat0 - dlat}, "
        f"{lon0 + dlon} {lat0 + dlat}, "
        f"{lon0 - dlon} {lat0 + dlat}, "
        f"{lon0 - dlon} {lat0 - dlat}"
    )
    return f"MULTIPOLYGON ((({ring})))"


def bounding_polygon_wkt(latitude: float, longitude: float, half_size_deg: float = 0.004) -> str:
    """Small AOI polygon for imagery metadata."""
    lon0, lat0 = longitude, latitude
    h = half_size_deg
    ring = (
        f"{lon0 - h} {lat0 - h}, {lon0 + h} {lat0 - h}, "
        f"{lon0 + h} {lat0 + h}, {lon0 - h} {lat0 + h}, {lon0 - h} {lat0 - h}"
    )
    return f"POLYGON (({ring}))"


# --- Harvest math (seed-specific: applies runoff + efficiency to canonical formula) ----------------

DEFAULT_RUNOFF_COEFFICIENT = 0.85
DEFAULT_SYSTEM_EFFICIENCY_PCT = 90.0


def effective_annual_harvest_gallons(
    roof_area_sqft: float,
    rainfall_inches_annual: float,
    runoff_coefficient: float = DEFAULT_RUNOFF_COEFFICIENT,
    system_efficiency_pct: float = DEFAULT_SYSTEM_EFFICIENCY_PCT,
) -> float:
    """Theoretical capture × runoff × system efficiency (MVP)."""
    raw = annual_rainwater_gallons(roof_area_sqft, rainfall_inches_annual)
    eff = (system_efficiency_pct / 100.0) if system_efficiency_pct else 1.0
    return raw * runoff_coefficient * eff


def monthly_harvest_json(annual_gallons: float) -> dict[str, Any]:
    """Seasonal shape: wetter mid-year for TX/AZ monsoon-ish; generic cosine for others."""
    months = [
        "Jan",
        "Feb",
        "Mar",
        "Apr",
        "May",
        "Jun",
        "Jul",
        "Aug",
        "Sep",
        "Oct",
        "Nov",
        "Dec",
    ]
    out: dict[str, float] = {}
    if annual_gallons <= 0:
        return {m: 0.0 for m in months}
    for i, m in enumerate(months):
        # Peak slightly in late spring / early summer (index 5–7 bump)
        seasonal = 0.85 + 0.15 * math.cos((i - 6) / 12.0 * 2 * math.pi)
        out[m] = round((annual_gallons / 12.0) * seasonal, 2)
    return out


# --- Policy rows (pilot states) -------------------------------------------------------------------

POLICY_TEMPLATES: dict[str, list[tuple[str, str, str, float | None, float]]] = {
    "TX": [
        ("State of Texas", "reuse_rule", "TCEQ guidance: authorized rainwater / condensate capture for non-potable use", None, 72.0),
        ("State of Texas", "incentive", "Property tax exemption potential for water conservation equipment (local option)", 25000.0, 58.0),
        ("Dallas-Fort Worth", "stormwater", "Municipal stormwater utility fee structure (impervious-driven)", None, 68.0),
    ],
    "AZ": [
        ("State of Arizona", "reuse_rule", "ADWR rainwater harvesting recognition; municipal reuse ordinances", None, 70.0),
        ("Maricopa County", "stormwater", "Regional stormwater quality / MS4 programs (NPDES)", None, 62.0),
        ("City of Tucson", "incentive", "Rainwater / greywater rebate programs (historical municipal programs)", 1500.0, 75.0),
    ],
    "PA": [
        ("Commonwealth of PA", "reuse_rule", "PADEP water reuse frameworks for industrial non-potable applications", None, 65.0),
        ("Philadelphia", "stormwater", "Stormwater billing based on impervious cover (strong fee driver)", None, 80.0),
        ("Philadelphia", "incentive", "Green infrastructure / stormwater credit opportunities", 5000.0, 72.0),
    ],
    "DEFAULT": [
        ("United States", "general", "Industrial water reuse guidance (EPA sector frameworks)", None, 45.0),
    ],
}


def policies_for_state(state: str) -> list[tuple[str, str, str, float | None, float]]:
    st = state.strip().upper()
    return POLICY_TEMPLATES.get(st, POLICY_TEMPLATES["DEFAULT"])


def imagery_stub(building_id: str, capture: date) -> tuple[str, str | None, float | None, float | None, str | None]:
    """Provider label, URL placeholder, resolution, cloud %, notes for SEED.md."""
    # Deterministic provider rotation
    h = abs(hash(building_id + ":img")) % 3
    providers = ("sentinel-2-l2a", "landsat-9-c2-l2", "gee-export")
    provider = providers[h]
    url = f"https://storage.example.invalid/rainuse/{building_id}/{capture.isoformat()}/tile.tif"
    res = 10.0 if provider.startswith("sentinel") else 30.0
    cloud = 4.0 + (abs(hash(building_id)) % 25)
    return provider, url, res, float(cloud), None
