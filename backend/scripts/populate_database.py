"""
Populate the Postgres database from bundled fixtures (and optional local CSV overrides).

Who provides the data?
----------------------
- **You (the team)** must obtain or export data from external sites (EPA, World Population Review,
  TCEQ, SEC EDGAR, Open Buildings, Earth Engine, etc.). Licensing, terms of use, and API keys
  are your responsibility.
- This repo ships **sample CSVs** under ``data/`` for demos. A fully automated download of every
  third-party source is **not** included here (many sites block scraping or require accounts).

What this script does
---------------------
1. Runs Alembic migrations (``init_db`` via ``seed_database.seed``).
2. Loads bundled CSVs and derives related rows (companies, imagery metadata, CV detections,
   physical features, yields, utilities, policies, and ``building_scores``). See ``backend/SEED.md``.
3. Optionally **merges** rows from ``data/imports/state_context_overrides.csv`` if that file
   exists (per-state updates without editing the large ``state_context.csv``).

Usage (from ``backend/``)::

  export DATABASE_URL=postgresql+psycopg://rainuse:rainuse@localhost:5432/rainuse
  python scripts/populate_database.py

Optional overrides file: copy ``data/imports/state_context_overrides.csv.example`` to
``data/imports/state_context_overrides.csv`` and edit.

"""

from __future__ import annotations

import argparse
import csv
import importlib.util
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from env_load import load_backend_env

load_backend_env()
IMPORTS_DIR = BACKEND_ROOT / "data" / "imports"
OVERRIDES_CSV = IMPORTS_DIR / "state_context_overrides.csv"


def _load_seed_module():
    spec = importlib.util.spec_from_file_location(
        "seed_database",
        BACKEND_ROOT / "scripts" / "seed_database.py",
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Cannot load seed_database.py")
    mod = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(BACKEND_ROOT))
    spec.loader.exec_module(mod)
    return mod


def apply_state_context_overrides() -> int:
    """Apply per-state updates from ``data/imports/state_context_overrides.csv`` if present."""
    if not OVERRIDES_CSV.is_file():
        return 0

    from database.engine import get_session_factory
    from database.tables import StateContextRow

    updated = 0
    SessionLocal = get_session_factory()
    with SessionLocal() as session:
        with OVERRIDES_CSV.open(newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                st = (row.get("state") or "").strip().upper()
                if st.startswith("#") or len(st) != 2:
                    continue
                rainfall = row.get("rainfall_inches_annual")
                price = row.get("water_price_per_1000_gal_usd")
                if rainfall is None or price is None or str(rainfall).strip() == "":
                    continue
                obj = session.get(StateContextRow, st)
                if obj is None:
                    session.add(
                        StateContextRow(
                            state_code=st,
                            rainfall_inches_annual=float(rainfall),
                            water_price_per_1000_gal_usd=float(price),
                        )
                    )
                else:
                    obj.rainfall_inches_annual = float(rainfall)
                    obj.water_price_per_1000_gal_usd = float(price)
                updated += 1
        session.commit()
    return updated


def main() -> None:
    parser = argparse.ArgumentParser(description="Populate RainUSE Postgres from fixtures + optional overrides.")
    parser.add_argument(
        "--no-overrides",
        action="store_true",
        help="Do not apply data/imports/state_context_overrides.csv even if present.",
    )
    args = parser.parse_args()

    seed_mod = _load_seed_module()
    print("Running seed (migrations + full RainUSE MVP fixture load)...")
    seed_mod.seed()

    if args.no_overrides:
        print("Skipping optional state overrides (--no-overrides).")
        return

    n = apply_state_context_overrides()
    if n:
        print(f"Applied {n} row(s) from {OVERRIDES_CSV.relative_to(BACKEND_ROOT)}")
    else:
        print(
            f"No overrides applied (file missing or empty): {OVERRIDES_CSV.relative_to(BACKEND_ROOT)}. "
            "See data/imports/state_context_overrides.csv.example"
        )


if __name__ == "__main__":
    main()
