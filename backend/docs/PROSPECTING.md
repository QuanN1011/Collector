# State prospecting — stable building records (priority 1)

This doc is the **handoff** for “prospecting by state”: how building data is loaded, which states are valid, and how the frontend should drive filters.

## Data sources (same API, two backends)

| Mode | When | Buildings | State context (rainfall + water $/1k gal) |
|------|------|-----------|---------------------------------------------|
| **Postgres** | `DATABASE_URL` set in `backend/.env` | `buildings` table (seeded from fixtures) | `state_context` table |
| **CSV fallback** | `DATABASE_URL` unset | `backend/data/buildings.csv` | `backend/data/state_context.csv` |

Both paths expose the **same** FastAPI routes. After changing CSVs, **restart** the server (`@lru_cache` loads CSVs once per process).

## Pilot dataset (continental US)

Bundled buildings use **USPS state codes** **TX**, **AZ**, and **PA** only. Every state that appears in `buildings` **must** have a matching row in `state_context` (rainfall + water price) or **`GET /buildings?state=XX`** will return **400** when validating context.

Full **50-state** `state_context.csv` is shipped so you can **add buildings** in other states without expanding the context file first.

## API contract for prospecting

1. **`GET /states`**  
   Returns `{ "states": ["AZ", "PA", "TX"] }` (sorted, from **distinct** `state_code` / CSV). Use this to build the state dropdown.

2. **`GET /buildings?state=TX`** (optional `state`)  
   - With `state`: validates **2-letter** code, requires **state context** row, returns enriched buildings (mock vision on lists).  
   - Without `state`: returns **all** buildings (demo / admin only — can be large).

3. **`GET /building/{id}`**  
   Same `id` values as in list responses. Unknown id → **404**.

4. **`GET /top-prospects?state=TX&limit=N`**  
   Requires `state`; same validation as buildings.

### Validation errors

- Malformed state (e.g. `TEX`, `9`, ``) → **400** with a clear message (`parse_state_code` in `database/db.py`).
- Valid code but no context row → **400** (missing `state_context`).

## Reproducible Postgres demo

```bash
# repo root
docker compose up -d

cd backend
source .venv/bin/activate
python scripts/seed_database.py
uvicorn main:app --reload --port 8000
```

Then: `GET http://127.0.0.1:8000/states` → `GET /buildings?state=TX`.

## Frontend checklist

- [ ] Load **`/states`** for the filter.  
- [ ] Only call **`/buildings?state=…`** with those codes (or handle **400**).  
- [ ] Use **`/building/{id}`** from the list row’s **`id`** (stable string).  
- [ ] Optional: **`live_cv=true`** only on **detail** (slow; see [VISION_PIPELINE.md](./VISION_PIPELINE.md)).

## Related code

- `database/db.py` — `list_buildings`, `get_building`, `get_state_context`, `parse_state_code`, `list_states_with_buildings`  
- `routes/states.py` — `GET /states`  
- `routes/buildings.py`, `routes/prospects.py` — state validation + **400** handling  
- `scripts/smoke_test.py` — regression checks for `/states` and multi-state lists  

---

*Expand to more states by adding rows to `buildings` / seed data; keep `state_context` aligned.*
