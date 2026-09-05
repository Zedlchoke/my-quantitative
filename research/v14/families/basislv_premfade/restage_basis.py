"""Fallback stager for the A9-F basis observables (I-lane obligation).

The A9-F staged bulk (76 entries, zero missing buckets, manifest sha256
``3867bdca...``) is the authority for this family; this lane loads it
READ-ONLY with per-file SHA-256 verification (fail-closed on mismatch) and
does NOT need to re-stage.  This script is the committed CONTINGENCY
required by the lane brief: IF the staged root is ever unavailable AND the
owner authorizes a re-stage, this script re-fetches the frozen 15m
conditioning observables for the 19 ranked names from the registered
keyless Binance public endpoints, writing ONLY inside this lane's own
worktree (``research/control/v14_run/i_family_1/restaged/`` -- gitignored
bulk; never committed), then re-emits a manifest in the A9-F schema.

A9F-OBS-5 / A9F-OBS-6 operational pattern, implemented (binding):
* forward pagination ONLY (discrepancy D3: backward ``endTime`` walks
  repeat the latest page and are invalid);
* ``limit=500`` per request; the endpoint intermittently answers HTTP 418
  (empty body) under serial pacing -- every request is retried up to 8
  attempts with a linear 20s backoff; a request still failing after the
  final attempt FAILS CLOSED (no silent gap);
* serial requests with a 0.55s sleep; no concurrency.

The frozen window: authorized window 2024-08-20T00:00:00Z..
2026-08-21T23:59:59.999Z, 15m buckets, 70272 expected buckets per symbol.

This script performs NETWORK FETCHES and is therefore NEVER run by the
test suite; it exists so the re-stage procedure is auditable code, not a
description.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_OUT_ROOT = HERE.parent / "i_family_1" / "restaged"

SYMBOLS = [
    "1000PEPEUSDT", "AAVEUSDT", "ACEUSDT", "ADAUSDT", "AVAXUSDT",
    "BCHUSDT", "BNBUSDT", "BOMEUSDT", "DOGEUSDT", "ENAUSDT",
    "ETHUSDT", "LINKUSDT", "NEARUSDT", "ONGUSDT", "SOLUSDT",
    "SUIUSDT", "WLDUSDT", "XRPUSDT", "ZECUSDT",
]
BUCKET_MS = 900_000
AUTHORIZED_START_MS = 1_724_112_000_000  # 2024-08-20T00:00:00Z
AUTHORIZED_LAST_OPEN_MS = 1_787_355_900_000  # 2026-08-21T23:45:00Z
EXPECTED_BUCKETS = (AUTHORIZED_LAST_OPEN_MS - AUTHORIZED_START_MS) // BUCKET_MS + 1
PAGE_LIMIT = 500
MAX_ATTEMPTS = 8
BACKOFF_SECONDS = 20.0
SERIAL_SLEEP_SECONDS = 0.55

BASIS_URL = "https://fapi.binance.com/futures/data/basis"
BASIS_PARAMS = "contractType=PERPETUAL&period=15m&limit={limit}&pair={pair}&startTime={start}&endTime={end}"


def fetch_with_backoff(url: str) -> list[dict]:
    """GET with the A9F-OBS-6 418 backoff-retry pattern (fail-closed)."""
    last_error = ""
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            with urllib.request.urlopen(url, timeout=30) as response:
                if response.status == 200:
                    return json.loads(response.read().decode("utf-8"))
                last_error = f"HTTP {response.status}"
        except Exception as exc:  # transient 418 / network noise
            last_error = repr(exc)
        time.sleep(BACKOFF_SECONDS * attempt)  # linear backoff
    raise RuntimeError(
        f"request failed after {MAX_ATTEMPTS} attempts (fail-closed): "
        f"{url} :: {last_error}"
    )


def stage_symbol_basis(symbol: str, out_root: Path) -> dict:
    """Forward-paginated basis-route staging for one symbol (D3-honoring)."""
    rows: dict[int, dict] = {}
    start = AUTHORIZED_START_MS
    requests = 0
    while start <= AUTHORIZED_LAST_OPEN_MS:
        end = min(start + (PAGE_LIMIT - 1) * BUCKET_MS, AUTHORIZED_LAST_OPEN_MS)
        url = f"{BASIS_URL}?{BASIS_PARAMS.format(limit=PAGE_LIMIT, pair=symbol, start=start, end=end)}"
        page = fetch_with_backoff(url)
        requests += 1
        for row in page:
            open_ms = int(row["timestamp"])
            rows[open_ms] = {
                "open_time_ms": open_ms,
                "futures_price": float(row["futuresPrice"]),
                "index_price": float(row["indexPrice"]),
                "basis": float(row["basis"]),
                "basis_rate": float(row["basisRate"]),
            }
        time.sleep(SERIAL_SLEEP_SECONDS)
        if not page:
            # Empty page inside the window: advance by the page span but the
            # zero-gap check below will fail-closed on the missing buckets.
            start = end + BUCKET_MS
            continue
        start = end + BUCKET_MS
    missing = [
        ms
        for ms in range(
            AUTHORIZED_START_MS, AUTHORIZED_LAST_OPEN_MS + BUCKET_MS, BUCKET_MS
        )
        if ms not in rows
    ]
    if missing:
        raise RuntimeError(
            f"{symbol}: {len(missing)} missing buckets after staging "
            "(fail-closed; first "
            f"{missing[0]}, last {missing[-1]})"
        )
    ordered = [rows[ms] for ms in sorted(rows)]
    out_dir = out_root / symbol
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{symbol}_basis_15m.parquet"
    import pandas as pd

    pd.DataFrame(ordered).to_parquet(out_path, index=False)
    return {
        "symbol": symbol,
        "rows": len(ordered),
        "expected_buckets": EXPECTED_BUCKETS,
        "missing_buckets": 0,
        "requests": requests,
        "file": str(out_path),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out-root",
        default=str(DEFAULT_OUT_ROOT),
        help="write root INSIDE this lane's worktree (never the A9-F tree)",
    )
    parser.add_argument(
        "--symbols", default="", help="comma-separated subset (default: all 19)"
    )
    args = parser.parse_args()
    out_root = Path(args.out_root).resolve()
    if "d2_a9f" in str(out_root) or "d2-a9f" in str(out_root):
        raise SystemExit("refusing to write into the A9-F lane tree (read-only)")
    wanted = args.symbols.split(",") if args.symbols else SYMBOLS
    summary = []
    for symbol in wanted:
        summary.append(stage_symbol_basis(symbol, out_root))
        print(f"staged {symbol}: {summary[-1]['rows']} rows", flush=True)
    (out_root / "restage_summary.json").write_text(
        json.dumps({"entries": summary, "schema": "v14_i_f1_restage_v1"}, indent=1),
        encoding="utf-8",
    )
    print(f"staged {len(summary)} symbols under {out_root}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
