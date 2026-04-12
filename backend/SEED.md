# RainUSE Nexus — database seeding (MVP)

This note describes what the seed pipeline loads, which sources it approximates, and how to run it locally.

For **full provenance** (required inputs, inferred fields, and cited external source categories), see **[`docs/DATABASE_SEED_DATA.md`](../docs/DATABASE_SEED_DATA.md)**.

To **import real public datasets** (Microsoft footprints, Open-Meteo precipitation, optional SEC company list) instead of the demo CSVs, see **[`docs/DATA_SOURCES_REAL_VS_GENERATED.md`](../docs/DATA_SOURCES_REAL_VS_GENERATED.md)** (includes whether you need computer vision: **you don’t** for those sources). Detailed lineage: **§2** in [`docs/DATABASE_SEED_DATA.md`](../docs/DATABASE_SEED_DATA.md). Commands: `scripts/ingest_real_data.py`, then `seed_database.py --buildings-csv … --state-context-csv …`.

## What gets populated

Running `scripts/seed_database.py` (or `scripts/populate_database.py`) applies Alembic migrations, then fills:

| Area | Source in repo |
| --- | --- |
| `state_context` | `data/state_context.csv` (state-level rainfall inches/year and water \$/1,000 gal) |
| `companies`, `company_sustainability_profiles`, `company_documents` | `data/companies.csv`, `company_sustainability_profiles.csv`, `company_documents.csv` |
| `buildings` | `data/buildings.csv` (+ synthetic **MULTIPOLYGON** footprints from roof area and lat/lon) |
| `imagery_assets` | Generated metadata (Sentinel-2 / Landsat–style labels, GEE-style placeholder URIs) |
| `cv_detections` | Deterministic mock CV (`ai/cooling_tower_detection`) plus roof/obstruction rows |
| `physical_features`, `water_yield_estimates`, `utility_profiles`, `policy_drivers`, `building_scores` | Derived in `seed_database.py` using `services/seed_scoring.py` |

## What is “real” vs inferred for the MVP

- **Footprints / roof area**: Building rows are generated for pilot metros (`scripts/generate_building_seed_csv.py`). They stand in for commercial/industrial candidates. Polygons are **axis-aligned squares** from roof area—not Microsoft US Building Footprints (that dataset is not vendored here). Regenerate the CSV anytime with the generator script.
- **Rainfall & state water price**: Curated public-style averages (PRISM-like rainfall; water price in the ballpark of state summaries / open references). Use `data/imports/state_context_overrides.csv` (see `populate_database.py`) to override specific states without editing the full CSV.
- **City utility economics**: Dallas, Austin, Houston, Mesquite, Phoenix, Tucson, and Philadelphia use **hand-tuned** water/wastewater/stormwater placeholders in `services/seed_scoring.py`. Other cities use the state average with a simple wastewater multiplier.
- **Policy rows**: Representative TCEQ / ADWR / PADEP / municipal **themes** for TX, AZ, and PA; illustrative dollar amounts where helpful. Treat as demo signals, not legal advice.
- **Companies / ESG**: A small curated set of recognizable tickers with plausible flags and SEC URL patterns—**not** live SEC pulls.
- **Imagery**: Metadata only; binaries are not stored. URLs are non-resolving `storage.example.invalid` paths for demos.

## Harvest and scoring math

- **Rainwater volume**: Starts from `services/rainwater.annual_rainwater_gallons` (0.623 factor). The seed applies **runoff** 0.85 and **system efficiency** 90% in `water_yield_estimates` (see `services/seed_scoring.effective_annual_harvest_gallons`).
- **Pillar scores (0–100)** and **final viability** weights live in `services/seed_scoring.py`. The API’s `/buildings` and `/top-prospects` responses still use `services/scoring.compute_viability` for the breakdown, but **override the headline score** with `building_scores.final_viability_score` when present (`database.db.get_stored_final_viability_standalone`).

## How to run

1. Start PostGIS: from the repo root, `docker compose up -d`.
2. Export `DATABASE_URL`, e.g.  
   `export DATABASE_URL=postgresql+psycopg://rainuse:rainuse@localhost:5432/rainuse`
3. Install backend dependencies (prefer a venv):  
   `cd backend && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt`
4. Seed:  
   `cd backend && .venv/bin/python scripts/seed_database.py`  
   Or: `.venv/bin/python scripts/populate_database.py` (optional state overrides file).

## Regenerating building rows

```bash
cd backend
python scripts/generate_building_seed_csv.py   # rewrites data/buildings.csv
python scripts/seed_database.py
```

The generator is deterministic (`random.Random(42)`) for reproducible footprints and sizes.
