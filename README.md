# Collector

Monorepo: **Next.js** frontend in `collector/`, **FastAPI** backend in `backend/`. The landing page talks to the API for Site Prospecting (buildings, satellite analysis) and Water Economics.

---

## Prerequisites

| Tool | Notes |
|------|--------|
| **Node.js** | 20+ recommended (matches `collector` devDependencies). |
| **Python** | 3.11+ |
| **PostgreSQL + PostGIS** | Required for real API data. Easiest path: **Docker** using repo `docker-compose.yml`. |
| **npm** | Comes with Node. |

Optional:

- **Google Cloud** project with **Maps JavaScript API** and **Places API (New)** if you want address autocomplete in Site Prospecting.
- **Auth0** tenant if you want login and API key issuance in the UI.

---

## 1. Clone and install Node dependencies

From the **repository root**:

```bash
git clone <repo-url>
cd Collector
npm run setup
```

`npm run setup` runs `npm install` at the root (for `concurrently`) and `npm install` inside `collector/`.

To install only the Next app:

```bash
cd collector && npm install
```

---

## 2. Python backend — virtualenv and `requirements.txt`

Always use a **virtual environment** so `uvicorn` uses the same packages as `pip install`.

From the **repository root**:

```bash
cd backend
python3 -m venv .venv
```

**Activate** the venv:

- **macOS / Linux:** `source .venv/bin/activate`
- **Windows (cmd):** `.venv\Scripts\activate.bat`
- **Windows (PowerShell):** `.venv\Scripts\Activate.ps1`

Install Python dependencies:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

`backend/requirements.txt` includes FastAPI, Uvicorn, SQLAlchemy, PostGIS drivers, Google AI / Earth Engine clients, etc.

---

## 3. PostgreSQL (PostGIS) and `DATABASE_URL`

The API expects a **Postgres** database with **PostGIS** when `DATABASE_URL` is set.

### Option A — Docker (recommended)

From the **repository root**:

```bash
docker compose up -d
```

This starts PostGIS on **localhost:5432** with user/password/db `rainuse` / `rainuse` / `rainuse`.

Set in `backend/.env` (see below):

```env
DATABASE_URL=postgresql+psycopg://rainuse:rainuse@localhost:5432/rainuse
```

### Option B — your own Postgres

Create a database and enable PostGIS, then set `DATABASE_URL` in `backend/.env` using the `postgresql+psycopg://` scheme (see `backend/.env.example`).

---

## 4. Backend environment file

```bash
cp backend/.env.example backend/.env
```

Edit `backend/.env`. At minimum for local dev:

- **`DATABASE_URL`** — as above if you use Docker or your own Postgres.
- **`AUTH0_DOMAIN`** / **`AUTH0_CLIENT_ID`** — optional; align with the Next app if you use Auth0.

Load order: repo **root** `.env` (if present), then **`backend/.env`** (backend wins on duplicate keys). See `backend/env_load.py`.

---

## 5. Database schema and seed data

With `DATABASE_URL` set and Postgres running, from **`backend/`** with the venv **activated**:

```bash
cd backend
alembic upgrade head
python scripts/seed_database.py
```

- **`alembic upgrade head`** — applies migrations (`backend/migrations/`).
- **`python scripts/seed_database.py`** — loads CSV-backed fixtures (buildings, state context, etc.). See script docstring and `docs/DATABASE_SEED_DATA.md` for options (e.g. alternate building CSVs).

---

## 6. Frontend environment (`collector/.env.local`)

```bash
cp collector/.env.example collector/.env.local
```

| Variable | Required? | Purpose |
|----------|-----------|---------|
| `NEXT_PUBLIC_API_URL` | No | Backend base URL. Default: `http://127.0.0.1:8000` |
| `NEXT_PUBLIC_GOOGLE_MAPS_JS_API_KEY` | No | Address autocomplete (Places + Maps JS). |
| `NEXT_PUBLIC_AUTH0_DOMAIN` | No | Auth0 login. |
| `NEXT_PUBLIC_AUTH0_CLIENT_ID` | No | Auth0 SPA client. |
| `NEXT_PUBLIC_APP_BASE_URL` | No | App origin for Auth0 callbacks if not `http://localhost:3000`. |

Restart `npm run dev` after changing env vars.

`collector/next.config.ts` also loads `.env.local` from the **repository root** (parent of `collector/`), so `NEXT_PUBLIC_*` works if you only keep one file at `/Collector/.env.local` instead of `/Collector/collector/.env.local`. Values in `collector/.env.local` still override the same keys when both exist.

---

## 7. Run everything (frontend + backend)

From the **repository root**, with:

- Backend venv **activated** (so `uvicorn` uses installed packages), and  
- `backend/.env` configured (at least `DATABASE_URL` if you need data routes),

run:

```bash
npm run dev
```

This starts:

- **FastAPI:** [http://127.0.0.1:8000](http://127.0.0.1:8000) — `PYTHONPATH=. uvicorn main:app --reload`
- **Next.js:** [http://localhost:3000](http://localhost:3000)

Open the home page in the browser. The **Site Prospecting** block calls the API for states, buildings, rankings, and optional satellite/AI flows; **Water Economics** uses the same building selection.

### Run services separately

**Backend** (from repo root, venv activated):

```bash
cd backend && PYTHONPATH=. uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

**Frontend** (from repo root):

```bash
npm run dev --prefix collector
```

---

## 8. Useful checks

| Check | URL / command |
|--------|----------------|
| API liveness | [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health) |
| Database | [http://127.0.0.1:8000/health/db](http://127.0.0.1:8000/health/db) |
| API docs | [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) |
| Next production build | `npm run build --prefix collector` |

---

## 9. Troubleshooting

- **`ModuleNotFoundError` (e.g. sqlalchemy)** — Install into the **same** venv you use to run Uvicorn: `pip install -r backend/requirements.txt` with `.venv` activated.
- **Wrong Python / uvicorn** — Use `python -m uvicorn main:app --reload` from `backend/` after `source .venv/bin/activate` instead of a global `uvicorn`.
- **404 from Next to API** — Confirm the backend is running on port **8000** and `NEXT_PUBLIC_API_URL` matches (no trailing slash required).
- **Port already in use** — Stop other processes on **3000** or **8000**, or change ports (adjust `dev:backend` in root `package.json` and `NEXT_PUBLIC_API_URL` accordingly).
- **CORS** — Backend allows `http://localhost:3000` and `http://127.0.0.1:3000` by default (`backend/main.py`).
- **Google address search** — Enable **Maps JavaScript API** and **Places API (New)** on the same GCP project as the key; restrict the key by HTTP referrer for your dev origin.
- **Auth0** — Same Application settings in Auth0 for **Allowed Callback URLs** / **Web Origins** as your dev URL (e.g. `http://localhost:3000`).

---

## 10. Repo layout (short)

| Path | Role |
|------|------|
| `collector/` | Next.js 16 app (`app/`, `lib/`, `public/`) |
| `backend/` | FastAPI app (`main.py`, `routes/`, `database/`, `scripts/`) |
| `docker-compose.yml` | Local PostGIS |
| `package.json` (root) | `npm run dev` runs backend + frontend together |

For Next-specific docs, see `collector/README.md` (create-next-app defaults).
