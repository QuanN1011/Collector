# Real data sources (prospecting API)

## Buildings catalog

- **Postgres:** `buildings` table (`database/tables.py`), loaded via ingest or `scripts/seed_database.py`.
- **Fallback:** `backend/data/buildings_catalog.csv` when present, else `backend/data/buildings.csv`, when `DATABASE_URL` is unset (`database/db.py`).

Fields used in prospecting: `id`, `name`, `state_code`, `city`, `roof_area_sqft`, `latitude`, `longitude`, `data_source`, footprint polygon flag (lineage).

## State environmental / utility context

- **Postgres:** `state_context` (`StateContextRow`).
- **Fallback:** `backend/data/state_context.csv`.

Provides **annual rainfall (inches)** and **reference water price ($/1,000 gal)** for the state. Ingest/update scripts may refresh rainfall (e.g. Open-Meteo) or manual edits—see `docs/DATABASE_SEED_DATA.md` and `backend/docs/DATA_SOURCES_WATER_PRICING.md`.

## Rainwater volume and savings

- **Rainwater:** `services/rainwater.py` — deterministic function of catchment (catalog sq ft) and state rainfall.
- **Savings:** `services/roi.py` — `(gallons / 1000) × water_price_per_1000_gal_usd`.

## Cooling tower (live CV only)

When `GET /building/{id}?live_cv=true` and `ENABLE_LIVE_CV` allows it:

1. **Imagery:** Google Earth Engine, collection `COPERNICUS/S2_SR_HARMONIZED`, median composite, date filter `2023-01-01`–`2024-12-31` (`ai/gee_imagery.py`).
2. **Vision:** Google Gemini multimodal (`ai/gemini_vision.py`), model from `GEMINI_API_KEY` / `gemini_model` in settings.

If live CV is off, coords are missing, GEE returns no thumbnail, or Gemini returns no parseable JSON, the API sets `tower_status=unavailable` and **does not** invent a tower score.

**Environment variables:** `GEE_PROJECT_ID`, `GEMINI_API_KEY`, optional `ENABLE_LIVE_CV`, `SAVE_GEE_THUMBNAILS` — see `backend/docs/API_AND_EXTERNAL_SERVICES.md`.

## ESG / sustainability

- **Current:** Not exposed as a numeric score. `esg_signal_score` is `null` and `esg_status=unavailable` until a building is linked to a company with an ingested `CompanySustainabilityProfile` (schema exists in `database/tables.py`; wiring TBD).

## Not used for GET `/buildings` headline score

- **`building_scores.final_viability_score`:** May still be populated by seed or offline jobs for analytics; **prospecting responses** compute viability in real time in `services/enrichment.py` (no DB override).

## Seed / demo tables

Tables such as `CvDetection`, `ImageryAsset`, and seed-only hash-derived fields in `seed_database.py` exist for **database demos** and **offline scoring experiments**. They are **not** the source of truth for the public prospecting enrichment path described above.
