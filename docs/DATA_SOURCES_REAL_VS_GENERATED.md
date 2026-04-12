# Data sources: real vs generated, and whether you need computer vision

This document is a **reference** for what RainUSE ingests from **public APIs and downloads**, what stays **synthetic or derived in code**, and how that relates to **computer vision (CV)**. For commands and workflow, see [`DATABASE_AND_WORKFLOW.md`](DATABASE_AND_WORKFLOW.md). For deeper fixture lineage, see [`DATABASE_SEED_DATA.md`](DATABASE_SEED_DATA.md).

---

## 1. Do you need computer vision to avoid “fake” data?

**No—not in this repository as shipped.**

- **Building footprints:** If you use **Microsoft US Building Footprints**, those polygons were produced **upstream** by Microsoft’s models on satellite/aerial imagery. **You download GeoJSON** and ingest them—you do **not** run a vision model in this app to get those shapes.
- **Rainfall:** **Open-Meteo** (ERA5-based archive) is a **HTTP API**—no CV.
- **Companies:** **SEC** publishes `company_tickers.json`—no CV.

What *is* CV-related **inside this repo** today:

- [`backend/ai/cooling_tower_detection.py`](../backend/ai/cooling_tower_detection.py) is a **deterministic stub** (hash-based), **not** inference on images.
- The seed pipeline creates **`cv_detections`** rows and **`imagery_assets`** metadata for demos **without** processing real image rasters.

So: **real geographic and climate data do not require you to implement CV here.** Optional future work would be to add a **real** CV pipeline (load tiles → run a model → write `cv_detections`). That is separate from “real footprints from Microsoft” or “real rainfall from an API.”

---

## 2. What is **not** generated (ingested from external sources)

| Data | How it enters the project | Primary source |
|------|---------------------------|----------------|
| Building polygons & area | Download + stream GeoJSON zip, write CSV with WKT | [Microsoft US Building Footprints](https://github.com/microsoft/USBuildingFootprints) (ODbL); CDN URLs in that repo’s README |
| Mean annual rainfall (inches) | HTTP API, aggregate daily → annual mean by state centroid | [Open-Meteo Archive API](https://open-meteo.com) (ERA5-based); centroids in [`backend/services/state_centroids.py`](../backend/services/state_centroids.py) |
| Company ticker / CIK / name | HTTP GET JSON | [SEC `company_tickers.json`](https://www.sec.gov/files/company_tickers.json) |
| State water price (when using precip ingest) | **Preserved** from your existing CSV during rainfall refresh—not fetched from a national API in-repo | Your [`state_context.csv`](../backend/data/state_context.csv) (you replace with trusted rate data if needed) |

**Scripts (real-data path):**

| Piece | Script | Notes |
|-------|--------|--------|
| **1. Microsoft footprints (real geometries)** | [`backend/scripts/ingest_ms_buildings.py`](../backend/scripts/ingest_ms_buildings.py) | Downloads official GeoJSON zip from Microsoft’s CDN; streams with **ijson**; area in sq ft via **Shapely + Pyproj**; writes **`footprint_wkt`** + centroid lat/lon. Helpers: [`backend/services/footprint_geometry.py`](../backend/services/footprint_geometry.py). Cache: `backend/data/cache/ms_footprints/` (gitignored). Large states (e.g. Texas ~2.8 GiB unzipped) need disk and time. |
| **2. State rainfall (API, not hand-curated numbers)** | [`backend/scripts/ingest_state_precip_open_meteo.py`](../backend/scripts/ingest_state_precip_open_meteo.py) | Calls Open-Meteo Archive; rewrites **`rainfall_inches_annual`**; keeps **`water_price_per_1000_gal_usd`** from `--merge-water-from` (typically your current `state_context.csv`). |
| **3. SEC company list** | [`backend/scripts/ingest_sec_company_tickers.py`](../backend/scripts/ingest_sec_company_tickers.py) | No API key; descriptive User-Agent; SEC may **rate-limit**—retry or off-peak. Output e.g. `companies_from_sec.csv`. |
| **4. Orchestrator** | [`backend/scripts/ingest_real_data.py`](../backend/scripts/ingest_real_data.py) | Subcommands: `footprints`, `precip`, `all`. |
| **5. Seed accepts real building WKT** | [`backend/scripts/seed_database.py`](../backend/scripts/seed_database.py) | Flags: `--buildings-csv`, `--state-context-csv`, optional company CSVs. If a row has **`footprint_wkt`**, that geometry is stored; otherwise the seed uses a **synthetic square** footprint. |

**Dependencies** (extra vs base backend): `ijson`, `shapely`, `pyproj` in [`backend/requirements.txt`](../backend/requirements.txt).

---

## 3. What **is** still generated or derived in code (MVP defaults)

These are **not** replaced by the Microsoft/Open-Meteo/SEC ingest unless you build additional pipelines:

| Area | What happens |
|------|----------------|
| **`imagery_assets`** | Metadata rows (provider labels, placeholder URLs, bounding boxes)—**no image binaries** stored. |
| **`cv_detections`** | Mock / seeded detections; [`cooling_tower_detection`](../backend/ai/cooling_tower_detection.py) is **not** real CV. |
| **`physical_features`**, **`water_yield_estimates`**, **`utility_profiles`**, **`policy_drivers`**, **`building_scores`** | Computed from formulas and templates in seed + [`services/seed_scoring.py`](../backend/services/seed_scoring.py). |
| **Demo `buildings.csv`** | [`generate_building_seed_csv.py`](../backend/scripts/generate_building_seed_csv.py) produces **synthetic** candidate rows if you do not use Microsoft ingest. |

**Not “live API” everywhere today**

- **State water / wastewater retail $:** No single national API wired in-repo; precip ingest **preserves** existing water price column until you replace it from rate studies or portals you trust.
- **Utility city overrides** (Dallas, Phoenix, etc.) are **hand-tuned placeholders** in code for scoring demos.
- **Policy rows** are **illustrative** themes, not a legal database.
- **SEC:** Rate limits may return errors—retry later.

---

## 4. Example: real footprints + API rainfall, then seed

Prerequisites: Docker Postgres + PostGIS, `DATABASE_URL`, Python venv with `pip install -r requirements.txt`.

```bash
cd backend

# Footprints + rainfall (keeps water $ from current state_context.csv)
python scripts/ingest_real_data.py all --states Texas Arizona Pennsylvania \
  --min-sqft 100000 --max-per-state 150

python scripts/seed_database.py \
  --buildings-csv data/buildings_microsoft.csv \
  --state-context-csv data/state_context.csv
```

---

## 5. Related docs

- [`DATA_SOURCES.md`](DATA_SOURCES.md) — **Index** of where bundled CSVs (especially `state_context.csv`) come from, and why the viability headline can change without other KPIs moving.  
- [`DATABASE_SEED_DATA.md`](DATABASE_SEED_DATA.md) — Full provenance, CSV → table mapping, API vs synthetic overview.  
- [`backend/SEED.md`](../backend/SEED.md) — Short runbook.  
- [`DATABASE_AND_WORKFLOW.md`](DATABASE_AND_WORKFLOW.md) — Docker, migrations, populate commands.
