# Database seed data: sources, inferences, and required inputs

This document records **where MVP fixture data comes from**, **what is inferred or synthetic**, and **what you need** to run the population pipeline. Operational commands remain in [`DATABASE_AND_WORKFLOW.md`](DATABASE_AND_WORKFLOW.md); the short runbook also lives in [`backend/SEED.md`](../backend/SEED.md).

**Quick reference (real vs generated, CV vs APIs):** [`DATA_SOURCES_REAL_VS_GENERATED.md`](DATA_SOURCES_REAL_VS_GENERATED.md).

**Index of file provenance (including `state_context.csv`):** [`DATA_SOURCES.md`](DATA_SOURCES.md).

**Full data inventory (DB + APIs + UI):** [`DATA_INVENTORY.md`](DATA_INVENTORY.md).

---

## 1. What you need to populate the database

| Requirement | Purpose |
|-------------|---------|
| **PostgreSQL + PostGIS** | Matches the schema (`Geometry` columns, `CREATE EXTENSION postgis`). Local default: `docker compose up -d` from the repo root. |
| **`DATABASE_URL`** | Set in the shell or `backend/.env`, e.g. `postgresql+psycopg://rainuse:rainuse@localhost:5432/rainuse`. See [`backend/database/config.py`](../backend/database/config.py). |
| **Python deps** | `backend/requirements.txt` installed in a venv (SQLAlchemy, GeoAlchemy2, Alembic, psycopg, etc.). |
| **Bundled CSVs** | Under `backend/data/` (see §3). Optional: `backend/data/imports/state_context_overrides.csv` when using `scripts/populate_database.py`. |
| **Scripts** | `scripts/seed_database.py` (full seed) or `scripts/populate_database.py` (seed + optional state overrides). Optional **real-data** ingest scripts (see §2). |

Migrations run via `init_db()` inside the seed entrypoints (Alembic `upgrade head`). The schema is defined in [`backend/database/tables.py`](../backend/database/tables.py) and created by the initial migration.

---

## 2. Real data ingestion (optional, network required)

These scripts **download or call public services** and write CSVs you can pass into `seed_database.py`. They replace the synthetic building generator and/or hand-curated rainfall for `state_context` when you choose to run them.

| Script | What it fetches | Output / notes |
|--------|-----------------|----------------|
| [`backend/scripts/ingest_ms_buildings.py`](../backend/scripts/ingest_ms_buildings.py) | [Microsoft US Building Footprints](https://github.com/microsoft/USBuildingFootprints) GeoJSON (ODbL) from Microsoft’s published CDN zips | `data/buildings_microsoft.csv` with **`footprint_wkt`** (true footprints), `roof_area_sqft` from geodesic area, centroid lat/lon. **Large downloads** (e.g. Texas unzipped ~2.8 GiB); zips are cached under `data/cache/ms_footprints/`. Streams features with **ijson** so RAM stays bounded. |
| [`backend/scripts/ingest_state_precip_open_meteo.py`](../backend/scripts/ingest_state_precip_open_meteo.py) | [Open-Meteo Archive API](https://open-meteo.com) (ERA5-based daily precipitation at each state’s approximate centroid; see [`services/state_centroids.py`](../backend/services/state_centroids.py)) | Overwrites **`rainfall_inches_annual`** in `state_context.csv` (or a path you pass). **Preserves** existing **`water_price_per_1000_gal_usd`** from your current CSV (`--merge-water-from`). Not identical to NOAA Climate Normals station aggregates—document attribution for demos. |
| [`backend/scripts/ingest_sec_company_tickers.py`](../backend/scripts/ingest_sec_company_tickers.py) | [SEC `company_tickers.json`](https://www.sec.gov/files/company_tickers.json) | `companies_from_sec.csv` with real **CIK**, **ticker**, **name**. SEC may **rate-limit**; use a descriptive `User-Agent` (set in script). Pair with empty sustainability/doc CSVs or curated ESG rows. |
| [`backend/scripts/ingest_real_data.py`](../backend/scripts/ingest_real_data.py) | Orchestrator (`footprints`, `precip`, or `all` subcommands) | Chains the above in order. |

**Typical pipeline (real buildings + API rainfall, keep bundled water prices until you replace them):**

```bash
cd backend
python scripts/ingest_real_data.py all --states Texas Arizona Pennsylvania --min-sqft 100000 --max-per-state 150
python scripts/seed_database.py --buildings-csv data/buildings_microsoft.csv --state-context-csv data/state_context.csv
```

**Seed CLI flags** (all optional paths): `--state-context-csv`, `--buildings-csv`, `--companies-csv`, `--company-sustainability-csv`, `--company-documents-csv`.

---

## 3. Demo / synthetic path vs real-ingest path (summary)

| Domain | Demo default (no ingest) | With ingest scripts |
|--------|--------------------------|----------------------|
| Building footprints | `generate_building_seed_csv.py` → `buildings.csv`; square **synthetic** geometry in `seed_database.py` | Microsoft CDN → `buildings_microsoft.csv` + **`footprint_wkt`**; **real** CV-derived footprints (ODbL). |
| State rainfall | Curated `state_context.csv` | Open-Meteo API → updated **rainfall** column (ERA5 reanalysis at centroid). |
| State water price | Curated `state_context.csv` | **Unchanged** unless you replace the column from an authoritative rate study (no single federal API in repo). |
| Companies | Curated CSVs | Optional SEC `company_tickers.json` → `companies_from_sec.csv`. |
| Imagery, CV rows, scores | Still **derived** in `seed_database.py` (metadata + mock CV + formulas) | Same unless you add new pipelines. |

---

## 4. Files that directly feed Postgres (CSV → tables)

| File | Tables | Notes |
|------|--------|--------|
| `backend/data/state_context.csv` | `state_context` | One row per state: annual rainfall (inches) and water price (`$/1,000 gal`). |
| `backend/data/companies.csv` | `companies` | Curated demo companies. |
| `backend/data/company_sustainability_profiles.csv` | `company_sustainability_profiles` | ESG-related flags and scores (many fields nullable). |
| `backend/data/company_documents.csv` | `company_documents` | Lightweight filing/document metadata and short excerpts; no large blobs. |
| `backend/data/buildings.csv` | `buildings` | Demo generator output: IDs, names, state, city, `roof_area_sqft`, lat/lon, optional `company_id`, `building_type`, `land_use_type`. |
| `backend/data/buildings_microsoft.csv` (after ingest) | `buildings` | Adds **`footprint_wkt`** (MULTIPOLYGON WKT). If present, `seed_database.py` loads that geometry instead of a synthetic square. |

Optional merge for **state-level** overrides without editing the full state file: `backend/data/imports/state_context_overrides.csv` (see `populate_database.py`).

---

## 5. What is computed or inferred in code (not copied from an external API)

These are **derived during seeding** in `seed_database.py` + `services/seed_scoring.py`:

| Output | Inference summary |
|--------|-------------------|
| `buildings.footprint_geom` | If **`footprint_wkt`** is absent in the buildings CSV: **MULTIPOLYGON** square from `roof_area_sqft` and centroid (lat/lon). If **`footprint_wkt`** is present (Microsoft ingest): geometry comes from that column. |
| `imagery_assets` | Synthetic metadata and QA-style scores tied to each building. |
| `cv_detections` | Mock / deterministic confidences; not from real model inference on stored rasters. |
| `physical_features` | Catchment areas, obstruction ratio, tower presence/count from mock tower detection + heuristics; `physical_fit_score` from pillar helpers. |
| `water_yield_estimates` | Uses `services/rainwater` (0.623 in³→gal relationship), then **runoff coefficient** (0.85) and **system efficiency** (90%) in seed; monthly JSON is a **seasonal shape** for demos. |
| `utility_profiles` | Resolved from state + city overrides or state defaults; `utility_cost_pressure_score` from pillar logic. |
| `policy_drivers` | Copied from per-state **templates** per building (repeated policy themes across buildings in the same state). |
| `building_scores` | All pillar scores 0–100 and **weighted** `final_viability_score` (`FINAL_WEIGHTS` in `seed_scoring.py`); `opportunity_tier` from thresholds. |

The API layer ([`backend/services/enrichment.py`](../backend/services/enrichment.py)) computes a **viability breakdown** with [`services/scoring.compute_viability`](../backend/services/scoring.py). It **overrides the headline** with persisted `building_scores.final_viability_score` when present **and** the request is not **`live_cv=true`**—so default detail matches seeded rollups; Satellite + AI detail uses the computed headline. See [`DATA_SOURCES.md`](DATA_SOURCES.md).

---

## 6. Pilot geography and building mix

- **Generator** (`generate_building_seed_csv.py`) emphasizes **Texas, Arizona, and Pennsylvania** metros (deterministic RNG seed for reproducibility).
- Roof areas are mostly in a **large commercial / industrial** band (~100k+ sq ft), with a small number of **near-threshold** rows for UI edge cases.
- **Company linkage** is optional per row (`company_id`); unlinked buildings still score using corporate pillar defaults when no company row applies.

---

## 7. When you change data assumptions

1. Update the relevant **CSV** or **`seed_scoring.py`** constants (utilities, policy text, climate stress proxies, scoring weights).  
2. Re-run **`python scripts/seed_database.py`** (or `populate_database.py`) against a database you are allowed to wipe or that uses the script’s delete-and-reinsert behavior.  
3. If you add **real** ingested datasets (footprints, PRISM rasters, rate tables), document the **license**, **retrieval date**, and **processing script** here or in a short companion note so the team can reproduce imports.

---

## Related documents

- [`DATA_SOURCES_REAL_VS_GENERATED.md`](DATA_SOURCES_REAL_VS_GENERATED.md) — real ingest vs generated, CV vs APIs, script index.  
- [`DATABASE_AND_WORKFLOW.md`](DATABASE_AND_WORKFLOW.md) — commands, migrations, pull checklist.  
- [`DATABASE_DECISIONS.md`](DATABASE_DECISIONS.md) — schema and product decisions.  
- [`backend/SEED.md`](../backend/SEED.md) — concise seed runbook and regeneration of `buildings.csv`.
