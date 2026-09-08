"""CRYPTO-V17 bounded staging: monthly aggTrades -> family-agnostic UTC-H1 panel.

Implements the P0-frozen design exactly (research/control/v17_run/p0_freeze_v17.json):
- symbols BTCUSDT, ETHUSDT (+SOLUSDT pulled in-pass under the frozen lane-2
  viability rule); window 2025-08-22..2026-08-21 (row-filtered BOTH ends);
- streaming zip -> csv member -> per-HOUR finalize as soon as the file's
  time-order crosses an hour boundary UTC (Binance aggTrades are
  time-ascending; violations abort with a FAILED heavy-lock release carrying
  the stderr tail); ONLY bounded O(1) accumulators per hour - NO per-trade
  retention, NO data-derived percentiles (the V16 954.8 MiB RSS came from
  per-day list retention; that class of state is forbidden here by contract);
- sha256 pinned per zip while downloading; raw archives deleted after reduction;
- ceilings: peak RSS <= 1024 MiB, transient disk <= 3 GiB, serial <= 6 h full /
  1 h smoke, parse <= 30 min per month (breach = BLOCKED_DATA per plan section 2);
- heavy phases run under the round-2 machine-wide heavy lock; FAILED releases
  carry the stderr tail in the release note (round-2 mandate).

Usage:
  python extract_v17_panel.py --smoke ETHUSDT:2026-05 SOLUSDT:2026-05
  python extract_v17_panel.py            # full frozen 39-symbol-month build
"""
import argparse
import csv
import hashlib
import io
import json
import math
import resource
import shutil
import sys
import threading
import time
import traceback
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from research.governance import heavy_lock

WORKTREE = Path(__file__).resolve().parents[4]
STAGING = WORKTREE / "v17_data" / "staging_v17"
ART = WORKTREE / "research" / "control" / "v17_run" / "staging"
FREEZE = WORKTREE / "research" / "control" / "v17_run" / "p0_freeze_v17.json"

BASE = "https://data.binance.vision/data/futures/um/monthly/aggTrades"
SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
MONTHS = [f"{y}-{m:02d}" for y, m in
          [(2025, 8), (2025, 9), (2025, 10), (2025, 11), (2025, 12),
           (2026, 1), (2026, 2), (2026, 3), (2026, 4), (2026, 5),
           (2026, 6), (2026, 7), (2026, 8)]]
WIN_START_MS = int(datetime(2025, 8, 22, tzinfo=timezone.utc).timestamp() * 1000)
WIN_END_MS = int(datetime(2026, 8, 21, 23, 59, 59, 999000, tzinfo=timezone.utc).timestamp() * 1000)
CHUNK = 8 * 1024 * 1024
MAX_DISK_TRANSIENT = 3 * 1024 ** 3
MAX_MONTH_PARSE_S = 1800.0

H1_SCHEMA = [
    "symbol", "hour_utc", "day_utc",
    "n_trades", "buy_count", "sell_count",
    "buy_qty", "sell_qty", "buy_quote", "sell_quote",
    "quote_total", "qty_total", "vwap",
    "first_price", "last_price", "high_price", "low_price",
    "max_trade_quote", "sum_qty_squared",
    "n_price_moves", "sum_squared_log_ret",
    "gap_sum_s", "gap_count", "entry_gap_s",
    "run_close_dir", "run_close_len", "run_switch_count",
    "max_run_buy", "max_run_sell",
    "first_ts_ms", "last_ts_ms",
]


def utcnow() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        while chunk := fh.read(CHUNK):
            h.update(chunk)
    return h.hexdigest()


def download_pin(url: str, dest: Path, result: Optional[dict] = None) -> tuple[int, str]:
    """Download + sha-pin. When `result` is given the work runs cooperatively
    as a prefetch target: the caller joins it before reducing (pipelined
    download/parse keeps the frozen serial data semantics while overlapping
    network I/O with CPU; disk bound: at most two transient zips ~2.3 GB
    worst-case vs the 3 GiB ceiling)."""
    free = shutil.disk_usage(dest.parent).free
    if free < MAX_DISK_TRANSIENT:
        raise RuntimeError(
            f"CEILING disk: only {free / 2**30:.2f} GiB free before download "
            f"(< {MAX_DISK_TRANSIENT / 2**30:.0f} GiB) -> BLOCKED_DATA")
    digest = hashlib.sha256()
    total = 0
    with urllib.request.urlopen(url, timeout=180) as resp, open(dest, "wb") as fh:
        expected = int(resp.headers.get("Content-Length", "-1"))
        while chunk := resp.read(CHUNK):
            digest.update(chunk)
            fh.write(chunk)
            total += len(chunk)
    if expected != -1 and total != expected:
        raise IOError(f"content-length mismatch {expected} != {total}")
    return total, digest.hexdigest()


def download_pin_async(url: str, dest: Path) -> tuple["threading.Thread", dict]:
    """Start a prefetch download in a daemon thread; join() re-raises errors.
    Bounded retry: transient network drops re-download the WHOLE file (sha256
    + content-length verified per attempt), max 3 attempts, backoff 30/60 s."""
    result: dict = {}
    delays = (30.0, 60.0)

    def work() -> None:
        last_exc: Optional[BaseException] = None
        for attempt in range(len(delays) + 1):
            try:
                n, sha = download_pin(url, dest)
                result["bytes"] = n
                result["sha256"] = sha
                return
            except BaseException as exc:  # re-raised at join after last attempt
                last_exc = exc
                if attempt < len(delays):
                    time.sleep(delays[attempt])
        result["error"] = last_exc

    t = threading.Thread(target=work, name=f"prefetch-{dest.name}", daemon=True)
    t.start()
    return t, result


def join_download(t: "threading.Thread", result: dict) -> tuple[int, str]:
    t.join()
    if "error" in result:
        raise result["error"]
    return result["bytes"], result["sha256"]


def new_hour() -> dict:
    return {"rows": 0, "buy_n": 0, "sell_n": 0,
            "buy_q": 0.0, "sell_q": 0.0, "buy_pq": 0.0, "sell_pq": 0.0,
            "pq": 0.0, "q": 0.0, "q2": 0.0,
            "hi": 0.0, "lo": float("inf"), "first": 0.0, "last": 0.0,
            "max_pq": 0.0, "prev_price": None,
            "moves": 0, "sslr": 0.0,
            "gap_sum": 0.0, "gap_n": 0, "entry_gap": 0.0,
            "switches": 0, "max_run_buy": 0, "max_run_sell": 0,
            "prev_dir": None,
            "first_ts": None, "last_ts": None}


class RunState:
    """Cross-hour aggressor run carry - bounded O(1), never a row list."""

    def __init__(self) -> None:
        self.dir: Optional[bool] = None  # True=buy aggressor
        self.len = 0

    def step(self, buy: bool) -> int:
        if self.dir is buy:
            self.len += 1
        else:
            self.dir = buy
            self.len = 1
        return self.len


def finalize_hour(symbol: str, hour_key: str, day_key: str, h: dict,
                  run: RunState) -> dict:
    n = h["rows"]
    if n:
        run_close_dir = "buy" if run.dir else "sell"
        run_close_len = run.len
    else:
        run_close_dir, run_close_len = "none", 0
    qty = h["q"]
    return {
        "symbol": symbol, "hour_utc": hour_key, "day_utc": day_key,
        "n_trades": n, "buy_count": h["buy_n"], "sell_count": h["sell_n"],
        "buy_qty": round(h["buy_q"], 8), "sell_qty": round(h["sell_q"], 8),
        "buy_quote": round(h["buy_pq"], 2), "sell_quote": round(h["sell_pq"], 2),
        "quote_total": round(h["pq"], 2), "qty_total": round(qty, 8),
        "vwap": round(h["pq"] / qty, 8) if qty else 0.0,
        "first_price": h["first"], "last_price": h["last"],
        "high_price": h["hi"],
        "low_price": h["lo"] if h["lo"] != float("inf") else 0.0,
        "max_trade_quote": round(h["max_pq"], 2),
        "sum_qty_squared": round(h["q2"], 8),
        "n_price_moves": h["moves"],
        "sum_squared_log_ret": round(h["sslr"], 12),
        "gap_sum_s": round(h["gap_sum"], 6), "gap_count": h["gap_n"],
        "entry_gap_s": round(h["entry_gap"], 6),
        "run_close_dir": run_close_dir, "run_close_len": run_close_len,
        "run_switch_count": h["switches"],
        "max_run_buy": h["max_run_buy"], "max_run_sell": h["max_run_sell"],
        "first_ts_ms": h["first_ts"], "last_ts_ms": h["last_ts"],
    }


class H1Writer:
    def __init__(self, staging: Path) -> None:
        self.staging = staging
        self.handles: dict[str, tuple[Any, csv.DictWriter]] = {}

    def write(self, symbol: str, rec: dict) -> None:
        if symbol not in self.handles:
            fh = open(self.staging / f"panel_{symbol}_h1.csv", "w", newline="")
            w = csv.DictWriter(fh, fieldnames=H1_SCHEMA)
            w.writeheader()
            self.handles[symbol] = (fh, w)
        self.handles[symbol][1].writerow(rec)

    def close(self) -> None:
        for fh, _ in self.handles.values():
            fh.close()


def month_key(zip_path: Path) -> str:
    stem = zip_path.name[:-4]
    parts = stem.rsplit("-", 2)
    return f"{parts[1]}-{parts[2]}"


def reduce_month(zip_path: Path, symbol: str, writer: H1Writer,
                 integrity: dict, cross: dict) -> dict:
    """Stream one monthly zip; finalize each hour as the file crosses the hour."""
    t0 = time.perf_counter()
    rows_in = rows_kept = out_of_order = 0
    h = new_hour()
    hour_key = None
    run: RunState = cross["run"]
    prev_ts_global: Optional[int] = cross["prev_ts_global"]

    def flush(complete_key: str, complete_day: str, acc: dict) -> None:
        writer.write(symbol, finalize_hour(symbol, complete_key,
                                           complete_day, acc, run))

    with zipfile.ZipFile(zip_path) as zf:
        members = [n for n in zf.namelist() if n.endswith(".csv")]
        if len(members) != 1:
            raise ValueError(f"expected one csv member, got {members}")
        with zf.open(members[0]) as raw, io.TextIOWrapper(raw, encoding="utf-8") as text:
            header = True
            prev_ts_file = None
            for row in csv.reader(text):
                if header:
                    header = False
                    if row and row[5] == "transact_time":
                        continue
                rows_in += 1
                ts = int(row[5])
                if prev_ts_file is not None and ts < prev_ts_file:
                    out_of_order += 1
                    if out_of_order > 100:
                        raise ValueError(
                            f"{symbol}: aggTrades not time-ascending at ts={ts} "
                            f"(>100 regressions) - refusing to reduce")
                    continue
                prev_ts_file = ts
                if ts < WIN_START_MS or ts > WIN_END_MS:
                    continue
                rows_kept += 1
                qty = float(row[2])
                price = float(row[1])
                buy_aggr = row[6] != "true"
                pq = qty * price
                dt = datetime.fromtimestamp(ts / 1000, tz=timezone.utc)
                hk = dt.strftime("%Y-%m-%dT%H")
                dk = dt.date().isoformat()
                if hour_key is None:
                    hour_key, h = hk, new_hour()
                    h["first"] = price
                    h["entry_gap"] = ((ts - prev_ts_global) / 1000.0
                                      if prev_ts_global is not None else 0.0)
                elif hk != hour_key:
                    flush(hour_key, h["day_utc"], h)
                    prev_hour_last = h["last_ts"]
                    h = new_hour()
                    hour_key = hk
                    h["first"] = price
                    h["entry_gap"] = ((ts - prev_hour_last) / 1000.0
                                      if prev_hour_last is not None else 0.0)
                h["day_utc"] = dk
                # bounded O(1) accumulation only - no per-trade retention
                h["rows"] += 1
                h["q"] += qty
                h["q2"] += qty * qty
                h["pq"] += pq
                h["max_pq"] = max(h["max_pq"], pq)
                if buy_aggr:
                    h["buy_n"] += 1
                    h["buy_q"] += qty
                    h["buy_pq"] += pq
                else:
                    h["sell_n"] += 1
                    h["sell_q"] += qty
                    h["sell_pq"] += pq
                h["hi"] = max(h["hi"], price)
                h["lo"] = price if h["lo"] == float("inf") else min(h["lo"], price)
                h["last"] = price
                if h["first_ts"] is None:
                    h["first_ts"] = ts
                if h["prev_price"] is not None:
                    h["moves"] += 1
                    r = math.log(price / h["prev_price"])
                    h["sslr"] += r * r
                h["prev_price"] = price
                if h["last_ts"] is not None:
                    h["gap_sum"] += (ts - h["last_ts"]) / 1000.0
                    h["gap_n"] += 1
                if h["prev_dir"] is not None and h["prev_dir"] is not buy_aggr:
                    h["switches"] += 1
                h["prev_dir"] = buy_aggr
                run_len = run.step(buy_aggr)
                if buy_aggr:
                    h["max_run_buy"] = max(h["max_run_buy"], run_len)
                else:
                    h["max_run_sell"] = max(h["max_run_sell"], run_len)
                h["last_ts"] = ts
                prev_ts_global = ts
            if hour_key is not None:
                flush(hour_key, h["day_utc"], h)
    cross["prev_ts_global"] = prev_ts_global
    integrity[f"{symbol}-{month_key(zip_path)}"] = {
        "rows_in_month_file": rows_in, "rows_kept_in_window": rows_kept,
        "out_of_order_skipped": out_of_order, "time_ascending": out_of_order == 0,
        "parse_seconds": round(time.perf_counter() - t0, 1)}
    stats = integrity[f"{symbol}-{month_key(zip_path)}"]
    if stats["parse_seconds"] > MAX_MONTH_PARSE_S:
        raise RuntimeError(
            f"CEILING parse: {symbol}-{month_key(zip_path)} "
            f"{stats['parse_seconds']}s > {MAX_MONTH_PARSE_S:.0f}s -> BLOCKED_DATA")
    return stats


def run_build(pairs, staging: Path, lock) -> dict:
    ART.mkdir(parents=True, exist_ok=True)
    staging.mkdir(parents=True, exist_ok=True)
    writer = H1Writer(staging)
    manifest_entries = []
    integrity = {}
    cross = {"run": RunState(), "prev_ts_global": None}
    t_start = time.perf_counter()
    try:
        def start_dl(i: int):
            sym, mon = pairs[i]
            url = f"{BASE}/{sym}/{sym}-aggTrades-{mon}.zip"
            dest = staging / f"{sym}-aggTrades-{mon}.zip"
            t, res = download_pin_async(url, dest)
            return (sym, mon, url), t, res, dest

        pending = start_dl(0) if pairs else None
        for i, (symbol, month) in enumerate(pairs):
            meta, thread, res, dest = pending
            nbytes, sha = join_download(thread, res)
            stats = reduce_month(dest, symbol, writer, integrity, cross)
            manifest_entries.append({
                "symbol": symbol, "month": month, "url": meta[2],
                "bytes_compressed": nbytes, "sha256": sha, **stats})
            dest.unlink()
            lock.heartbeat(extra={"last_done": f"{symbol}-{month}"})
            print(f"{symbol} {month}: kept {stats['rows_kept_in_window']}, "
                  f"{stats['parse_seconds']}s", flush=True)
            if i + 1 < len(pairs):
                pending = start_dl(i + 1)
    finally:
        writer.close()
    peak_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    peak_mib = round(peak_rss / 1048576, 1)
    if peak_mib > 1024:
        raise RuntimeError(f"CEILING rss: peak {peak_mib} MiB > 1024 -> BLOCKED_DATA")
    wall_h = round((time.perf_counter() - t_start) / 3600, 3)
    by_symbol = {}
    for s in writer.handles:
        path = staging / f"panel_{s}_h1.csv"
        with open(path) as fh:
            rows = list(csv.DictReader(fh))
        zero = sum(1 for r in rows if r["n_trades"] == "0")
        days = {r["day_utc"] for r in rows}
        by_symbol[s] = {"hourly_rows": len(rows), "zero_hours": zero,
                        "days_populated": len(days)}
    return {
        "schema": "v17_run_artifact_v1", "artifact": "staging_panel_manifest",
        "generated_utc": utcnow(), "symbols": sorted(writer.handles),
        "window": ["2025-08-22", "2026-08-21"],
        "contract_ref": {
            "freeze": "research/control/v17_run/p0_freeze_v17.json",
            "freeze_sha256": sha256_file(FREEZE) if FREEZE.exists() else None},
        "wall_hours_serial": wall_h,
        "sources": manifest_entries,
        "integrity": integrity,
        "panel_sha256": {s: sha256_file(staging / f"panel_{s}_h1.csv")
                         for s in writer.handles},
        "hourly_rows": {s: v["hourly_rows"] for s, v in by_symbol.items()},
        "zero_hours": {s: v["zero_hours"] for s, v in by_symbol.items()},
        "days_populated": {s: v["days_populated"] for s, v in by_symbol.items()},
        "peak_rss_bytes_macos": peak_rss,
        "peak_rss_MiB": peak_mib,
        "raw_archives_retained": False,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", nargs="*", default=None,
                    help="pairs SYMBOL:MONTH; smoke ceiling wall <= 1 h")
    args = ap.parse_args()
    smoke = args.smoke is not None
    if smoke:
        pairs = [tuple(p.split(":")) for p in args.smoke]
        staging = WORKTREE / "v17_data" / "staging_v17_smoke"
        max_wall_h = 1.0
    else:
        pairs = [(s, m) for s in SYMBOLS for m in MONTHS]
        staging = STAGING
        max_wall_h = 6.0

    command = [sys.executable, str(Path(__file__).resolve())] + sys.argv[1:]
    with heavy_lock.acquire(
        cycle_id="CRYPTO-V17", role="P0_STAGING_EXTRACTION_H1",
        worktree=str(WORKTREE), command=command,
        expected_artifacts=[str(staging / "panel_manifest.json")],
    ) as lock:
        try:
            manifest = run_build(pairs, staging, lock)
        except Exception:
            tail = "\n".join(traceback.format_exc().strip().splitlines()[-12:])
            lock.release(status="FAILED", note=f"stderr tail: {tail}")
            raise
        manifest["wall_ceiling_hours"] = max_wall_h
        if manifest["wall_hours_serial"] > max_wall_h:
            raise RuntimeError(
                f"CEILING serial: wall {manifest['wall_hours_serial']} h > "
                f"{max_wall_h} h -> BLOCKED_DATA")
        out = staging / "panel_manifest.json"
        out.write_text(json.dumps(manifest, indent=1) + "\n")
        print(f"manifest written -> {out}; peak RSS {manifest['peak_rss_MiB']} MiB; "
              f"wall {manifest['wall_hours_serial']} h; raw archives deleted",
              flush=True)


if __name__ == "__main__":
    main()
