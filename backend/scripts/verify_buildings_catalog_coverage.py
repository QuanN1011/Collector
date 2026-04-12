"""
Report building catalog coverage: state_context vs Microsoft vs synthetic (bru-*).

Reads ``data/buildings_catalog.csv`` and ``data/state_context.csv`` (no DB required).

Usage (from backend/)::

  python scripts/verify_buildings_catalog_coverage.py
"""

from __future__ import annotations

import csv
import sys
from collections import Counter, defaultdict
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent.parent
_DATA = BACKEND_ROOT / "data"


def main() -> None:
    catalog = _DATA / "buildings_catalog.csv"
    sc_path = _DATA / "state_context.csv"
    if not catalog.is_file():
        print(f"Missing {catalog}", file=sys.stderr)
        sys.exit(1)

    with sc_path.open(newline="", encoding="utf-8") as f:
        state_ctx_rows = list(csv.DictReader(f))
    states_ctx = {r["state"].strip().upper() for r in state_ctx_rows}

    ms_by_state: Counter[str] = Counter()
    syn_by_state: Counter[str] = Counter()
    examples_ms: dict[str, dict[str, str]] = {}
    states_with_rows: set[str] = set()

    with catalog.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            st = (row.get("state") or "").strip().upper()
            if not st:
                continue
            states_with_rows.add(st)
            ds = (row.get("data_source") or "").strip()
            bid = (row.get("id") or "").strip()
            if ds == "microsoft_us_building_footprints":
                ms_by_state[st] += 1
                if st not in examples_ms and bid:
                    examples_ms[st] = row
            elif bid.startswith("bru-"):
                syn_by_state[st] += 1

    ms_state_set = set(ms_by_state.keys())
    syn_fallback_states = sorted(st for st in states_ctx if syn_by_state.get(st, 0) > 0 and ms_by_state.get(st, 0) == 0)
    no_building_states = sorted(states_ctx - states_with_rows)

    print("## state_context")
    print("count:", len(states_ctx))
    print()
    print("## Microsoft-backed rows")
    print("states with ≥1 Microsoft row:", len(ms_state_set))
    print("total Microsoft rows:", sum(ms_by_state.values()))
    print("per-state counts:")
    for st in sorted(ms_by_state.keys()):
        print(f"  {st}: {ms_by_state[st]}")
    print()
    print("## Synthetic bru-* rows (fallback)")
    print("total synthetic rows:", sum(syn_by_state.values()))
    print("states using synthetic fallback (have bru-* but no Microsoft rows):", syn_fallback_states)
    print("state_context states with zero buildings in catalog:", no_building_states)
    print()
    print("## Catalog totals")
    print("rows in buildings_catalog.csv:", sum(ms_by_state.values()) + sum(syn_by_state.values()))
    print()
    print("## Example Microsoft rows (up to 3 states)")
    for i, st in enumerate(sorted(examples_ms.keys())[:3]):
        r = examples_ms[st]
        print(f"  {st}: id={r.get('id')!r} roof_area_sqft={r.get('roof_area_sqft')!r}")


if __name__ == "__main__":
    main()
