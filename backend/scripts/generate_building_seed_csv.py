"""
Generate backend/data/buildings.csv with pilot-heavy commercial/industrial candidates.

Run from repo root or backend:
  python scripts/generate_building_seed_csv.py

Not executed automatically by the API; commit the CSV output for reproducible seeds.
Footprint areas are synthetic; geometry in DB is derived at seed time (see seed_database.py).
"""

from __future__ import annotations

import csv
import random
from pathlib import Path

_DATA = Path(__file__).resolve().parent.parent / "data"
_OUT = _DATA / "buildings.csv"

# Metro seeds: (city, state, center_lat, center_lon)
_METROS: list[tuple[str, str, float, float]] = [
    # Texas
    ("Dallas", "TX", 32.78, -96.80),
    ("Houston", "TX", 29.76, -95.36),
    ("Austin", "TX", 30.27, -97.74),
    ("San Antonio", "TX", 29.42, -98.49),
    ("Fort Worth", "TX", 32.75, -97.33),
    ("El Paso", "TX", 31.76, -106.49),
    ("Mesquite", "TX", 32.77, -96.60),
    ("Laredo", "TX", 27.53, -99.46),
    ("Corpus Christi", "TX", 27.80, -97.40),
    ("Plano", "TX", 33.02, -96.70),
    # Arizona
    ("Phoenix", "AZ", 33.45, -112.07),
    ("Tucson", "AZ", 32.22, -110.97),
    ("Mesa", "AZ", 33.42, -111.83),
    ("Chandler", "AZ", 33.31, -111.84),
    ("Glendale", "AZ", 33.54, -112.19),
    ("Scottsdale", "AZ", 33.49, -111.93),
    ("Tempe", "AZ", 33.43, -111.94),
    ("Peoria", "AZ", 33.58, -112.24),
    # Pennsylvania
    ("Philadelphia", "PA", 39.95, -75.15),
    ("Pittsburgh", "PA", 40.44, -79.99),
    ("Allentown", "PA", 40.60, -75.47),
    ("Erie", "PA", 42.13, -80.09),
    ("Harrisburg", "PA", 40.27, -76.88),
]

_COMPANIES = [
    "cmp-amzn",
    "cmp-wmt",
    "cmp-tgt",
    "cmp-fdx",
    "cmp-ups",
    "cmp-tsla",
    "cmp-gm",
    "cmp-intc",
    "cmp-mu",
    "cmp-ko",
    "cmp-pep",
    "cmp-xom",
    "cmp-cvs",
    "cmp-hd",
    "cmp-nke",
    "",
]

_NAMES = [
    "Regional Distribution Center",
    "Industrial Park Building",
    "Manufacturing Campus",
    "Cold Storage Facility",
    "Fulfillment Hub",
    "Semiconductor Warehouse",
    "Chemical Processing Annex",
    "Food & Beverage Plant",
    "Automotive Supplier Complex",
    "Logistics Cross-Dock",
    "Printing & Packaging Plant",
    "Data Hall Support Building",
    "Aerospace Components Plant",
    "Plastics Extrusion Facility",
    "Metal Finishing Facility",
]


def _jitter(rng: random.Random, lat: float, lon: float) -> tuple[float, float]:
    return lat + rng.uniform(-0.09, 0.09), lon + rng.uniform(-0.11, 0.11)


def _roof(rng: random.Random, prefer_large: bool) -> float:
    if prefer_large:
        # Target RainUSE “strong candidate” band (~100k–450k sq ft commercial/industrial roofs).
        return float(rng.uniform(100_000, 450_000))
    # Rare edge-case row: still large-format industrial, slightly below the 100k marketing cutoff.
    return float(rng.uniform(88_000, 99_500))


def main() -> None:
    rng = random.Random(42)
    rows: list[dict[str, str]] = []
    n = 0
    for city, st, clat, clon in _METROS * 3:
        # ~92% meet/exceed the 100k sq ft prospecting threshold; a few “near miss” rows for UI edge cases.
        prefer_large = (n % 12) != 0
        lat, lon = _jitter(rng, clat, clon)
        roof = _roof(rng, prefer_large)
        comp = rng.choice(_COMPANIES)
        suffix = f"{st.lower()}-{city.lower().replace(' ', '')}-{n:03d}"
        bid = f"bru-{suffix}"
        name = f"{city} {_NAMES[n % len(_NAMES)]} {n % 100}"
        rows.append(
            {
                "id": bid,
                "name": name,
                "state": st,
                "city": city,
                "roof_area_sqft": f"{roof:.0f}",
                "latitude": f"{lat:.6f}",
                "longitude": f"{lon:.6f}",
                "company_id": comp,
                "building_type": rng.choice(["distribution", "manufacturing", "warehouse", "food_processing"]),
                "land_use_type": rng.choice(["industrial", "commercial", "logistics"]),
            }
        )
        n += 1
        if n >= 78:
            break

    # Ensure pilot states dominate: already the case from metros
    _OUT.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "id",
        "name",
        "state",
        "city",
        "roof_area_sqft",
        "latitude",
        "longitude",
        "company_id",
        "building_type",
        "land_use_type",
    ]
    with _OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)
    print(f"Wrote {len(rows)} rows to {_OUT}")


if __name__ == "__main__":
    main()
