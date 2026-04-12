# Computer vision work — implementation summary

This document is a **checkpoint handoff**: what the RainUSE Nexus backend does today for **physical / satellite / “CV”** signals, **which files implement it**, and **what is intentionally out of scope** so far.

**Deeper behavior (mock vs live, caching, troubleshooting):** [VISION_PIPELINE.md](./VISION_PIPELINE.md)  
**REST API, env vars, smoke test:** [API_AND_EXTERNAL_SERVICES.md](./API_AND_EXTERNAL_SERVICES.md)

---

## 1. What “computer vision” means here

The product does **not** train a custom detector yet. The live path is:

**Earth Engine → Sentinel-2 RGB thumbnail (PNG bytes) → Gemini multimodal (image + text prompt) → parsed JSON** (`cooling_tower_likely`, `confidence`).

That is **remote sensing + a vision-language model**, not classical training of convolutional weights on your own labels.

Separately, **roof area** and the **≥100,000 sq ft “large roof”** flag come from the **building catalog** (`roof_area_sqft` in Postgres/CSV), not from segmenting the satellite image. **`roof_confidence`** and **`roof_catchment_provenance`** describe **catalog lineage** (e.g. Microsoft footprints vs synthetic seed). See [ROOF_CATCHMENT_LINEAGE.md](./ROOF_CATCHMENT_LINEAGE.md).

---

## 2. End-to-end flow (API → AI)

1. **Client** calls **`GET /building/{building_id}`** with optional **`?live_cv=true`** (`routes/buildings.py`).
2. **`enrich_building(..., live_cv=...)`** (`services/enrichment.py`) loads state context and calls **`get_physical_analysis(record, force_live=live_cv)`**.
3. **`get_physical_analysis`** (`ai/physical_pipeline.py`):
   - If **`live_cv` is false** or **`ENABLE_LIVE_CV`** is not enabled → **`_mock_physical`**: no GEE, no Gemini; cooling signal from a **deterministic function of `building_id`** (`_mock_tower`).
   - If live is allowed → **`_live_physical`**:
     - Requires **`latitude` / `longitude`** on the building row.
     - **`fetch_sentinel2_thumb_png`** (`ai/gee_imagery.py`) builds a **cloud-screened median composite** from **`COPERNICUS/S2_SR_HARMONIZED`**, exports a square **PNG** via **`getThumbURL`**, downloads with **httpx**.
     - Optionally writes the same PNG to **`backend/debug_gee_thumbnails/`** when **`SAVE_GEE_THUMBNAILS=true`** (see `services/settings.py`).
     - **`analyze_cooling_tower_from_image`** (`ai/gemini_vision.py`) sends **prompt + PNG** to **Gemini** (`google-genai`); parses JSON from the reply.
     - On GEE or Gemini failure, falls back to **mock** tower values.
   - Live results are **cached in memory per `building_id`** for the process lifetime.
4. **Enrichment** merges **`physical_analysis`** (catchment, `large_roof`, tower bool/confidence, `imagery_source`, `vision_backend`) into **`BuildingEnriched`** and feeds **viability scoring** (`services/scoring.py`).

**List endpoints** (`GET /buildings`, `GET /top-prospects`) always use **`live_cv=False`** so lists stay fast.

---

## 3. Files that implement or touch the CV story

| Path | Role |
|------|------|
| **`routes/buildings.py`** | Exposes **`live_cv`** on **`GET /building/{id}`** only. |
| **`services/enrichment.py`** | Calls **`get_physical_analysis`**; passes tower fields into ROI/viability; returns **`physical_analysis`** on the API model. |
| **`ai/physical_pipeline.py`** | **Orchestration**: mock vs live, GEE fetch, optional debug PNG save, Gemini call, cache, exception fallback. |
| **`ai/gee_imagery.py`** | Earth Engine init, Sentinel-2 collection filters, composite, **`getThumbURL`**, HTTP download. Tunables: **`GEE_BUFFER_METERS`**, **`GEE_THUMB_SIZE`**. |
| **`ai/gemini_vision.py`** | Gemini client, fixed prompt, **`Part.from_bytes`** for PNG, JSON extraction and clamping. Model from **`GEMINI_MODEL`**. |
| **`ai/cooling_tower_detection.py`** | **`detect_cooling_tower(building_id)`** — same deterministic mock as seed data; **not** the live GEE+Gemini path. |
| **`services/settings.py`** | **`ENABLE_LIVE_CV`**, **`GEE_PROJECT_ID`**, **`GEMINI_API_KEY`**, **`GEMINI_MODEL`**, GEE thumb/buffer, **`SAVE_GEE_THUMBNAILS`**. |
| **`models/building.py`** | **`PhysicalAnalysis`**, **`BuildingEnriched`** — schema for API including **`vision_backend`** (`mock` \| `gemini_vision`). |
| **`scripts/smoke_test.py`** | Asserts **mock** vision on default run; **`RUN_LIVE_CV=1`** optionally exercises **`?live_cv=true`**. |
| **`scripts/seed_database.py`** | Uses **`detect_cooling_tower`** to populate deterministic **CV-related seed rows** in Postgres (not live inference). |
| **`backend/debug_gee_thumbnails/README.md`** | Where debug PNGs are written when enabled. |

---

## 4. What this implementation demonstrates (learning / demo value)

- **Earth Engine as imagery factory**: collection → temporal/cloud filters → median RGB → exportable thumbnail.
- **Multimodal API integration**: bytes-in, structured JSON-out, with **regex + `json.loads`** parsing.
- **Product wiring**: feature flag (**`ENABLE_LIVE_CV`**), **opt-in query param** (`live_cv`), **in-process cache**, **graceful degradation** to mock.
- **Observability for tuning**: optional **on-disk PNG** identical to what Gemini receives (`SAVE_GEE_THUMBNAILS`).
- **Honest limits**: Sentinel-2 **~10 m** pixels limit detail on rooftop mechanical equipment; **Gemini** is a **weak, interpretive** signal, not survey-grade truth.

---

## 5. Not implemented yet (natural next steps to “maximize” CV)

These are **intentional gaps** for a later iteration:

| Area | Status |
|------|--------|
| **Second imagery source** (e.g. NAIP, aerial, commercial) | Not in code; still **S2-only** in `gee_imagery.py`. |
| **Roof polygon / sq ft from pixels** | Not implemented; catchment remains **catalog `roof_area_sqft`**. |
| **Labeled evaluation set** | No repo-wide benchmark; no precision/recall script. |
| **Prompt/schema iteration tied to metrics** | Single static prompt in `gemini_vision.py`. |
| **Custom trained model** (detection/segmentation) or fine-tuning | Not started. |
| **Persistent cache** (Redis/DB) for live physical analysis | Only **in-memory** per server process. |

A strong next learning step: **curate ~20–50 labeled sites** (tower yes/no), run the live path, save thumbs + model JSON, and **score accuracy** before changing architecture.

---

## 6. Related commands

```bash
cd backend
python scripts/smoke_test.py
RUN_LIVE_CV=1 python scripts/smoke_test.py   # optional: live GEE + Gemini
```

With **`SAVE_GEE_THUMBNAILS=true`**, inspect **`backend/debug_gee_thumbnails/*.png`** after a successful live fetch (see folder README).

---

*Last aligned with backend layout: `ai/`, `services/settings.py`, `routes/buildings.py`, `debug_gee_thumbnails/`.*
