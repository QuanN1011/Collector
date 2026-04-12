# Data inventory: database, APIs, and what the UI shows

This document lists **what the program stores**, **where it comes from** (imports, API calls, or formulas), and **how each value on the prospecting / water economics UI is computed**. For file-level notes on `state_context.csv`, see [`DATA_SOURCES.md`](DATA_SOURCES.md).

---

## 1. Data persisted in PostgreSQL (or CSV fallback without Docker)

When `DATABASE_URL` is set, Alembic migrations create tables; **`seed_database.py`** / **`populate_database.py`** load CSVs and compute derived rows. Without Postgres, **`database/db.py`** reads **`backend/data/state_context.csv`** and **`backend/data/buildings.csv`** directly.

| Table / data | What it holds | Typical source |
|--------------|---------------|----------------|
| **`state_context`** | Per-state `rainfall_inches_annual`, `water_price_per_1000_gal_usd` | **Imported** from [`backend/data/state_context.csv`](../backend/data/state_context.csv). Rainfall may be **refreshed** via HTTP [**Open-Meteo Archive API**](https://open-meteo.com) ([`ingest_state_precip_open_meteo.py`](../backend/scripts/ingest_state_precip_open_meteo.py)). Water price is **not** fetched by that script; you **merge** from your own tables (e.g. monthly-bill CSV converted with [`ingest_state_water_from_monthly_bill_csv.py`](../backend/scripts/ingest_state_water_from_monthly_bill_csv.py)). See [`backend/docs/DATA_SOURCES_WATER_PRICING.md`](../backend/docs/DATA_SOURCES_WATER_PRICING.md). |
| **`buildings`** | Site id, name, state, city, `roof_area_sqft`, lat/lon, optional `footprint_geom`, `data_source` | **Imported** from CSV (`buildings.csv` from [`generate_building_seed_csv.py`](../backend/scripts/generate_building_seed_csv.py), or **`buildings_microsoft.csv`** after downloading [**Microsoft US Building Footprints**](https://github.com/microsoft/USBuildingFootprints) GeoJSON zips via [`ingest_ms_buildings.py`](../backend/scripts/ingest_ms_buildings.py)). **No live API** during normal HTTP requests. |
| **`companies`** | Demo company rows | **Imported** [`backend/data/companies.csv`](../backend/data/companies.csv) (curated). Optional real tickers: [**SEC** `company_tickers.json**](https://www.sec.gov/files/company_tickers.json) via [`ingest_sec_company_tickers.py`](../backend/scripts/ingest_sec_company_tickers.py). |
| **`company_sustainability_profiles`**, **`company_documents`** | ESG-ish demo metadata | **Imported** bundled CSVs under `backend/data/`. |
| **`building_scores`** | Pillar scores + **`final_viability_score`** | **Computed at seed time** in [`services/seed_scoring.py`](../backend/services/seed_scoring.py), not copied from an external API. Used by API to **override headline viability** when `live_cv=false` ([`enrichment.py`](../backend/services/enrichment.py)). |
| **`physical_features`**, **`water_yield_estimates`**, **`utility_profiles`**, **`policy_drivers`** | Seed-era rollups for demos | **Computed** during seed from formulas + state/city overrides in code; **not** the same code path as the live **`BuildingEnriched`** HTTP response (which recomputes in `enrichment.py`). |
| **`imagery_assets`**, **`cv_detections`** | Metadata / mock detection rows for demos | **Inserted by seed**; not populated by real CV inference on stored rasters in the default pipeline. |
| **`api_keys`** | Issued API keys for `X-Api-Key` | **Written** when a verified user calls **`POST /api/keys/issue`**; Auth0 **JWT** verified against Auth0 (**HTTPS JWKS**), not a third-party “data” API for buildings. |

---

## 2. External services used at runtime (not bulk-imported into all tables)

| Service | When | Purpose |
|---------|------|---------|
| **Google Earth Engine + Gemini** (optional) | `GET /building/{id}?live_cv=true` when [`live_cv_enabled()`](../backend/services/settings.py) is true | Fetch Sentinel-2 thumbnail, run vision on **cooling tower** cues ([`physical_pipeline.py`](../backend/ai/physical_pipeline.py)). **Not** used for list endpoints. |
| **Auth0** | Login in browser; **`POST /api/keys/issue`** | OIDC / JWT; no building data. |

There is **no** runtime HTTP call to Open-Meteo or Microsoft when you simply load the prospecting page—those are **offline ingest scripts** unless you run them yourself.

---

## 3. Prospecting API payload (`BuildingEnriched`) — computed per request

The FastAPI routes **`/states`**, **`/buildings`**, **`/building/{id}`**, **`/top-prospects`** return enriched buildings from [`enrich_building()`](../backend/services/enrichment.py). Sources below.

| Field | Source of truth |
|-------|-----------------|
| **`id`**, **`name`**, **`state`**, **`city`** | **Postgres `buildings`** or **CSV** row. |
| **`roof_area_sqft`**, **`latitude`**, **`longitude`** | Same building row (catalog / ingest). |
| **`rainfall_inches_annual`**, **`water_price_per_1000_gal_usd`** | **`state_context`** for that building’s state (from DB or `state_context.csv`). |
| **`rainwater_potential_gallons`** | **Formula** [`annual_rainwater_gallons`](../backend/services/rainwater.py): roof catchment (from physical analysis, usually = catalog sq ft) × state rainfall × **0.623**. |
| **`annual_water_savings`** | **Formula** [`annual_water_savings_usd`](../backend/services/roi.py): (gallons / 1000) × state **`water_price_per_1000_gal_usd`**. |
| **`viability_score`** | **`compute_viability()`** in [`scoring.py`](../backend/services/scoring.py) (weighted blend of rainfall, water price, cooling tower subscore, mock ESG). If DB has **`building_scores.final_viability_score`** and **`live_cv` is false**, headline is **replaced** by that stored value. |
| **`viability_breakdown`** | Same **`compute_viability`** pillar subscores (0–100 scale each). |
| **`cooling_tower_detected`**, **`cooling_tower_confidence`** | **`get_physical_analysis()`**: either **mock** (hash of building id) or **Gemini + GEE** when live CV runs. |
| **`esg_signal_score`** | **`mock_esg_subscore(building_id)`** — **deterministic placeholder**, not external ESG data. |
| **`physical_analysis`** | Roof catchment from **catalog**; tower from **mock or Gemini**; `vision_backend` / `imagery_source` indicate mode. |
| **`data_notes`** | Static explanatory string on the model. |

**List routes** (`/buildings`, `/top-prospects`) use **`live_cv=false`**. **Detail** (`/building/{id}`) passes the **`live_cv`** query param from the **Satellite + AI refresh** checkbox.

---

## 4. Frontend: which API fields drive each area

### Prospecting section ([`ProspectingSection.tsx`](../collector/app/Components/ProspectingSection.tsx) + [`BuildingInsights.tsx`](../collector/app/Components/BuildingInsights.tsx))

| UI element | Backing data |
|------------|----------------|
| State / building pickers | **`/states`**, **`/buildings?state=`** |
| **Viability score** | `building.viability_score` |
| **Annual savings proxy** | `building.annual_water_savings` |
| **ESG signal (demo)** | `building.esg_signal_score` |
| **Annual rainfall (state)** | `building.rainfall_inches_annual` |
| **Viability breakdown bars** | `building.viability_breakdown` keys (`rainfall`, `water_price`, `cooling_tower`, `esg_mock`) |
| **Catchment sq ft, large roof, roof confidence, provenance** | `building.physical_analysis` |
| **Cooling tower detected + %** | `physical_analysis` + top-level `cooling_tower_*` (aligned with enrichment) |
| **Analysis mode** | `physical_analysis.vision_backend` / `imagery_source` |

### Water economics section ([`WaterEconomicsSection.tsx`](../collector/app/Components/WaterEconomicsSection.tsx))

| UI element | Backing data |
|------------|----------------|
| State, building name | Same `building` object |
| **Reference water rate** | `building.water_price_per_1000_gal_usd` |
| **Annual rainfall** | `building.rainfall_inches_annual` |
| **Rainwater potential / savings** (and slider stress) | `building.rainwater_potential_gallons` + rate math **in the browser** (same ROI idea as backend) |
| **Implied monthly bill** (illustrative) | Derived in **frontend** from `water_price_per_1000_gal_usd` × **12,000 gal/mo** assumption (see comment in file) |

### Other UI

| Area | Source |
|------|--------|
| **CONNECTED / health** | **`GET /health`** (no DB required for basic check). |
| **Auth** | **Auth0** SPA SDK in the browser. |

---

## 5. Related documents

| Document | Contents |
|----------|----------|
| [`DATA_SOURCES.md`](DATA_SOURCES.md) | Index + `state_context.csv` + viability headline behavior. |
| [`DATA_SOURCES_REAL_VS_GENERATED.md`](DATA_SOURCES_REAL_VS_GENERATED.md) | Real ingest vs synthetic, script list. |
| [`DATABASE_SEED_DATA.md`](DATABASE_SEED_DATA.md) | CSV → table mapping, seed pipeline. |
| [`DATABASE_AND_WORKFLOW.md`](DATABASE_AND_WORKFLOW.md) | Docker, migrations, commands. |
