"""
Download Microsoft US Building Footprints (GeoJSON per state) and emit a CSV for seeding.

Source: https://github.com/microsoft/USBuildingFootprints (ODbL). Files are fetched from the
official Azure CDN URLs published in that repository's README.

This script streams features (ijson) so the full GeoJSON does not need to fit in RAM. Large states
(Texas ~2.8 GiB unzipped) require disk space and patience.

Usage (from backend/)::

  # Subset of states:
  python scripts/ingest_ms_buildings.py --states Texas Arizona Pennsylvania \\
    --min-sqft 100000 --max-per-state 150 --output data/buildings_microsoft.csv

  # All 50 states + DC (long-running; caches zips under data/cache/ms_footprints):
  python scripts/ingest_ms_buildings.py --all-states --min-sqft 100000 --max-per-state 300 \\
    --output data/buildings_microsoft_nationwide.csv

  # Refresh catalog after ingest:
  python scripts/merge_buildings_catalog.py

Requires: ijson, shapely, pyproj (see requirements.txt).
"""

from __future__ import annotations

import argparse
import csv
import sys
import zipfile
from pathlib import Path

import httpx
import ijson
from shapely.geometry import shape as shp_shape

BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from services.footprint_geometry import footprint_to_multipolygon_wkt, polygon_area_sqft
from services.nominatim_reverse import reverse_geocode

DEFAULT_CACHE = BACKEND_ROOT / "data" / "cache" / "ms_footprints"
DEFAULT_GEOCODE_CACHE = BACKEND_ROOT / "data" / "cache" / "nominatim_reverse"

# Official download pattern from microsoft/USBuildingFootprints README.
MS_BASE = "https://minedbuildings.z5.web.core.windows.net/legacy/usbuildings-v2"

# Map CLI state names (file stem) to 2-letter codes.
STATE_CODE_BY_STEM: dict[str, str] = {
    "Alabama": "AL",
    "Alaska": "AK",
    "Arizona": "AZ",
    "Arkansas": "AR",
    "California": "CA",
    "Colorado": "CO",
    "Connecticut": "CT",
    "Delaware": "DE",
    "DistrictofColumbia": "DC",
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
    "NewHampshire": "NH",
    "NewJersey": "NJ",
    "NewMexico": "NM",
    "NewYork": "NY",
    "NorthCarolina": "NC",
    "NorthDakota": "ND",
    "Ohio": "OH",
    "Oklahoma": "OK",
    "Oregon": "OR",
    "Pennsylvania": "PA",
    "RhodeIsland": "RI",
    "SouthCarolina": "SC",
    "SouthDakota": "SD",
    "Tennessee": "TN",
    "Texas": "TX",
    "Utah": "UT",
    "Vermont": "VT",
    "Virginia": "VA",
    "Washington": "WA",
    "WestVirginia": "WV",
    "Wisconsin": "WI",
    "Wyoming": "WY",
}


def _download_zip(url: str, dest: Path, timeout: float) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    with httpx.Client(timeout=timeout, follow_redirects=True) as client:
        with client.stream("GET", url) as r:
            r.raise_for_status()
            with dest.open("wb") as f:
                for chunk in r.iter_bytes():
                    f.write(chunk)


def _extract_geojson(zip_path: Path, dest_dir: Path) -> Path:
    dest_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "r") as zf:
        names = [n for n in zf.namelist() if n.lower().endswith(".geojson")]
        if not names:
            raise RuntimeError(f"No .geojson inside {zip_path}")
        member = names[0]
        out = dest_dir / Path(member).name
        out.write_bytes(zf.read(member))
        return out


def _all_state_stems_ordered() -> list[str]:
    """Stem keys for Microsoft CDN zips, ordered by USPS code (AL … WY, DC)."""
    return sorted(STATE_CODE_BY_STEM.keys(), key=lambda k: STATE_CODE_BY_STEM[k])


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest Microsoft US Building Footprints into CSV.")
    parser.add_argument(
        "--all-states",
        action="store_true",
        help="Process every region in the Microsoft dataset (50 states + DC). Use with --min-sqft / --max-per-state.",
    )
    parser.add_argument(
        "--states",
        nargs="*",
        default=None,
        help='State names matching file stems, e.g. "Texas" "DistrictofColumbia". Not used with --all-states.',
    )
    parser.add_argument("--min-sqft", type=float, default=100_000.0)
    parser.add_argument("--max-per-state", type=int, default=200)
    parser.add_argument("--cache-dir", type=Path, default=DEFAULT_CACHE)
    parser.add_argument("--output", type=Path, default=BACKEND_ROOT / "data" / "buildings_microsoft.csv")
    parser.add_argument("--force-download", action="store_true")
    parser.add_argument("--http-timeout", type=float, default=600.0)
    parser.add_argument(
        "--skip-geocode",
        action="store_true",
        help="Do not call Nominatim (city/county/geocode_display_name left empty).",
    )
    parser.add_argument(
        "--geocode-cache-dir",
        type=Path,
        default=DEFAULT_GEOCODE_CACHE,
        help="JSON cache directory for reverse geocode responses (respects Nominatim rate limits).",
    )
    parser.add_argument(
        "--geocode-delay",
        type=float,
        default=1.1,
        help="Seconds to sleep after each uncached Nominatim request (policy: ~1 req/s).",
    )
    args = parser.parse_args()

    if args.all_states and args.states:
        parser.error("Use either --all-states or --states, not both")
    if args.all_states:
        state_names = _all_state_stems_ordered()
    elif args.states:
        state_names = args.states
    else:
        parser.error("Provide --states NAME [NAME ...] or use --all-states")

    fieldnames = [
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
    rows_written = 0
    args.output.parent.mkdir(parents=True, exist_ok=True)

    with args.output.open("w", newline="", encoding="utf-8") as out_f:
        writer = csv.DictWriter(out_f, fieldnames=fieldnames)
        writer.writeheader()

        for state_name in state_names:
            stem = state_name.replace(" ", "")
            if stem not in STATE_CODE_BY_STEM:
                print(f"Unknown state name for Microsoft dataset: {state_name!r}", file=sys.stderr)
                sys.exit(1)
            st_code = STATE_CODE_BY_STEM[stem]
            zip_name = f"{stem}.geojson.zip"
            url = f"{MS_BASE}/{zip_name}"
            zip_path = args.cache_dir / zip_name
            if args.force_download or not zip_path.is_file():
                print(f"Downloading {url} → {zip_path} …")
                _download_zip(url, zip_path, timeout=args.http_timeout)
            else:
                print(f"Using cached zip {zip_path}")

            extract_dir = args.cache_dir / "extracted" / stem
            gj_path = _extract_geojson(zip_path, extract_dir)
            print(f"Streaming {gj_path} …")

            count = 0
            idx = 0
            with gj_path.open("rb") as f:
                for feature in ijson.items(f, "features.item"):
                    idx += 1
                    if idx % 250_000 == 0:
                        print(f"  … scanned {idx:,} features, kept {count} large footprints in {st_code}")
                    geom = feature.get("geometry")
                    if not geom:
                        continue
                    try:
                        area = polygon_area_sqft(geom)
                    except Exception:
                        continue
                    if area < args.min_sqft:
                        continue
                    try:
                        wkt = footprint_to_multipolygon_wkt(geom)
                    except Exception:
                        continue
                    g = shp_shape(geom)
                    c = g.centroid
                    lon, lat = c.x, c.y
                    bid = f"ms-{st_code.lower()}-{rows_written:06d}"
                    city = ""
                    county = ""
                    geocode_display_name = ""
                    if not args.skip_geocode:
                        try:
                            geo = reverse_geocode(
                                lat,
                                lon,
                                expect_state_code=st_code,
                                cache_dir=args.geocode_cache_dir,
                                delay_after_request_sec=args.geocode_delay,
                            )
                            city = geo.city
                            county = geo.county
                            geocode_display_name = geo.display_name
                            if not geo.state_matches_expected:
                                print(
                                    f"WARN geocode: Nominatim state does not match ingest state "
                                    f"{st_code} for {bid} ({lat:.5f}, {lon:.5f})",
                                    file=sys.stderr,
                                )
                        except Exception as exc:
                            print(f"WARN reverse_geocode failed for {bid}: {exc}", file=sys.stderr)
                    writer.writerow(
                        {
                            "id": bid,
                            "name": f"Microsoft footprint {st_code} #{count + 1}",
                            "state": st_code,
                            "city": city,
                            "county": county,
                            "geocode_display_name": geocode_display_name,
                            "roof_area_sqft": f"{round(area, 2)}",
                            "latitude": f"{lat:.7f}",
                            "longitude": f"{lon:.7f}",
                            "company_id": "",
                            "building_type": "commercial_industrial_unknown",
                            "land_use_type": "unknown",
                            "footprint_wkt": wkt,
                            "data_source": "microsoft_us_building_footprints",
                        }
                    )
                    rows_written += 1
                    count += 1
                    if count >= args.max_per_state:
                        break

            print(f"Finished {state_name}: wrote {count} row(s) (min area ≥ {args.min_sqft:,.0f} sq ft).")

    print(f"Done. Total rows: {rows_written} → {args.output}")


if __name__ == "__main__":
    main()
