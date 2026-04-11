# RainUSE Nexus — Database decisions

This document records **what we decided** for the relational schema and persistence layer, and **why**, so backend, frontend, and data teammates can align without re-litigating the same topics.

**Stack:** PostgreSQL with **PostGIS** extension, **SQLAlchemy 2** ORM in the Python backend (`backend/database/`).  
**Scope:** Hackathon prototype; prefer **simple, conservative** tables with clear paths to extend later.

---

## 1. Building-centric model

- **Decision:** Everything that matters for prospecting ultimately references a **`buildings`** row (site candidate).
- **Why:** The product is “which buildings to target,” not abstract regions. Maps, scores, and CV outputs all anchor on a building id.

---

## 2. Drought and climate stress

- **Decision:** Treat **drought / regional water stress** as part of **`climate_risk_score`** on **`building_scores`**, not as a separate column for v1.
- **Why:** Keeps the schema small; the **meaning** of the number comes from **upstream datasets + the scoring pipeline**, not from the column name alone. We can split into a dedicated field later if product copy needs it.

---

## 3. Choropleth (map coloring)

- **Decision:** **State-level choropleth only** for the hackathon. Aggregate with **mean** of **`final_viability_score`** per state (investment impact framing). **Live queries** — no precomputed regional stats tables.
- **Why:** Fast to ship; 50 states are cheap to aggregate in SQL or in memory at prototype scale. **Comments / follow-ups:** allow **max** or **median** later via query changes (no schema change required).
- **Note:** State boundaries come from **static GeoJSON or the map provider**, not from Postgres.

---

## 4. Rankings and “top N”

- **Decision:** **Do not store** rank columns (e.g. `rank_in_state`). Use **`ORDER BY final_viability_score DESC LIMIT n`** with **`n`** supplied by the API (default **10**, cap e.g. **1000**).
- **Why:** Stored ranks go **stale** whenever data changes; `ORDER BY` is always **truth**. **Follow-up:** if we ever need materialized ranks at scale, add **`rankings_computed_at`** and a batch job — documented as a later option only.

---

## 5. Scores: single source of truth (hackathon rule)

- **Decision:** **Rollups** consumed by the API and map (e.g. **`final_viability_score`**, pillar scores on **`building_scores`**) are the **canonical** presentation layer. **Feature / input** tables (future: CV features, raw model outputs) must **not duplicate the same metric name** as both “input” and “final” unless one is clearly raw and one is final.
- **Why:** Avoids two tables drifting apart (“which physical score is real?”).

---

## 6. Tower / detection confidence vs dataset

- **Decision:** **`detection_confidence_score`** on **`building_scores`** is produced by a **scoring / aggregation step** (e.g. combine roof vs cooling-tower model confidences with a documented rule). It is **not** a raw field copied straight from an ingest CSV.
- **Why:** The **database stores the result**; the **rule** lives in one place in code so the team does not guess max vs mean vs weighted blend.

---

## 7. Corporate ESG when no company is linked

- **Decision:** **`corporate_esg_score`** is **nullable** — “no corporate contribution” when unknown or unlinked.
- **Why:** Honest semantics; avoids pretending we know ESG when we do not. Downstream scoring can reweight or omit; document the formula in the scoring module.

---

## 8. Geography: footprint vs centroid

- **Decision:** Store **both**:
  - **`footprint_geom`**: PostGIS **MultiPolygon, SRID 4326** for accuracy (roof/site geometry) when available; nullable until the pipeline fills it.
  - **`latitude` / `longitude`**: scalar columns for **map pins**, simple APIs, and fewer ORM surprises in a short hackathon.
- **Why:** Polygons are best for **area/spatial truth**; lat/lon is best for **fast map UX** and **indexing** patterns everyone understands. Optional later: **GiST** index on `footprint_geom` or on a PostGIS **point** built from lat/lon for bbox queries.

---

## 9. State normalization

- **Decision:** **`state_code`** is **two-letter US** (normalized to upper case in app and seed).
- **Why:** Consistent **`GROUP BY`** for choropleth and filters; avoids `TX` vs `Texas` bugs.

---

## 10. Live queries and no regional stat tables

- **Decision:** **No** `state_stats` / materialized rollups for v1.
- **Why:** Prototype scale; fewer moving parts. Revisit if queries become slow.

---

## 11. Large text (SEC / ESG documents)

- **Decision (operational):** **Externalize** full **PDF/HTML** bodies to **object storage** (S3/GCS); DB holds **`storage_uri`**, **`content_hash`**, **`byte_length`**, optional short **`excerpt`**. **`parsed_json`** stays in DB only while small.
- **Why:** Keeps backups and replicas manageable. **“Externalize”** = *not* storing huge blobs only in Postgres.

---

## 12. Current implementation (this repo)

| Piece | Role |
|--------|------|
| **`state_context`** | Per-state rainfall and water price inputs for MVP scoring. |
| **`buildings`** | Core site; `state_code`, roof area, lat/lon, optional `footprint_geom`. |
| **`building_scores`** | Single current rollup per building: `final_viability_score`, `climate_risk_score`, nullable `corporate_esg_score`, nullable `detection_confidence_score`, `computed_at`. |

- **CSV fallback:** If **`DATABASE_URL`** is unset, the API still reads **`backend/data/*.csv`** so anyone can run without Docker.
- **Postgres path:** **`docker-compose.yml`** provides PostGIS; **`backend/scripts/seed_database.py`** loads CSVs and **writes computed** `final_viability_score` (and a **placeholder** `climate_risk_score` for demo). **Tower confidences** remain **computed in app code** until the CV pipeline writes **`detection_confidence_score`**.
- **Note:** If **`final_viability_score`** is overridden from **`building_scores`** but the API still returns a **computed breakdown** dict, those subscores may not sum to the overridden total until the scoring service persists full breakdowns (acceptable for the prototype).

---

## 13. Future extensions (explicitly not required for v1)

- **Score history** table or append-only **`building_scores`** versions + `score_version`.
- **Bbox / map viewport queries** using PostGIS + GiST (after state-level ship).
- **County / MSA** choropleth: add **`county_fips`** or similar.
- **Company / document** tables for SEC/SBTi when ingestion exists.
- **PII / retention** for addresses — only if product requires it.

---

## 14. How to run the database locally

1. `docker compose up -d` (repo root).
2. Copy `backend/.env.example` → `backend/.env` (or export `DATABASE_URL`).
3. From `backend/`: `python scripts/seed_database.py`.
4. Start API: `uvicorn main:app --reload` (working directory `backend/`).

---

*Last updated to match team decisions for RainUSE Nexus hackathon scope.*
