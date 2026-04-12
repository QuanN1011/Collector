"""
Fetch state-level mean annual precipitation (inches) from the Open-Meteo Archive API.

The API serves ERA5 (and related) reanalysis data; values are computed at each state's
approximate geographic centroid (see ``scripts/data_sources/state_centroids.py``), then
aggregated from daily precipitation sums (mm) to a 1991–2020 mean annual total (inches).

This is **not** identical to NOAA Climate Normals station aggregates, but it is **live API data**
with documented attribution (https://open-meteo.com).

Usage::

  python scripts/ingest_state_precip_open_meteo.py \\
    --merge-water-from data/state_context.csv \\
    --output data/state_context.csv

Requires ``httpx`` (already in requirements.txt).
"""

from __future__ import annotations

import argparse
import csv
import sys
import time
from collections import defaultdict
from pathlib import Path

import httpx

BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from services.state_centroids import STATE_CENTROIDS

MM_TO_IN = 1.0 / 25.4
ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"


def _mean_annual_precip_inches(daily: dict) -> float | None:
    times = daily.get("time") or []
    precips = daily.get("precipitation_sum") or []
    if len(times) != len(precips):
        return None
    by_year: dict[int, float] = defaultdict(float)
    for t, p in zip(times, precips):
        if p is None:
            continue
        y = int(str(t)[:4])
        by_year[y] += float(p)
    vals = [by_year[y] for y in sorted(by_year) if 1991 <= y <= 2020]
    if not vals:
        return None
    mean_mm = sum(vals) / len(vals)
    return round(mean_mm * MM_TO_IN, 2)


def fetch_state_precip_inches(lat: float, lon: float, client: httpx.Client) -> float | None:
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": "1991-01-01",
        "end_date": "2020-12-31",
        "daily": "precipitation_sum",
    }
    r = client.get(ARCHIVE_URL, params=params, timeout=120.0)
    r.raise_for_status()
    js = r.json()
    daily = js.get("daily") or {}
    return _mean_annual_precip_inches(daily)


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch state mean annual precipitation via Open-Meteo.")
    parser.add_argument(
        "--merge-water-from",
        type=Path,
        default=BACKEND_ROOT / "data" / "state_context.csv",
        help="Existing CSV whose water_price_per_1000_gal_usd column is preserved.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=BACKEND_ROOT / "data" / "state_context.csv",
        help="Output CSV path (can match merge file to overwrite rainfall only).",
    )
    parser.add_argument("--sleep-seconds", type=float, default=0.35, help="Delay between API calls.")
    args = parser.parse_args()

    water_by_state: dict[str, float] = {}
    if args.merge_water_from.is_file():
        with args.merge_water_from.open(newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                st = row["state"].strip().upper()
                water_by_state[st] = float(row["water_price_per_1000_gal_usd"])
    else:
        print(f"Warning: {args.merge_water_from} missing; water prices will be blank.", file=sys.stderr)

    rows: list[dict[str, str]] = []
    with httpx.Client() as client:
        for st in sorted(STATE_CENTROIDS):
            lat, lon = STATE_CENTROIDS[st]
            inches = fetch_state_precip_inches(lat, lon, client)
            if inches is None:
                print(f"Failed to fetch precipitation for {st}", file=sys.stderr)
                continue
            wp = water_by_state.get(st, "")
            rows.append(
                {
                    "state": st,
                    "rainfall_inches_annual": str(inches),
                    "water_price_per_1000_gal_usd": str(wp) if wp != "" else "",
                }
            )
            print(f"{st}: {inches} in/year (1991–2020 mean, ERA5 archive @ centroid)")
            time.sleep(max(0.0, args.sleep_seconds))

    # Ensure all 50 states + DC if centroids cover them
    if len(rows) < 50:
        print(f"Warning: only wrote {len(rows)} state rows.", file=sys.stderr)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["state", "rainfall_inches_annual", "water_price_per_1000_gal_usd"])
        w.writeheader()
        w.writerows(sorted(rows, key=lambda r: r["state"]))

    print(f"Wrote {len(rows)} rows → {args.output}")
    print("Attribution: precipitation from Open-Meteo Archive API (ERA5); see https://open-meteo.com")


if __name__ == "__main__":
    main()
