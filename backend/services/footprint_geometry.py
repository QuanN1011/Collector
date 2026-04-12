"""Footprint geometry helpers for Microsoft GeoJSON → PostGIS-compatible WKT."""

from __future__ import annotations

import math
from typing import Any

from pyproj import Transformer
from shapely.geometry import MultiPolygon, shape
from shapely.ops import transform


def _utm_epsg_for_lon_lat(lon: float, lat: float) -> int:
    zone = int(math.floor((lon + 180) / 6) + 1)
    if lat >= 0:
        return 32600 + zone
    return 32700 + zone


def polygon_area_sqft(geom_dict: dict[str, Any]) -> float:
    """Geodesic-ish area via UTM projection (good for building-scale polygons)."""
    g = shape(geom_dict)
    if g.is_empty:
        return 0.0
    if g.geom_type == "MultiPolygon":
        g = max(g.geoms, key=lambda x: x.area)
    elif g.geom_type != "Polygon":
        return 0.0
    centroid = g.centroid
    lon, lat = centroid.x, centroid.y
    epsg = _utm_epsg_for_lon_lat(lon, lat)
    project = Transformer.from_crs("EPSG:4326", f"EPSG:{epsg}", always_xy=True).transform
    g2 = transform(project, g)
    m2 = g2.area
    return m2 * 10.76391041671  # ft²


def footprint_to_multipolygon_wkt(geom_dict: dict[str, Any]) -> str:
    """Normalize Polygon/MultiPolygon to MULTIPOLYGON WKT for ``buildings.footprint_geom``."""
    g = shape(geom_dict)
    if g.geom_type == "Polygon":
        g = MultiPolygon([g])
    elif g.geom_type == "MultiPolygon":
        pass
    else:
        raise ValueError(f"Unsupported geometry type: {g.geom_type}")
    return g.wkt
