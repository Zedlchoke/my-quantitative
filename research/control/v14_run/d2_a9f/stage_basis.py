"""A9-F T2: minimal staging of the frozen 15m basis conditioning observables.

Stages, per universe symbol (19 ranked names; BTCUSDT excluded per the
proposals), the four routes cited by the four basis-axis proposals at the
frozen 15m granularity over the authorized window
2024-08-20T00:00Z..2026-08-21T23:59:59.999Z (last fully-inside 15m bucket
opens 2026-08-21T23:45Z):

* premiumIndexKlines (symbol=)  -- A6 primary signal; A5 cross-check;
* markPriceKlines    (symbol=)  -- A5-WIDTHGATE numerator; A6 cross-check;
* indexPriceKlines   (pair=)    -- A5-WIDTHGATE denominator (D2: pair=);
                                  A6-PREMREV causal-control signal;
* /futures/data/basis (pair=, contractType=PERPETUAL, period=15m)
                                -- A5-PREMFADE primary signal (fields
                                   futuresPrice, indexPrice, basisRate).

Forward startTime pagination ONLY.  Keyless public GETs against
https://fapi.binance.com; >= 0.55s sleep between calls.  Deterministic and
re-runnable: a (symbol, route) is skipped only when its file already exists
and matches the expected complete bucket grid; otherwise it is re-fetched in
full.  Bulk data are written machine-local under staged/ (gitignored); the
manifest (row counts, first/last open, sha256, gaps) is the committed
authority record.

No PnL, no positions, no returns.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

BASE = "https://fapi.binance.com"
HERE = Path(__file__).resolve().parent
STAGED = HERE / "staged"
STAGED.mkdir(parents=True, exist_ok=True)

SLEEP_SECONDS = 0.55
BASIS_SLEEP_SECONDS = 0.9        # /futures/data/* endpoints are WAF-sensitive
BASIS_RETRY_SLEEP = 20.0         # backoff on transient HTTP 418 (empty body)
BASIS_MAX_ATTEMPTS = 8
LIMIT_KLINES = 1500          # documented kline max
LIMIT_BASIS = 500            # documented /futures/data/basis max
BUCKET_SECONDS = 900

WINDOW_START_MS = 1724112000000  # 2024-08-20T00:00:00Z (authorized start)
WINDOW_END_MS = 1787356799999    # 2026-08-21T23:59:59.999Z (authorized end)
BUCKET_MS = BUCKET_SECONDS * 1000
LAST_BUCKET_OPEN_MS = (WINDOW_END_MS // BUCKET_MS) * BUCKET_MS  # 2026-08-21T23:45Z
EXPECTED_BUCKETS = (LAST_BUCKET_OPEN_MS - WINDOW_START_MS) // BUCKET_MS + 1

UNIVERSE = [
    "1000PEPEUSDT", "AAVEUSDT", "ACEUSDT", "ADAUSDT", "AVAXUSDT",
    "BCHUSDT", "BNBUSDT", "BOMEUSDT", "DOGEUSDT", "ENAUSDT",
    "ETHUSDT", "LINKUSDT", "NEARUSDT", "ONGUSDT", "SOLUSDT",
    "SUIUSDT", "WLDUSDT", "XRPUSDT", "ZECUSDT",
]

ROUTES = {
    "premium_klines": {"path": "/fapi/v1/premiumIndexKlines", "param": "symbol", "limit": LIMIT_KLINES},
    "mark_klines": {"path": "/fapi/v1/markPriceKlines", "param": "symbol", "limit": LIMIT_KLINES},
    "index_klines": {"path": "/fapi/v1/indexPriceKlines", "param": "pair", "limit": LIMIT_KLINES},
    "basis": {"path": "/futures/data/basis", "param": "pair", "limit": LIMIT_BASIS},
}

PROGRESS_PATH = HERE / "staged" / "_progress.json"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def http_get_json(path: str, params: dict, *, max_attempts: int = 1, retry_sleep: float = 0.0):
    """GET with backoff on transient HTTP 418/429 and transport errors."""
    url = BASE + path + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (research-staging)"})
    attempt = 0
    while True:
        attempt += 1
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                return resp.status, json.loads(resp.read().decode("utf-8")), url
        except urllib.error.HTTPError as exc:
            if exc.code in (418, 429, 500, 502, 503, 504) and attempt < max_attempts:
                time.sleep(retry_sleep * attempt)
                continue
            return exc.code, None, url
        except (urllib.error.URLError, TimeoutError, ConnectionError, OSError) as exc:
            if attempt < max_attempts:
                time.sleep(retry_sleep * attempt)
                continue
            raise RuntimeError(f"transport failure after {attempt} attempts: {exc} url={url}") from exc


def fetch_route(symbol: str, route: str) -> list[list]:
    """Fetch all buckets for (symbol, route) by forward startTime pagination."""
    cfg = ROUTES[route]
    param_key = cfg["param"]
    rows: list[list] = []
    start = WINDOW_START_MS
    requests = 0
    page_attempt = 0
    while start <= LAST_BUCKET_OPEN_MS:
        params = {
            param_key: symbol,
            "interval": "15m",
            "limit": cfg["limit"],
            "startTime": start,
            "endTime": WINDOW_END_MS,
        }
        if route == "basis":
            params = {
                param_key: symbol,
                "contractType": "PERPETUAL",
                "period": "15m",
                "limit": cfg["limit"],
                "startTime": start,
                "endTime": WINDOW_END_MS,
            }
        status, payload, url = http_get_json(
            cfg["path"],
            params,
            max_attempts=BASIS_MAX_ATTEMPTS if route == "basis" else 5,
            retry_sleep=BASIS_RETRY_SLEEP,
        )
        requests += 1
        # /futures/data/* intermittently returns HTTP 200 with a JSON error
        # OBJECT instead of a row list -- treat as transient and retry.
        if route == "basis" and status == 200 and not isinstance(payload, list):
            if page_attempt < BASIS_MAX_ATTEMPTS:
                page_attempt += 1
                time.sleep(BASIS_RETRY_SLEEP * page_attempt)
                continue
            raise RuntimeError(
                f"{route}|{symbol}: HTTP 200 non-list payload after retries at start={start}: {str(payload)[:200]}"
            )
        if status != 200 or not isinstance(payload, list):
            raise RuntimeError(f"{route}|{symbol}: HTTP {status} at start={start} url={url}")
        if not payload:
            break
        for row in payload:
            open_ms = int(row[0]) if isinstance(row, list) else int(row["timestamp"])
            if open_ms < start:  # defensive: stale/duplicate page (D3 pattern)
                continue
            rows.append(row)
        last_open = int(payload[-1][0]) if isinstance(payload[-1], list) else int(payload[-1]["timestamp"])
        nxt = last_open + BUCKET_SECONDS * 1000
        if nxt <= start:  # no forward progress; refuse (would loop forever)
            raise RuntimeError(f"{route}|{symbol}: pagination stalled at {last_open}")
        start = nxt
        page_attempt = 0
        time.sleep(SLEEP_SECONDS if route != "basis" else BASIS_SLEEP_SECONDS)
    return rows, requests


def normalize_rows(route: str, rows: list) -> dict[str, list]:
    """Project raw rows into typed columns keyed by bucket open time."""
    if route == "basis":
        out: dict[str, list] = {
            "open_time_ms": [], "futures_price": [], "index_price": [],
            "basis": [], "basis_rate": [],
        }
        for row in rows:
            out["open_time_ms"].append(int(row["timestamp"]))
            out["futures_price"].append(float(row["futuresPrice"]))
            out["index_price"].append(float(row["indexPrice"]))
            out["basis"].append(float(row["basis"]))
            out["basis_rate"].append(float(row["basisRate"]))
        return out
    # kline routes: [openTime, open, high, low, close, ...]
    key = {"premium_klines": "premium_close", "mark_klines": "mark_close", "index_klines": "index_close"}[route]
    out = {"open_time_ms": [], key: []}
    for row in rows:
        out["open_time_ms"].append(int(row[0]))
        out[key].append(float(row[4]))
    return out


def write_parquet(route: str, symbol: str, cols: dict[str, list]) -> str:
    arrays = [pa.array(cols[name], type=pa.int64() if name == "open_time_ms" else pa.float64())
              for name in cols]
    table = pa.table(arrays, names=list(cols))
    target = STAGED / f"{symbol}_{route}_15m.parquet"
    pq.write_table(table, target)
    return str(target)


def gap_report(open_times: list[int]) -> dict:
    grid = [WINDOW_START_MS + i * BUCKET_SECONDS * 1000 for i in range(EXPECTED_BUCKETS)]
    have = set(open_times)
    missing = [t for t in grid if t not in have]
    dupes = len(open_times) - len(have)
    return {
        "expected_buckets": EXPECTED_BUCKETS,
        "missing_buckets": len(missing),
        "missing_first_utc": (
            datetime.fromtimestamp(missing[0] / 1000, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            if missing else None
        ),
        "missing_last_utc": (
            datetime.fromtimestamp(missing[-1] / 1000, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            if missing else None
        ),
        "duplicate_opens": dupes,
    }


def complete(route: str, symbol: str) -> bool:
    """Re-run determinism: skip only a file already covering the full grid."""
    path = STAGED / f"{symbol}_{route}_15m.parquet"
    if not path.exists():
        return False
    table = pq.read_table(path)
    opens = table.column("open_time_ms").to_pylist()
    info = gap_report(opens)
    return (
        info["missing_buckets"] == 0
        and info["duplicate_opens"] == 0
        and len(opens) == EXPECTED_BUCKETS
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--routes",
        default="premium_klines,mark_klines,index_klines,basis",
        help="comma-separated subset of routes to stage (skips complete pairs)",
    )
    args = parser.parse_args()
    wanted = [r.strip() for r in args.routes.split(",") if r.strip()]
    unknown = [r for r in wanted if r not in ROUTES]
    if unknown:
        raise SystemExit(f"unknown routes: {unknown}")

    entries: dict[str, dict] = {}
    errors: dict[str, str] = {}
    total_requests = 0
    for symbol in UNIVERSE:
        for route in wanted:
            if complete(route, symbol):
                print(f"[{utc_now_iso()}] skip complete {route}|{symbol}", flush=True)
            else:
                print(f"[{utc_now_iso()}] fetching {route}|{symbol}", flush=True)
                try:
                    raw, requests = fetch_route(symbol, route)
                except Exception as exc:  # keep staging the remaining symbols
                    errors[f"{route}|{symbol}"] = f"{type(exc).__name__}: {exc}"
                    print(f"[{utc_now_iso()}] ERROR {route}|{symbol}: {exc}", flush=True)
                    continue
                total_requests += requests
                cols = normalize_rows(route, raw)
                write_parquet(route, symbol, cols)
            path = STAGED / f"{symbol}_{route}_15m.parquet"
            table = pq.read_table(path)
            opens = table.column("open_time_ms").to_pylist()
            info = gap_report(opens)
            data = path.read_bytes()
            entry = {
                "file": str(path),
                "sha256": hashlib.sha256(data).hexdigest(),
                "bytes": len(data),
                "rows": len(opens),
                "first_open_utc": datetime.fromtimestamp(opens[0] / 1000, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "last_open_utc": datetime.fromtimestamp(opens[-1] / 1000, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                **info,
            }
            entries[f"{route}|{symbol}"] = entry
            print(
                f"[{utc_now_iso()}] staged {route}|{symbol}: rows={entry['rows']} "
                f"missing={entry['missing_buckets']} dupes={entry['duplicate_opens']}",
                flush=True,
            )

    manifest = {
        "schema": "v14_d2_a9f_staged_basis_manifest_v1",
        "cycle": "CRYPTO-V14",
        "producer_role": "A9-F",
        "generated_utc": utc_now_iso(),
        "authorized_window_utc": ["2024-08-20T00:00:00Z", "2026-08-21T23:59:59.999Z"],
        "bucket_seconds": BUCKET_SECONDS,
        "expected_buckets_per_symbol": EXPECTED_BUCKETS,
        "universe": UNIVERSE,
        "routes_staged_this_run": wanted,
        "http_requests_this_run": total_requests,
        "errors_this_run": errors,
        "routes": {
            "premium_klines": "/fapi/v1/premiumIndexKlines symbol= (A6 primary; A5 cross-check)",
            "mark_klines": "/fapi/v1/markPriceKlines symbol= (WIDTHGATE numerator)",
            "index_klines": "/fapi/v1/indexPriceKlines pair= (D2; WIDTHGATE denominator; PREMREV control)",
            "basis": "/futures/data/basis pair= contractType=PERPETUAL period=15m (PREMFADE primary; D3 forward pagination only)",
        },
        "keyless_public_endpoints_only": True,
        "sleep_seconds": SLEEP_SECONDS,
        "entries": entries,
        "notes": [
            "bulk parquet files are machine-local under staged/ and gitignored; this manifest is the committed authority record",
            "re-runnable: (symbol, route) pairs already covering the full grid are skipped",
        ],
    }
    with open(HERE / "staged_basis_manifest.json", "w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=1, sort_keys=True)
        handle.write("\n")
    print(f"DONE staged entries={len(entries)}")


if __name__ == "__main__":
    main()
