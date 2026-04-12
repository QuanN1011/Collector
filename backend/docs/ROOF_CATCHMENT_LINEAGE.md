# Roof catchment area & confidence (priority 2)

The hackathon brief asks for **commercial roof catchment**, a **>100,000 sq ft** flag, and **confidence** for physical signals.

## What we ship in the API

| Field | Meaning |
|-------|--------|
| **`physical_analysis.roof_catchment_sqft`** | Same as catalog **`roof_area_sqft`** (footprint / synthetic area). **Not** measured from Sentinel-2 pixels. |
| **`physical_analysis.large_roof`** | `True` when catchment ≥ **100,000** sq ft. |
| **`physical_analysis.roof_confidence`** | **0–1** confidence in that **catalog** area, from **data lineage** (how the number was produced). |
| **`physical_analysis.roof_catchment_provenance`** | Short tag: `microsoft_us_building_footprints`, `synthetic_commercial_seed`, `catalog_polygon_footprint`, etc. |

**Cooling towers** use a separate path (`cooling_tower_*` + optional live GEE/Gemini). Satellite imagery does **not** currently re-estimate roof size.

## Lineage rules (`ai/physical_pipeline._roof_lineage`)

1. **`data_source`** contains `microsoft` or equals `microsoft_us_building_footprints` → high confidence (**0.88**).
2. **`data_source`** `synthetic_commercial_seed` or synthetic seed **`id`** prefix `bru-` → demo seed (**0.72**).
3. **`data_source`** `synthetic_polygon_from_area` → square footprint from area only (**0.74**).
4. **`has_footprint_polygon`** (WKT in CSV or PostGIS geom) without the above → **0.84** `catalog_polygon_footprint`.
5. Otherwise → **0.68** `catalog_area_only`.

## Database & CSV

- **Postgres:** `buildings.data_source` (nullable `VARCHAR(64)`), set in **`seed_database.py`**:  
  - explicit CSV column `data_source`, else  
  - `microsoft_us_building_footprints` if **`footprint_wkt`** present, else  
  - `synthetic_commercial_seed`.
- **CSV fallback:** optional columns **`data_source`**, **`footprint_wkt`** (see `database/db._load_buildings_csv`).

Migration: **`b2f8a1c0d4e1_add_building_data_source`**.

## Frontend copy suggestion

> Roof size is from our building footprint catalog; confidence reflects dataset quality, not satellite measurement. Cooling-tower signal may use satellite + AI when enabled.

See also: [VISION_PIPELINE.md](./VISION_PIPELINE.md), [CV_IMPLEMENTATION_SUMMARY.md](./CV_IMPLEMENTATION_SUMMARY.md).
