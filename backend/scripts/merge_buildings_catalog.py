"""
Merge Microsoft US Building Footprints CSV rows with synthetic seed rows.

Microsoft rows are the preferred catalog baseline. Synthetic ``bru-*`` rows are kept only for
states that have **no** Microsoft row in the Microsoft CSV (auto mode), or when using
``--keep-synthetic-states`` to force-keep specific states.

Typical use after ``ingest_ms_buildings.py``::

  python scripts/ingest_ms_buildings.py --all-states --min-sqft 100000 --max-per-state 300 \\
    --output data/buildings_microsoft_nationwide.csv
  python scripts/merge_buildings_catalog.py --microsoft data/buildings_microsoft_nationwide.csv

"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

# Superset columns: Microsoft ingest adds footprint_wkt + data_source.
FIELDNAMES = [
    "id",
    "name",
    "state",
    "city",
    "county",
    "geocode_display_name",
    "roof_area_sqft",
    "latitude",
    "longitude",
    "company_id",
    "building_type",
    "land_use_type",
    "footprint_wkt",
    "data_source",
]


def _row_normalize(row: dict[str, str]) -> dict[str, str]:
    return {k: (row.get(k) or "").strip() for k in FIELDNAMES}


def _default_microsoft_csv() -> Path:
    """Prefer nationwide ingest output, then multi-state, then TX sample."""
    for name in (
        "buildings_microsoft_nationwide.csv",
        "buildings_microsoft.csv",
        "buildings_microsoft_tx_sample.csv",
    ):
        p = BACKEND_ROOT / "data" / name
        if p.is_file():
            return p
    return BACKEND_ROOT / "data" / "buildings_microsoft_tx_sample.csv"


def main() -> None:
    p = argparse.ArgumentParser(description="Merge Microsoft footprint CSV + synthetic buildings CSV.")
    p.add_argument(
        "--microsoft",
        type=Path,
        dest="microsoft_csv",
        default=None,
        help="CSV from ingest_ms_buildings.py. Default: first existing of "
        "buildings_microsoft_nationwide.csv, buildings_microsoft.csv, buildings_microsoft_tx_sample.csv.",
    )
    p.add_argument(
        "--synthetic",
        type=Path,
        default=BACKEND_ROOT / "data" / "buildings.csv",
        help="Legacy synthetic generator output (bru-* ids).",
    )
    p.add_argument(
        "--output",
        type=Path,
        default=BACKEND_ROOT / "data" / "buildings_catalog.csv",
        help="Merged CSV for seed_database.py.",
    )
    p.add_argument(
        "--auto-exclude-synthetic",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Drop synthetic rows for any USPS code that appears in the Microsoft CSV (default: on).",
    )
    p.add_argument(
        "--keep-synthetic-states",
        nargs="*",
        default=[],
        help="Always keep synthetic rows for these states even if Microsoft has rows (e.g. testing).",
    )
    args = p.parse_args()

    ms_path = args.microsoft_csv or _default_microsoft_csv()
    ms_rows: list[dict[str, str]] = []
    if ms_path.is_file():
        with ms_path.open(newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                ms_rows.append(_row_normalize(row))
    else:
        print(f"Warning: Microsoft CSV missing ({ms_path}); output is synthetic-only.", file=sys.stderr)

    ms_states: set[str] = {r["state"].strip().upper() for r in ms_rows if r.get("state")}
    keep_syn = {s.strip().upper() for s in args.keep_synthetic_states}

    syn_kept: list[dict[str, str]] = []
    with args.synthetic.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            st = (row.get("state") or "").strip().upper()
            if args.auto_exclude_synthetic and st in ms_states and st not in keep_syn:
                continue
            syn_kept.append(_row_normalize(row))

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as out:
        w = csv.DictWriter(out, fieldnames=FIELDNAMES)
        w.writeheader()
        for row in ms_rows + syn_kept:
            w.writerow(row)

    print(
        f"Wrote {args.output} — {len(ms_rows)} Microsoft row(s), "
        f"{len(syn_kept)} synthetic row(s). "
        f"Microsoft states: {len(ms_states)} ({', '.join(sorted(ms_states))})."
    )


if __name__ == "__main__":
    main()
