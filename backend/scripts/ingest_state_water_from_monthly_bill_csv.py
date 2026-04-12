#!/usr/bin/env python3
"""
Merge **monthly residential water bill ($/mo)** by state into ``state_context.csv`` as
``water_price_per_1000_gal_usd``.

Conversion (same rough assumption as ``docs/DATA_SOURCES_WATER_PRICING.md``):

    water_price_per_1000_gal_usd ≈ monthly_bill_usd / 12

This is a **proxy** (tiered rates, sewer, fixed fees differ). Tune or replace with
utility tariffs for production.

Usage (from ``backend/``):

  python scripts/ingest_state_water_from_monthly_bill_csv.py \\
    --monthly data/water-prices-by-state-2026.csv \\
    --state-context data/state_context.csv

Dry-run (print rows, do not write):

  python scripts/ingest_state_water_from_monthly_bill_csv.py ... --dry-run
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

# Full state name → USPS (as in World Population Review–style tables)
_STATE_NAME_TO_CODE: dict[str, str] = {
    "Alabama": "AL",
    "Alaska": "AK",
    "Arizona": "AZ",
    "Arkansas": "AR",
    "California": "CA",
    "Colorado": "CO",
    "Connecticut": "CT",
    "Delaware": "DE",
    "Florida": "FL",
    "Georgia": "GA",
    "Hawaii": "HI",
    "Idaho": "ID",
    "Illinois": "IL",
    "Indiana": "IN",
    "Iowa": "IA",
    "Kansas": "KS",
    "Kentucky": "KY",
    "Louisiana": "LA",
    "Maine": "ME",
    "Maryland": "MD",
    "Massachusetts": "MA",
    "Michigan": "MI",
    "Minnesota": "MN",
    "Mississippi": "MS",
    "Missouri": "MO",
    "Montana": "MT",
    "Nebraska": "NE",
    "Nevada": "NV",
    "New Hampshire": "NH",
    "New Jersey": "NJ",
    "New Mexico": "NM",
    "New York": "NY",
    "North Carolina": "NC",
    "North Dakota": "ND",
    "Ohio": "OH",
    "Oklahoma": "OK",
    "Oregon": "OR",
    "Pennsylvania": "PA",
    "Rhode Island": "RI",
    "South Carolina": "SC",
    "South Dakota": "SD",
    "Tennessee": "TN",
    "Texas": "TX",
    "Utah": "UT",
    "Vermont": "VT",
    "Virginia": "VA",
    "Washington": "WA",
    "West Virginia": "WV",
    "Wisconsin": "WI",
    "Wyoming": "WY",
}


def _read_monthly(path: Path) -> dict[str, float]:
    """state_code -> water_price_per_1000_gal from monthly bill column."""
    out: dict[str, float] = {}
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = (row.get("state") or row.get("State") or "").strip()
            raw = row.get("WaterPricesMonthlyWaterBill_2025") or row.get("monthly_water_bill_usd") or ""
            if not name or not raw.strip():
                continue
            try:
                monthly = float(raw.replace("$", "").strip())
            except ValueError:
                continue
            code = _STATE_NAME_TO_CODE.get(name)
            if not code:
                print(f"Warning: unknown state name {name!r}, skip.", file=sys.stderr)
                continue
            per_1k = round(monthly / 12.0, 2)
            out[code] = per_1k
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Merge monthly water bill CSV into state_context water_price column.")
    ap.add_argument("--monthly", type=Path, required=True, help="CSV with state name + monthly bill")
    ap.add_argument("--state-context", type=Path, required=True, help="state_context.csv to read/update")
    ap.add_argument("--dry-run", action="store_true", help="Print updates only; do not write")
    args = ap.parse_args()

    prices = _read_monthly(args.monthly)
    if not prices:
        print("No rows parsed from monthly CSV.", file=sys.stderr)
        return 1

    rows: list[dict[str, str]] = []
    with args.state_context.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or ["state", "rainfall_inches_annual", "water_price_per_1000_gal_usd"]
        for row in reader:
            st = row["state"].strip().upper()
            if st in prices:
                old = row.get("water_price_per_1000_gal_usd", "")
                row["water_price_per_1000_gal_usd"] = str(prices[st])
                print(f"{st}: water_price {old} -> {prices[st]} ($/1k gal from monthly/12)")
            rows.append(row)

    if args.dry_run:
        print("Dry-run: not writing.")
        return 0

    with args.state_context.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)

    print(f"Updated {args.state_context} ({len(prices)} state price overrides applied).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
