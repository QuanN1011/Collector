# Collector

## Run frontend + backend (local)

1. **Backend:** Python 3.11+, Postgres/PostGIS with `DATABASE_URL` in `backend/.env`, then from repo root:
   - `cd backend && alembic upgrade head` (if you use migrations)
   - `python scripts/seed_database.py` when you need data
2. **Install:** from repo root, `npm run setup` (installs root + `collector/` dependencies).
3. **Dev:** from repo root, `npm run dev` — starts FastAPI on [http://127.0.0.1:8000](http://127.0.0.1:8000) and Next.js on [http://localhost:3000](http://localhost:3000).

The home page **Prospecting** block loads states, buildings, rankings, and building detail (optional live satellite + AI); **Water economics** uses the same selection for state reference rates, rainfall, and rainwater value (including a rate stress-test).

Optional: copy `collector/.env.example` to `collector/.env.local` to change `NEXT_PUBLIC_API_URL`.