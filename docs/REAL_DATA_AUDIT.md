# Real data audit (RainUSE Nexus prospecting)

This document maps **UI/API fields** to **sources**, classifies **mock vs real**, and tracks **implementation status** after the “real data first” pass.

## Rule: what counts as “real”

A value is **real** only if it comes from one of:

- An imported authoritative dataset (CSV/Postgres catalog),
- A trusted external API,
- CV/model output run on real imagery,
- A **deterministic formula** applied to **real inputs** (documented in code).

Anything else must be **null**, **unavailable**, or explicitly labeled—not a plausible fake.

## Field matrix

| UI/API field | Current source | Current status | Desired real source | Implementation status | Notes / blockers |
|--------------|----------------|----------------|---------------------|----------------------|-------------------|
| Building name | `buildings` table / `data/buildings.csv` | Real (catalog) | Same | Done | `database/db.py` `list_buildings` / `get_building` |
| City | `buildings` | Real | Same | Done | |
| State | `buildings` | Real | Same | Done | |
| Lat / lon | `buildings` | Real when present | Same | Done | Missing coords block GEE imagery → tower `unavailable` |
| `roof_area_sqft` | `buildings` | Real | Same | Done | Used as catalog catchment for rainwater math |
| Catchment area (analysis) | Same as roof area | Derived | Same | Done | `physical_analysis.roof_catchment_sqft` |
| `rainfall_inches_annual` | `state_context` (Postgres or CSV) | Real | Same | Done | `backend/data/state_context.csv` or `state_context` table |
| `water_price_per_1000_gal_usd` | `state_context` | Real | Same | Done | Documented in `backend/docs/DATA_SOURCES_WATER_PRICING.md` |
| Annual rainwater gallons | Formula on catchment + rainfall | Derived (real inputs) | Same | Done | `services/rainwater.py` |
| Annual savings (USD) | Formula on gallons + price | Derived (real inputs) | Same | Done | `services/roi.py` |
| Cooling tower presence / confidence | GEE + Gemini when `live_cv=true` | **Real** only on success; else **unavailable** | Same | Done | No hash/mock; see `ai/physical_pipeline.py` |
| ESG score | — | **Unavailable** | `CompanySustainabilityProfile` + linkage | Not done | `esg_signal_score` is `null`; reason in `esg_unavailable_reason` |
| Viability score | `services/scoring.py` | Derived from real state context; optional tower | Same | Done | `partial` when tower omitted; weights in `provenance` |
| Viability breakdown | Same | Derived | Same | Done | Keys: `rainfall`, `water_price`, optional `cooling_tower` |
| Provenance / analysis mode / freshness | `BuildingEnriched.provenance` + `physical_analysis` | Real metadata | Same | Done | `viability.computed_at_utc`, inference timestamps when present |

## Removed / non-user-facing mock paths

| Item | Location | Resolution |
|------|----------|------------|
| `_mock_tower` / hash tower | ~~`physical_pipeline.py`~~ | Removed |
| `mock_esg_subscore` | ~~`scoring.py` / `enrichment.py`~~ | Removed |
| `building_scores.final_viability_score` override | ~~`enrichment.py`~~ | Removed from prospecting API |
| `detect_cooling_tower(building_id)` hash | `cooling_tower_detection.py` | Returns `(False, 0.0)` for seed scripts only; API uses `get_physical_analysis` |
| Seed `CvDetection` deterministic variety | `seed_database.py` | Still uses hash for **demo DB rows**; **not** read by GET `/building` enrichment |

## Checklist: main prospecting flow

- [x] No hash-based tower or ESG in API responses
- [x] No `final_viability_score` seed override in enrichment
- [x] Cooling tower: `real_detected` \| `real_not_detected` \| `unavailable` via `physical_analysis.tower_status`
- [x] Viability `full` vs `partial` + `viability_missing_components`
- [x] Structured `provenance` object on each enriched building
- [ ] ESG from real company data (blocked on ingest + API wiring)
- [ ] Optional: `state_context` row-level `updated_at` for freshness (schema follow-up)

See also: [REAL_DATA_SOURCES.md](./REAL_DATA_SOURCES.md), [PROVENANCE_MODEL.md](./PROVENANCE_MODEL.md).
