# Database commands and post-pull workflow

This document describes **important commands** related to the database and a **repeatable routine** to run after you **pull** updates from Git so your machine matches the team’s schema and dependencies.

---

## 1. Concepts (quick)

| Term | Meaning |
|------|--------|
| **`DATABASE_URL`** | Connection string for PostgreSQL (set in `backend/.env` or your shell). |
| **Migration** | A versioned schema change applied by **Alembic** (`backend/migrations/`). |
| **`init_db()`** | Backend helper that runs **`alembic upgrade head`** so the DB matches the latest migrations. |
| **Seed / populate** | Scripts that **insert demo or fixture data** after the schema exists. |

---

## 2. Important database-related commands

Run these from the **repository root** or **`backend/`** as noted.

### 2.1 Start PostgreSQL + PostGIS (local)

```bash
# Repo root
docker compose up -d
```

Matches `docker-compose.yml` (default user/db/password in `backend/.env.example`).

### 2.2 Configure the API

```bash
# backend/
cp .env.example .env
# Edit .env: set DATABASE_URL=postgresql+psycopg://rainuse:rainuse@localhost:5432/rainuse
```

### 2.3 Python environment (backend)

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2.4 Apply schema migrations (Alembic)

**Automatically** when the API starts: `init_db()` in `main.py` runs **`alembic upgrade head`** if `DATABASE_URL` is set.

**Manually** (same effect, useful for debugging):

```bash
cd backend
export DATABASE_URL=...   # or use .env
alembic upgrade head
```

**Create a new migration** after changing `database/tables.py` (review generated SQL, especially geometry):

```bash
cd backend
alembic revision --autogenerate -m "short description"
alembic upgrade head
```

### 2.5 Populate demo data (fixtures)

**Full populate** (migrations + seed + optional overrides):

```bash
cd backend
export DATABASE_URL=...
python scripts/populate_database.py
```

**Seed only** (same core seed, no optional override merge):

```bash
cd backend
python scripts/seed_database.py
```

Optional: copy `data/imports/state_context_overrides.csv.example` to `data/imports/state_context_overrides.csv` and adjust, then run `populate_database.py` again.

**Data provenance (what is real vs synthetic, APIs vs generated, CV not required for Microsoft/API ingest):** see [`docs/DATA_SOURCES_REAL_VS_GENERATED.md`](DATA_SOURCES_REAL_VS_GENERATED.md). Deeper lineage: [`docs/DATABASE_SEED_DATA.md`](DATABASE_SEED_DATA.md). Operational notes: [`backend/SEED.md`](../backend/SEED.md).

### 2.6 Run the API

```bash
cd backend
uvicorn main:app --reload
```

Open `http://127.0.0.1:8000/docs` for interactive API docs.

---

## 3. General execution order (first-time setup)

1. Install **Docker** (for Postgres) or point `DATABASE_URL` at a hosted Postgres with **PostGIS**.
2. `docker compose up -d` (if using local compose).
3. `backend/.env` with valid `DATABASE_URL`.
4. `cd backend` → venv → `pip install -r requirements.txt`.
5. `python scripts/populate_database.py` **or** start `uvicorn` once (migrations run on startup) then `python scripts/seed_database.py` if you need data.
6. Frontend (if used): `cd collector` → `npm install` → `npm run dev`.

---

## 4. Every time you `git pull` — refresh checklist

Pulling can change **dependencies**, **migrations**, **seed CSVs**, or **scripts**. Use this checklist after each update:

| Step | Action |
|------|--------|
| 1 | **`git pull`** (or merge/rebase as your team does). |
| 2 | **Backend deps:** `cd backend && pip install -r requirements.txt` (venv active). |
| 3 | **DB schema:** With `DATABASE_URL` set, run **`alembic upgrade head`** **or** start the API once so **`init_db()`** runs. |
| 4 | **Data (if fixtures changed or DB empty):** `python scripts/populate_database.py` or `seed_database.py`. |
| 5 | **Frontend deps:** `cd collector && npm install` (if `package-lock.json` changed). |
| 6 | **Re-read docs:** If `docs/` or `README` changed, skim **`docs/DATABASE_DECISIONS.md`**, **`docs/DATA_SOURCES_REAL_VS_GENERATED.md`** (real vs generated data), **`docs/DATABASE_SEED_DATA.md`**, and **this file** for new commands or env vars. |

If a teammate added a **new Alembic revision**, step 3 is mandatory before relying on old data.

---

## 5. CSV fallback (no Docker)

If **`DATABASE_URL`** is **unset**, the API reads **`backend/data/*.csv`** only; migrations against Postgres are skipped. Useful for quick UI work without a database.

---

## 6. Who updates this document?

When you change **how** the database is created, seeded, or deployed, update:

- **`docs/DATABASE_DECISIONS.md`** — product/schema *decisions*.
- **`docs/DATA_SOURCES_REAL_VS_GENERATED.md`** — *real ingest vs generated*, *CV vs APIs*, and *script index*.
- **`docs/DATABASE_SEED_DATA.md`** — *sources*, *inferred fields*, and *fixture lineage* for seeded data.
- **`docs/DATABASE_AND_WORKFLOW.md`** (this file) — *commands* and *pull/update* routine.

---

*Last aligned with backend layout: `database/`, `migrations/`, `scripts/populate_database.py`, `scripts/seed_database.py`, `docs/DATABASE_SEED_DATA.md`.*
