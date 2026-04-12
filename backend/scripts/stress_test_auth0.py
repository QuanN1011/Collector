"""
Stress / load smoke tests related to Auth0 integration.

Two modes (run one or both):

1) **JWKS (Auth0-hosted)** — GET ``https://<AUTH0_DOMAIN>/.well-known/jwks.json``
   Exercises TLS + Auth0 CDN + JSON fetch. No secrets. Safe for moderate concurrency.

2) **Issue endpoint (your API)** — POST ``/api/keys/issue`` with ``Authorization: Bearer <id_token>``
   Exercises PyJWT/JWKS verification + DB writes in ``api_keys``. Requires a **fresh ID token**
   from the browser (short-lived). Many successful calls **rotate** the stored API key for that user.

Usage::

  cd backend
  . .venv/bin/activate
  export PYTHONPATH=.

  # Auth0 JWKS only (no token)
  python scripts/stress_test_auth0.py --jwks-only --auth0-domain dev-xxxx.us.auth0.com

  # API issue path (paste token from DevTools → Application or Network after login)
  export RAINUSE_ID_TOKEN='eyJ...'
  python scripts/stress_test_auth0.py --base-url http://127.0.0.1:8000

  # Both
  python scripts/stress_test_auth0.py --auth0-domain dev-xxxx.us.auth0.com --base-url http://127.0.0.1:8000
"""

from __future__ import annotations

import argparse
import os
import statistics
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from urllib.parse import urlparse

import httpx


@dataclass
class Result:
    label: str
    status: int
    ms: float


@dataclass
class RunStats:
    results: list[Result] = field(default_factory=list)
    errors: int = 0


def _percentile(vals: list[float], p: float) -> float:
    if not vals:
        return 0.0
    s = sorted(vals)
    n = len(s)
    if n == 1:
        return s[0]
    k = (n - 1) * (p / 100.0)
    lo = int(k)
    hi = min(lo + 1, n - 1)
    return s[lo] + (k - lo) * (s[hi] - s[lo])


def _worker_jwks(domain: str, repeats: int) -> RunStats:
    url = f"https://{domain.rstrip('/')}/.well-known/jwks.json"
    out = RunStats()
    with httpx.Client() as client:
        for _ in range(repeats):
            t0 = time.perf_counter()
            try:
                r = client.get(url, timeout=60.0)
                ms = (time.perf_counter() - t0) * 1000
                out.results.append(Result("jwks", r.status_code, ms))
                if r.status_code != 200:
                    out.errors += 1
            except Exception as e:
                ms = (time.perf_counter() - t0) * 1000
                print(f"ERROR jwks: {e!r}", file=sys.stderr)
                out.results.append(Result("jwks", 0, ms))
                out.errors += 1
    return out


def _worker_issue(base: str, token: str, repeats: int) -> RunStats:
    url = base.rstrip("/") + "/api/keys/issue"
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
    out = RunStats()
    with httpx.Client() as client:
        for _ in range(repeats):
            t0 = time.perf_counter()
            try:
                r = client.post(url, headers=headers, timeout=120.0)
                ms = (time.perf_counter() - t0) * 1000
                out.results.append(Result("issue", r.status_code, ms))
                if r.status_code != 200:
                    out.errors += 1
            except Exception as e:
                ms = (time.perf_counter() - t0) * 1000
                print(f"ERROR issue: {e!r}", file=sys.stderr)
                out.results.append(Result("issue", 0, ms))
                out.errors += 1
    return out


def _print_stats(label: str, results: list[Result], expect_status: int) -> int:
    ok = [r.ms for r in results if r.status == expect_status]
    bad = sum(1 for r in results if r.status != expect_status)
    print(f"\n=== {label} ===")
    print(f"Samples: {len(results)}  non-{expect_status}: {bad}")
    if not ok:
        print("  No successful samples.")
        return bad
    stdev = statistics.stdev(ok) if len(ok) > 1 else 0.0
    print(
        f"  Latency ms: n={len(ok)}  min={min(ok):.1f}  max={max(ok):.1f}  "
        f"mean={statistics.mean(ok):.1f}  stdev={stdev:.1f}\n"
        f"  p50={_percentile(ok, 50):.1f}  p95={_percentile(ok, 95):.1f}  p99={_percentile(ok, 99):.1f}"
    )
    return bad


def main() -> None:
    parser = argparse.ArgumentParser(description="Stress Auth0 JWKS and/or API key issue (JWT verify).")
    parser.add_argument("--auth0-domain", default=os.environ.get("AUTH0_DOMAIN", ""), help="Tenant domain (no https)")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000", help="Your API base URL")
    parser.add_argument("--workers", type=int, default=4, help="Concurrent worker threads per phase")
    parser.add_argument("--repeats", type=int, default=10, help="Each worker repeats this many requests per phase")
    parser.add_argument(
        "--jwks-only",
        action="store_true",
        help="Only fetch Auth0 JWKS (no POST /api/keys/issue)",
    )
    parser.add_argument(
        "--issue-only",
        action="store_true",
        help="Only POST /api/keys/issue (requires RAINUSE_ID_TOKEN)",
    )
    parser.add_argument(
        "--token",
        default=os.environ.get("RAINUSE_ID_TOKEN", ""),
        help="Auth0 ID token (or set RAINUSE_ID_TOKEN)",
    )
    args = parser.parse_args()

    do_jwks = not args.issue_only
    do_issue = not args.jwks_only

    if do_issue and not args.token.strip():
        print(
            "POST /api/keys/issue requires an ID token. After logging in to the app, copy the id_token\n"
            "  (DevTools → Network → authorized request, or Application storage) and run:\n"
            "  export RAINUSE_ID_TOKEN='eyJ...'\n"
            "Or:  python scripts/stress_test_auth0.py --token 'eyJ...' ...\n",
            file=sys.stderr,
        )
        if not do_jwks:
            sys.exit(1)

    if do_jwks and not args.auth0_domain.strip():
        print("Set --auth0-domain or AUTH0_DOMAIN in the environment.", file=sys.stderr)
        if not do_issue or not args.token.strip():
            sys.exit(1)
        do_jwks = False

    total_errors = 0

    if do_jwks:
        domain = args.auth0_domain.strip()
        print(f"JWKS: https://{domain}/.well-known/jwks.json")
        print(f"Workers: {args.workers}, repeats per worker: {args.repeats}")
        t0 = time.perf_counter()
        all_jwks: list[Result] = []
        with ThreadPoolExecutor(max_workers=args.workers) as ex:
            futs = [ex.submit(_worker_jwks, domain, args.repeats) for _ in range(args.workers)]
            for fut in as_completed(futs):
                st = fut.result()
                all_jwks.extend(st.results)
        wall = time.perf_counter() - t0
        print(f"Wall time: {wall:.2f}s (~{len(all_jwks) / wall:.1f} req/s)" if wall > 0 else "")
        total_errors += _print_stats("Auth0 JWKS", all_jwks, 200)

    if do_issue and args.token.strip():
        parsed = urlparse(args.base_url)
        if parsed.hostname in (None, ""):
            print("Invalid --base-url", file=sys.stderr)
            sys.exit(1)
        print(f"\nPOST {args.base_url.rstrip('/')}/api/keys/issue (JWT verify + DB)")
        print("Note: each 200 may rotate the api_keys row for this user.")
        t0 = time.perf_counter()
        all_issue: list[Result] = []
        with ThreadPoolExecutor(max_workers=args.workers) as ex:
            futs = [ex.submit(_worker_issue, args.base_url, args.token.strip(), args.repeats) for _ in range(args.workers)]
            for fut in as_completed(futs):
                st = fut.result()
                all_issue.extend(st.results)
        wall = time.perf_counter() - t0
        print(f"Wall time: {wall:.2f}s (~{len(all_issue) / wall:.1f} req/s)" if wall > 0 else "")
        total_errors += _print_stats("API issue", all_issue, 200)

    if total_errors > 0:
        print("\nSome requests failed.", file=sys.stderr)
        sys.exit(1)
    print("\nOK (all successful samples in expected class)")


if __name__ == "__main__":
    main()
