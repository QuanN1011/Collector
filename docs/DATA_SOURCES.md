# Where data files come from

This page is the **index** for provenance of CSVs and key inputs. For ingest commands and workflows, see [`DATABASE_AND_WORKFLOW.md`](DATABASE_AND_WORKFLOW.md) and [`DATABASE_SEED_DATA.md`](DATABASE_SEED_DATA.md). For real vs synthetic and CV, see [`DATA_SOURCES_REAL_VS_GENERATED.md`](DATA_SOURCES_REAL_VS_GENERATED.md).

**Full list — database tables, APIs, formulas, and UI field mapping:** [`DATA_INVENTORY.md`](DATA_INVENTORY.md).

---

## `backend/data/state_context.csv`

| Column | Role | Typical source in this repo |
|--------|------|-----------------------------|
| `state` | USPS code (e.g. `TX`) | — |
| `rainfall_inches_annual` | Mean annual precipitation (inches) for scoring / rainwater math | **Hand-curated** in the bundled CSV, or **replaced** by [`backend/scripts/ingest_state_precip_open_meteo.py`](../backend/scripts/ingest_state_precip_open_meteo.py) (Open-Meteo / ERA5 at a state centroid—see [`state_centroids.py`](../backend/services/state_centroids.py)). |
| `water_price_per_1000_gal_usd` | State-level **USD per 1,000 gallons** for ROI and scoring | **Hand-curated** reference-style values in the bundled file. There is **no** national utility API wired in-repo. You may **merge** third-party tables (e.g. monthly bill rankings) using a **documented conversion**—see [`backend/docs/DATA_SOURCES_WATER_PRICING.md`](../backend/docs/DATA_SOURCES_WATER_PRICING.md) and [`backend/scripts/ingest_state_water_from_monthly_bill_csv.py`](../backend/scripts/ingest_state_water_from_monthly_bill_csv.py). |

**Summary:** `state_context.csv` is **not** randomly generated. It is a **maintained** state lookup table. Rainfall can be **refreshed from an API** via the precip ingest script; water price stays whatever you put in the CSV until you **replace** or **merge** it from a source you trust.

Loaded into Postgres as table **`state_context`** (see [`DATABASE_SEED_DATA.md`](DATABASE_SEED_DATA.md) §4).

---

## Other important files under `backend/data/`

| File | Purpose |
|------|---------|
| `buildings.csv` | Demo seed: synthetic / generator buildings (see `generate_building_seed_csv.py`). |
| `buildings_microsoft.csv` | After Microsoft ingest: real footprints + areas from [US Building Footprints](https://github.com/microsoft/USBuildingFootprints). |
| `companies.csv`, `company_*.csv` | Curated demo company / ESG-adjacent fixtures. |
| `water-prices-by-state-*.csv` (imports) | Optional **external** snapshots (e.g. monthly bill by state). Convert to `water_price_per_1000_gal_usd` before treating as canonical—see water pricing doc above. |

---

## API responses vs stored scores

The FastAPI layer ([`backend/services/enrichment.py`](../backend/services/enrichment.py)) computes **`viability_breakdown`** with [`services/scoring.compute_viability`](../backend/services/scoring.py) (rainfall, water price, cooling tower, ESG mock).

- When **`live_cv=false`** (Satellite + AI refresh **off**), if the database has a persisted **`building_scores.final_viability_score`**, the API **may use that value as the headline `viability_score`** so the number matches seeded demo rollups (see [`DATABASE_SEED_DATA.md`](DATABASE_SEED_DATA.md) §5).
- When **`live_cv=true`**, the headline is the **computed** blend from the current breakdown (CV or mock physical), **without** that stored override—so the **top number can change** while **rainfall, water price, savings proxy, and ESG** stay the same (same state + same building id).

**Why it can look like “only viability changes”**

- **Annual savings**, **rainfall**, **water price** use **catalog roof area** and **state_context**—they do not change when you only toggle live CV if the building and state context are unchanged.
- **ESG (demo)** is a **deterministic hash** of `building_id`—unchanged.
- **Cooling tower** *subscore* in the breakdown only moves if **detected** / **confidence** change (e.g. real Gemini vs mock, or different inference). If mock and live agree, that **bar stays flat** while the **headline** still moves because of **stored vs computed** score logic or scoring weight updates.

This is **expected behavior**, not a sign that other fields are “wrong.”

---

## Related documents

| Doc | Contents |
|-----|----------|
| [`DATA_INVENTORY.md`](DATA_INVENTORY.md) | **Complete inventory**: every major table, runtime API, `BuildingEnriched` field sources, frontend mapping. |
| [`DATA_SOURCES_REAL_VS_GENERATED.md`](DATA_SOURCES_REAL_VS_GENERATED.md) | APIs vs synthetic, script index, CV scope. |
| [`DATABASE_SEED_DATA.md`](DATABASE_SEED_DATA.md) | Full CSV → table mapping, seed pipeline. |
| [`backend/docs/DATA_SOURCES_WATER_PRICING.md`](../backend/docs/DATA_SOURCES_WATER_PRICING.md) | Monthly bill → `$/1,000 gal` conversion notes. |
| [`backend/docs/VISION_PIPELINE.md`](../backend/docs/VISION_PIPELINE.md) | `live_cv`, Earth Engine, Gemini. |
