"""
Blend viability with geographic proximity to an origin (e.g. user-picked Maps location).

Uses haversine distance; no Google API call — origin lat/lng typically come from Places / Geocoding on the client.
"""

from __future__ import annotations

import math
from models.building import BuildingEnriched


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in kilometers (WGS84 sphere)."""
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(min(1.0, math.sqrt(a)))


def proximity_score_from_km(dist_km: float) -> float:
    """0–100; high near origin, decays with distance (~half around 150 km)."""
    return 100.0 * math.exp(-max(0.0, dist_km) / 150.0)


def combined_location_score(viability: float, dist_km: float | None, location_weight: float) -> float:
    """
    ``location_weight`` in [0, 1]: 0 = pure viability; 1 = pure proximity.

    Buildings without coordinates cannot be ranked by distance, so they use viability only
    (same as turning location weight off for that row).
    """
    w = max(0.0, min(1.0, location_weight))
    if w == 0.0 or dist_km is None:
        return viability
    prox = proximity_score_from_km(dist_km)
    return (1.0 - w) * viability + w * prox


def sort_by_viability_and_proximity(
    buildings: list[BuildingEnriched],
    *,
    origin_lat: float,
    origin_lng: float,
    location_weight: float,
) -> list[BuildingEnriched]:
    """Return a new list sorted by descending combined score."""

    def dist_for(b: BuildingEnriched) -> float | None:
        if b.latitude is None or b.longitude is None:
            return None
        return haversine_km(origin_lat, origin_lng, float(b.latitude), float(b.longitude))

    def key(b: BuildingEnriched) -> float:
        d = dist_for(b)
        return combined_location_score(b.viability_score, d, location_weight)

    return sorted(buildings, key=key, reverse=True)
