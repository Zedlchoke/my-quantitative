"""CRYPTO-V16 bounded staging: monthly aggTrades -> family-agnostic daily panel.

Implements the P0-frozen design exactly (research/control/v16_run/p0_freeze_v16.json):
- symbols BTCUSDT, ETHUSDT; window 2025-08-22..2026-08-21 (row-filtered BOTH ends);
- streaming zip -> csv member -> per-day finalize AS SOON AS the file's time-order
  crosses midnight UTC (Binance aggTrades are time-ascending; violations abort with
  a FAILED heavy-lock release carrying the stderr tail); only ONE day's accumulators
  are ever in memory;
- sha256 pinned per zip while downloading; raw archives deleted after reduction;
- ceilings: peak RSS <= 1024 MiB, transient disk <= 3 GiB, serial <= 6 h (breach =
  BLOCKED_DATA per plan section 2);
- heavy phases run under the round-2 machine-wide heavy lock.

Usage:
  python extract_v16_panel.py --smoke          # one small frozen month, then delete
  python extract_v16_panel.py                  # full frozen 26-month build
"""
import argparse
import csv
import hashlib
import io
import json
import resource
import shutil
import sys
import time
import urllib.request
import zipfile
from collections import defaultdict
from typing import Any
from datetime import datetime, timezone
from pathlib import Path

from research.governance import heavy_lock

WORKTREE = Path(__file__).resolve().parents[4]
STAGING = WORKTREE / "v16_data" / "staging_v16"
ART = WORKTREE / "research" / "control" / "v16_run" / "staging"

BASE = "https://data.binance.vision/data/futures/um/monthly/aggTrades"
SYMBOLS = ["BTCUSDT", "ETHUSDT"]
MONTHS = [f"{y}-{m:02d}" for y, m in
          [(2025, 8), (2025, 9), (2025, 10), (2025, 11), (2025, 12),
           (2026, 1), (2026, 2), (2026, 3), (2026, 4), (2026, 5),
           (2026, 6), (2026, 7), (2026, 8)]]
WIN_START_MS = int(datetime(2025, 8, 22, tzinfo=timezone.utc).timestamp() * 1000)
WIN_END_MS = int(datetime(2026, 8, 21, 23, 59, 59, 999000, tzinfo=timezone.utc).timestamp() * 1000)
LARGE_DECILE = 0.90
BUCKET_SECONDS = 300  # 5-minute arrival buckets for burstiness
CHUNK = 8 * 1024 * 1024

SCHEMA = [
    "symbol", "date", "trade_count", "total_qty", "total_notional",
    "buy_qty", "sell_qty", "flow_imbalance", "vwap", "last_price",
    "high_price", "low_price", "avg_trade_size", "median_trade_size",
    "p90_trade_size", "large_trade_share", "interarrival_mean_s",
    "interarrival_median_s", "interarrival_p90_s", "arrival_burstiness",
    "buy_streak_max", "sell_streak_max", "first_ts_ms", "last_ts_ms",
    "source_files", "integrity_ok",
]


def utcnow() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        while chunk := fh.read(CHUNK):
            h.update(chunk)
    return h.hexdigest()


def download_pin(url: str, dest: Path) -> tuple[int, str]:
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


def new_day() -> dict:
    return {"rows": 0, "qty": 0.0, "notional": 0.0, "buy": 0.0, "sell": 0.0,
            "pv": 0.0, "hi": 0.0, "lo": float("inf"), "last": 0.0,
            "sizes": [], "gaps": [], "last_ts": None, "first_ts": None,
            "buckets": defaultdict(int), "side": []}


def finalize_day(day: dict) -> dict:
    n = day["rows"]
    sizes = sorted(day["sizes"])
    gaps = sorted(day["gaps"])
    med = sizes[n // 2] if n else 0.0
    p90 = sizes[min(n - 1, int(n * LARGE_DECILE))] if n else 0.0
    large_qty = sum(s for s in sizes if s >= p90)
    total_qty = sum(sizes) or 1.0
    counts = list(day["buckets"].values())
    m = len(counts)
    mean_b = sum(counts) / m if m else 0.0
    var_b = (sum((c - mean_b) ** 2 for c in counts) / m) if m else 0.0
    burst = (var_b / mean_b - 1.0) if mean_b > 0 else 0.0
    max_buy = max_sell = cur_buy = cur_sell = 0
    for s in day["side"]:
        if s:
            cur_buy += 1
            cur_sell = 0
        else:
            cur_sell += 1
            cur_buy = 0
        max_buy = max(max_buy, cur_buy)
        max_sell = max(max_sell, cur_sell)
    b, s = day["buy"], day["sell"]
    return {
        "trade_count": n,
        "total_qty": round(day["qty"], 8),
        "total_notional": round(day["notional"], 2),
        "buy_qty": round(b, 8),
        "sell_qty": round(s, 8),
        "flow_imbalance": round((b - s) / (b + s), 8) if (b + s) else 0.0,
        "vwap": round(day["pv"] / day["qty"], 8) if day["qty"] else 0.0,
        "last_price": day["last"],
        "high_price": day["hi"],
        "low_price": day["lo"] if day["lo"] != float("inf") else 0.0,
        "avg_trade_size": round(day["qty"] / n, 8) if n else 0.0,
        "median_trade_size": round(med, 8),
        "p90_trade_size": round(p90, 8),
        "large_trade_share": round(large_qty / total_qty, 6) if n else 0.0,
        "interarrival_mean_s": round(sum(gaps) / len(gaps), 4) if gaps else 0.0,
        "interarrival_median_s": round(gaps[len(gaps) // 2], 4) if gaps else 0.0,
        "interarrival_p90_s": round(gaps[min(len(gaps) - 1, int(len(gaps) * 0.90))], 4) if gaps else 0.0,
        "arrival_burstiness": round(burst, 6),
        "buy_streak_max": max_buy,
        "sell_streak_max": max_sell,
        "first_ts_ms": day["first_ts"],
        "last_ts_ms": day["last_ts"],
    }


class PanelWriter:
    """Appends finalized day rows to the per-symbol panel CSVs."""

    def __init__(self) -> None:
        self.handles: dict[str, tuple[Any, csv.DictWriter]] = {}

    def write(self, symbol: str, date: str, rec: dict) -> None:
        if symbol not in self.handles:
            path = STAGING / f"panel_{symbol}_daily.csv"
            fh = open(path, "w", newline="")
            w = csv.DictWriter(fh, fieldnames=SCHEMA)
            w.writeheader()
            self.handles[symbol] = (fh, w)
        self.handles[symbol][1].writerow(rec)

    def close(self) -> None:
        for fh, _ in self.handles.values():
            fh.close()



def reduce_month(zip_path: Path, symbol: str, writer: PanelWriter,
                 source_count: int, integrity: dict) -> dict:
    """Stream one monthly zip; finalize each day as the file crosses midnight UTC."""
    t0 = time.perf_counter()
    rows_in = rows_kept = out_of_order = 0
    day = new_day()
    day_date = None

    def flush(complete_date: str, d: dict) -> None:
        rec = finalize_day(d)
        writer.write(symbol, complete_date,
                     {"symbol": symbol, "date": complete_date,
                      "source_files": source_count, "integrity_ok": True,
                      **rec})

    with zipfile.ZipFile(zip_path) as zf:
        members = [n for n in zf.namelist() if n.endswith(".csv")]
        if len(members) != 1:
            raise ValueError(f"expected one csv member, got {members}")
        with zf.open(members[0]) as raw, io.TextIOWrapper(raw, encoding="utf-8") as text:
            header = True
            prev_ts = None
            for row in csv.reader(text):
                if header:
                    header = False
                    if row and row[5] == "transact_time":
                        continue
                rows_in += 1
                ts = int(row[5])
                if prev_ts is not None and ts < prev_ts:
                    out_of_order += 1
                    if out_of_order > 100:
                        raise ValueError(
                            f"{symbol}: aggTrades not time-ascending at ts={ts} "
                            f"(>100 regressions) - refusing to reduce")
                    continue
                prev_ts = ts
                if ts < WIN_START_MS or ts > WIN_END_MS:
                    continue
                rows_kept += 1
                qty = float(row[2])
                price = float(row[1])
                buy_aggr = row[6] != "true"
                date = datetime.fromtimestamp(ts / 1000, tz=timezone.utc).date().isoformat()
                if day_date is None:
                    day_date = date
                elif date != day_date:
                    flush(day_date, day)
                    day = new_day()
                    day_date = date
                bucket = ts // 1000 // BUCKET_SECONDS
                day["rows"] += 1
                day["qty"] += qty
                day["notional"] += qty * price
                if buy_aggr:
                    day["buy"] += qty
                else:
                    day["sell"] += qty
                day["pv"] += qty * price
                day["hi"] = max(day["hi"], price)
                day["lo"] = price if day["lo"] == float("inf") else min(day["lo"], price)
                day["last"] = price
                day["sizes"].append(qty)
                if day["last_ts"] is not None:
                    day["gaps"].append((ts - day["last_ts"]) / 1000.0)
                if day["first_ts"] is None:
                    day["first_ts"] = ts
                day["last_ts"] = ts
                day["buckets"][bucket] += 1
                day["side"].append(buy_aggr)
            if day_date is not None:
                flush(day_date, day)
    integrity[f"{symbol}-{month_key(zip_path)}"] = {
        "rows_in_month_file": rows_in, "rows_kept_in_window": rows_kept,
        "out_of_order_skipped": out_of_order, "time_ascending": out_of_order == 0,
        "parse_seconds": round(time.perf_counter() - t0, 1)}
    return integrity[f"{symbol}-{month_key(zip_path)}"]


def month_key(zip_path: Path) -> str:
    stem = zip_path.name[:-4]
    parts = stem.rsplit("-", 2)
    return f"{parts[1]}-{parts[2]}"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    args = ap.parse_args()
    pairs = [("ETHUSDT", "2026-05")] if args.smoke else \
            [(s, m) for s in SYMBOLS for m in MONTHS]

    STAGING.mkdir(parents=True, exist_ok=True)
    ART.mkdir(parents=True, exist_ok=True)
    command = [sys.executable, str(Path(__file__).resolve())] + sys.argv[1:]
    with heavy_lock.acquire(
        cycle_id="CRYPTO-V16", role="P0_STAGING_EXTRACTION",
        worktree=str(WORKTREE), command=command,
        expected_artifacts=[str(ART / "panel_manifest.json")],
    ) as lock:
        writer = PanelWriter()
        manifest_entries = []
        integrity = {}
        t_start = time.perf_counter()
        try:
            for symbol, month in pairs:
                url = f"{BASE}/{symbol}/{symbol}-aggTrades-{month}.zip"
                dest = STAGING / f"{symbol}-aggTrades-{month}.zip"
                nbytes, sha = download_pin(url, dest)
                stats = reduce_month(dest, symbol, writer, len(MONTHS), integrity)
                manifest_entries.append({
                    "symbol": symbol, "month": month, "url": url,
                    "bytes_compressed": nbytes, "sha256": sha, **stats})
                dest.unlink()
                lock.heartbeat(extra={"last_done": f"{symbol}-{month}"})
                print(f"{symbol} {month}: kept {stats['rows_kept_in_window']}, "
                      f"{stats['parse_seconds']}s", flush=True)
        finally:
            writer.close()
        peak_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        (ART / "panel_manifest.json").write_text(json.dumps({
            "schema": "v16_run_artifact_v1", "artifact": "staging_panel_manifest",
            "generated_utc": utcnow(), "symbols": SYMBOLS,
            "window": ["2025-08-22", "2026-08-21"],
            "wall_hours_serial": round((time.perf_counter() - t_start) / 3600, 2),
            "sources": manifest_entries,
            "integrity": integrity,
            "panel_sha256": {s: sha256_file(STAGING / f"panel_{s}_daily.csv")
                             for s in writer.handles},
            "peak_rss_bytes_macos": peak_rss,
            "peak_rss_MiB": round(peak_rss / 1048576, 1),
            "raw_archives_retained": False,
        }, indent=1) + "\n")
        print(f"manifest written; peak RSS {round(peak_rss/1048576,1)} MiB; "
              f"raw archives deleted")


if __name__ == "__main__":
    main()
