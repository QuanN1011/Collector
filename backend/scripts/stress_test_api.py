"""
Basic load / stress smoke test for the RainUSE API.

Runs concurrent HTTP clients against /health, /buildings, and /top-prospects and prints
latency stats (ms) and error counts. Not a full benchmark suite—just sanity under parallel load.

Usage (API must be running)::

  cd backend
  export DATABASE_URL=...   # if testing with DB
  PYTHONPATH=. uvicorn main:app --host 127.0.0.1 --port 8000

  # another terminal:
  PYTHONPATH=. python scripts/stress_test_api.py --base-url http://127.0.0.1:8000
"""

from __future__ import annotations

import argparse
import statistics
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field

import httpx


@dataclass
class Result:
    path: str
    status: int
    ms: float


@dataclass
class RunStats:
    results: list[Result] = field(default_factory=list)
    errors: int = 0


def _one(client: httpx.Client, base: str, path: str) -> Result:
    """Single GET; returns Result with wall time in ms."""
    url = base.rstrip("/") + path
    t0 = time.perf_counter()
    try:
        r = client.get(url, timeout=120.0)
        ms = (time.perf_counter() - t0) * 1000
        return Result(path=path, status=r.status_code, ms=ms)
    except Exception as e:
        ms = (time.perf_counter() - t0) * 1000
        print(f"ERROR {path}: {e!r}", file=sys.stderr)
        return Result(path=path, status=0, ms=ms)


def _worker(base: str, paths: list[str], repeats: int) -> RunStats:
    out = RunStats()
    with httpx.Client() as client:
        for _ in range(repeats):
            for path in paths:
                res = _one(client, base, path)
                out.results.append(res)
                if res.status != 200:
                    out.errors += 1
    return out


def _percentile(vals: list[float], p: float) -> float:
    """Linear interpolation on sorted values (p in 0..100)."""
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


def main() -> None:
    parser = argparse.ArgumentParser(description="Basic API stress / load smoke test.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000", help="API root, no trailing slash issues handled")
    parser.add_argument("--workers", type=int, default=4, help="Concurrent worker threads")
    parser.add_argument("--repeats", type=int, default=25, help="Each worker runs each path this many times")
    parser.add_argument(
        "--paths",
        nargs="*",
        default=[
            "/health",
            "/buildings?state=TX",
            "/top-prospects?state=TX&limit=15",
        ],
        help="Paths to GET (relative to base URL)",
    )
    args = parser.parse_args()

    print(f"Target: {args.base_url}")
    print(f"Workers: {args.workers}, repeats per path per worker: {args.repeats}")
    print(f"Paths: {args.paths}")
    print("---")

    t0 = time.perf_counter()
    all_results: list[Result] = []
    total_errors = 0

    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futures = [
            ex.submit(_worker, args.base_url, list(args.paths), args.repeats) for _ in range(args.workers)
        ]
        for fut in as_completed(futures):
            st = fut.result()
            all_results.extend(st.results)
            total_errors += st.errors

    wall = time.perf_counter() - t0
    total_requests = len(all_results)
    rps = total_requests / wall if wall > 0 else 0

    by_path: dict[str, list[float]] = {}
    for r in all_results:
        if r.status == 200:
            by_path.setdefault(r.path, []).append(r.ms)

    print(f"Total requests: {total_requests} in {wall:.2f}s (~{rps:.1f} req/s)")
    print(f"Non-200 responses: {total_errors}")
    print("---")
    print("Latency (ms) for successful requests, by path:")
    for path in args.paths:
        vals = sorted(by_path.get(path, []))
        if not vals:
            print(f"  {path}: no successful samples")
            continue
        stdev = statistics.stdev(vals) if len(vals) > 1 else 0.0
        print(
            f"  {path}\n"
            f"    n={len(vals)}  min={min(vals):.1f}  max={max(vals):.1f}  "
            f"mean={statistics.mean(vals):.1f}  stdev={stdev:.1f}\n"
            f"    p50={_percentile(vals, 50):.1f}  p95={_percentile(vals, 95):.1f}  p99={_percentile(vals, 99):.1f}"
        )

    if total_errors > 0:
        sys.exit(1)
    print("OK (all HTTP 200)")


if __name__ == "__main__":
    main()
