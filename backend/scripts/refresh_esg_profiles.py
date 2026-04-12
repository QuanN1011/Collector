"""
Refresh ``company_sustainability_profiles`` from the canonical CSV (idempotent upsert).

Implementation: ``services.esg_profile_sync.refresh_profiles_from_csv``.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

from env_load import load_backend_env

load_backend_env()

from services.esg_profile_sync import refresh_profiles_from_csv


def main() -> None:
    parser = argparse.ArgumentParser(description="Refresh ESG profiles from canonical CSV.")
    parser.add_argument(
        "--csv",
        type=Path,
        default=_BACKEND_ROOT / "data" / "company_sustainability_profiles.csv",
    )
    args = parser.parse_args()
    if not args.csv.is_file():
        print(f"ERROR: file not found: {args.csv}", file=sys.stderr)
        raise SystemExit(2)
    n = refresh_profiles_from_csv(args.csv)
    print(f"refresh_esg_profiles: upserted {n} row(s) from {args.csv}")


if __name__ == "__main__":
    main()
