"""
Download the SEC's public company ticker JSON and write a companies CSV for seeding.

Source: https://www.sec.gov/files/company_tickers.json (no API key; SEC requests a descriptive User-Agent).

This does not fetch filings or sustainability data—only company id, name, ticker, and CIK.

Usage::

  python scripts/ingest_sec_company_tickers.py --limit 150 --output data/companies_from_sec.csv

Pair with empty sustainability/doc CSV headers if you are not hand-curating ESG rows::

  printf 'company_id,has_esg_report,has_water_target,has_science_based_target,climate_risk_score,esg_alignment_score\\n' > data/company_sustainability_profiles.empty.csv
  printf 'id,company_id,document_type,filing_date,source_url,excerpt\\n' > data/company_documents.empty.csv

  python scripts/seed_database.py --companies-csv data/companies_from_sec.csv \\
    --company-sustainability-csv data/company_sustainability_profiles.empty.csv \\
    --company-documents-csv data/company_documents.empty.csv \\
    --buildings-csv data/buildings_microsoft.csv
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import httpx

BACKEND_ROOT = Path(__file__).resolve().parent.parent
SEC_URL = "https://www.sec.gov/files/company_tickers.json"
SEC_HEADERS = {
    "User-Agent": "RainUSE-Nexus/1.0 (contact: https://github.com/)",
    "Accept": "application/json",
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch SEC company_tickers.json → companies CSV.")
    parser.add_argument("--output", type=Path, default=BACKEND_ROOT / "data" / "companies_from_sec.csv")
    parser.add_argument("--limit", type=int, default=200, help="Max rows to write (SEC file has ~10k).")
    args = parser.parse_args()

    with httpx.Client(headers=SEC_HEADERS, timeout=60.0, follow_redirects=True) as client:
        r = client.get(SEC_URL)
        r.raise_for_status()
        payload = r.json()

    rows_out: list[dict[str, str]] = []

    def _append_row(cik: str, ticker: str, title: str) -> None:
        if len(rows_out) >= args.limit:
            return
        cik = str(cik).strip()
        ticker = (ticker or "").strip()
        title = (title or "").strip()
        if not cik or not title:
            return
        cid = f"sec-{cik.zfill(10)}"
        rows_out.append(
            {
                "id": cid,
                "company_name": title.replace("\n", " ")[:500],
                "ticker": ticker or "",
                "cik": cik,
                "industry": "",
                "website": "",
                "hq_state": "",
            }
        )

    # Format A: {"fields":["cik_str","ticker","title"],"data":[[...], ...]}
    if isinstance(payload, dict) and "data" in payload and "fields" in payload:
        fields = list(payload["fields"])
        try:
            i_cik = fields.index("cik_str")
            i_tk = fields.index("ticker")
            i_tt = fields.index("title")
        except ValueError:
            i_cik, i_tk, i_tt = 0, 1, 2
        for row in payload["data"]:
            if len(rows_out) >= args.limit:
                break
            _append_row(str(row[i_cik]), str(row[i_tk]), str(row[i_tt]))
    else:
        # Format B: {"0": {"cik_str": ..., "ticker": "...", "title": "..."}, ...}
        items = payload.items() if isinstance(payload, dict) else []
        for _k, row in sorted(items, key=lambda kv: int(kv[0]) if str(kv[0]).isdigit() else 0):
            if len(rows_out) >= args.limit:
                break
            if not isinstance(row, dict):
                continue
            _append_row(str(row.get("cik_str", "")), str(row.get("ticker", "")), str(row.get("title", "")))

    args.output.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["id", "company_name", "ticker", "cik", "industry", "website", "hq_state"]
    with args.output.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows_out)

    print(f"Wrote {len(rows_out)} companies → {args.output} (source: {SEC_URL})")


if __name__ == "__main__":
    main()
