"""
Orchestrate real-data ingestion (Microsoft footprints + optional Open-Meteo precipitation).

Examples::

  # 1) Footprints only (writes data/buildings_microsoft.csv)
  python scripts/ingest_real_data.py footprints --states Texas Arizona Pennsylvania \\
    --min-sqft 100000 --max-per-state 120

  # 2) Refresh state rainfall from Open-Meteo (keeps water $ from existing state_context.csv)
  python scripts/ingest_real_data.py precip --merge-water-from data/state_context.csv

  # 3) Run both then seed Postgres (requires DATABASE_URL)
  python scripts/ingest_real_data.py all --states Texas Arizona Pennsylvania \\
    --min-sqft 100000 --max-per-state 120

See docs/DATABASE_SEED_DATA.md for licenses and attribution.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = BACKEND_ROOT / "scripts"


def _run(cmd: list[str]) -> None:
    print("+", " ".join(cmd))
    subprocess.check_call(cmd, cwd=str(BACKEND_ROOT))


def cmd_footprints(args: argparse.Namespace) -> None:
    cmd = [
        sys.executable,
        str(SCRIPTS / "ingest_ms_buildings.py"),
        "--states",
        *args.states,
        "--min-sqft",
        str(args.min_sqft),
        "--max-per-state",
        str(args.max_per_state),
        "--output",
        str(args.output),
        "--cache-dir",
        str(args.cache_dir),
    ]
    if args.force_download:
        cmd.append("--force-download")
    _run(cmd)


def cmd_precip(args: argparse.Namespace) -> None:
    cmd = [
        sys.executable,
        str(SCRIPTS / "ingest_state_precip_open_meteo.py"),
        "--merge-water-from",
        str(args.merge_water_from),
        "--output",
        str(args.output),
        "--sleep-seconds",
        str(args.sleep_seconds),
    ]
    _run(cmd)


def cmd_all(args: argparse.Namespace) -> None:
    cmd_footprints(args)
    cmd_precip(args)


def main() -> None:
    parser = argparse.ArgumentParser(description="RainUSE real-data ingestion orchestrator.")
    sub = parser.add_subparsers(dest="command", required=True)

    p_fp = sub.add_parser("footprints", help="Download Microsoft US Building Footprints subset.")
    p_fp.add_argument("--states", nargs="+", required=True)
    p_fp.add_argument("--min-sqft", type=float, default=100_000.0)
    p_fp.add_argument("--max-per-state", type=int, default=150)
    p_fp.add_argument("--output", type=Path, default=BACKEND_ROOT / "data" / "buildings_microsoft.csv")
    p_fp.add_argument("--cache-dir", type=Path, default=BACKEND_ROOT / "data" / "cache" / "ms_footprints")
    p_fp.add_argument("--force-download", action="store_true")
    p_fp.set_defaults(func=cmd_footprints)

    p_pr = sub.add_parser("precip", help="Fetch state precipitation from Open-Meteo archive API.")
    p_pr.add_argument(
        "--merge-water-from",
        type=Path,
        default=BACKEND_ROOT / "data" / "state_context.csv",
    )
    p_pr.add_argument("--output", type=Path, default=BACKEND_ROOT / "data" / "state_context.csv")
    p_pr.add_argument("--sleep-seconds", type=float, default=0.35)
    p_pr.set_defaults(func=cmd_precip)

    p_all = sub.add_parser("all", help="Run footprints then precipitation.")
    p_all.add_argument("--states", nargs="+", required=True)
    p_all.add_argument("--min-sqft", type=float, default=100_000.0)
    p_all.add_argument("--max-per-state", type=int, default=150)
    p_all.add_argument(
        "--buildings-output",
        type=Path,
        default=BACKEND_ROOT / "data" / "buildings_microsoft.csv",
    )
    p_all.add_argument("--cache-dir", type=Path, default=BACKEND_ROOT / "data" / "cache" / "ms_footprints")
    p_all.add_argument("--force-download", action="store_true")
    p_all.add_argument(
        "--merge-water-from",
        type=Path,
        default=BACKEND_ROOT / "data" / "state_context.csv",
    )
    p_all.add_argument(
        "--state-context-output",
        type=Path,
        default=BACKEND_ROOT / "data" / "state_context.csv",
    )
    p_all.add_argument("--sleep-seconds", type=float, default=0.35)

    def _all_impl(ns: argparse.Namespace) -> None:
        cmd_footprints(
            argparse.Namespace(
                states=ns.states,
                min_sqft=ns.min_sqft,
                max_per_state=ns.max_per_state,
                output=ns.buildings_output,
                cache_dir=ns.cache_dir,
                force_download=ns.force_download,
            )
        )
        cmd_precip(
            argparse.Namespace(
                merge_water_from=ns.merge_water_from,
                output=ns.state_context_output,
                sleep_seconds=ns.sleep_seconds,
            )
        )

    p_all.set_defaults(func=_all_impl)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
