"""CRYPTO-V16 P0 pre-check: bounded streaming aggTrades sample measurement.

Downloads ONE symbol-month zip (worst case), sha256-pins it while streaming,
reduces it to bounded daily observables WITHOUT extracting the CSV to disk,
measures peak RSS and wall time, then deletes the raw archive. Evidence-only:
no PnL, no proposal, no scored outcome exists.

Usage: python precheck_stream_sample.py SYMBOL YYYY-MM
"""
import csv
import hashlib
import io
import json
import os
import resource
import shutil
import sys
import time
import urllib.request
import zipfile
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from research.governance import heavy_lock

BASE = "https://data.binance.vision/data/futures/um/monthly/aggTrades"
WORKTREE = Path(__file__).resolve().parents[4]
STAGING = WORKTREE / "v16_data" / "precheck"
ARTIFACT_DIR = WORKTREE / "research" / "control" / "v16_run" / "p0_probe"
CHUNK = 8 * 1024 * 1024


def utcnow() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def download_and_pin(url: str, dest: Path) -> tuple[int, str, float, int]:
    digest = hashlib.sha256()
    total = 0
    t0 = time.perf_counter()
    with urllib.request.urlopen(url, timeout=120) as resp, open(dest, "wb") as fh:
        expected = int(resp.headers.get("Content-Length", "-1"))
        while True:
            chunk = resp.read(CHUNK)
            if not chunk:
                break
            digest.update(chunk)
            fh.write(chunk)
            total += len(chunk)
    elapsed = time.perf_counter() - t0
    return total, digest.hexdigest(), elapsed, expected


def stream_reduce(zip_path: Path) -> dict:
    t0 = time.perf_counter()
    days = defaultdict(lambda: [0, 0.0, 0.0])  # rows, buy_vol, sell_vol
    min_ts, max_ts, ncols = None, None, None
    with zipfile.ZipFile(zip_path) as zf:
        members = [n for n in zf.namelist() if n.endswith(".csv")]
        if len(members) != 1:
            raise ValueError(f"expected exactly one csv member, got {members}")
        with zf.open(members[0]) as raw, io.TextIOWrapper(raw, encoding="utf-8") as text:
            header_skipped = False
            for row in csv.reader(text):
                if not header_skipped:
                    header_skipped = True
                    if row and row[5] == "transact_time":
                        continue
                if ncols is None:
                    ncols = len(row)
                elif len(row) != ncols:
                    raise ValueError(f"column drift at agg_trade_id={row[0]}")
                ts = int(row[5])
                if min_ts is None:
                    min_ts = max_ts = ts
                else:
                    if ts < min_ts:
                        min_ts = ts
                    if ts > max_ts:
                        max_ts = ts
                qty = float(row[2])
                day = datetime.fromtimestamp(ts / 1000, tz=timezone.utc).date().isoformat()
                rec = days[day]
                rec[0] += 1
                if row[6] == "true":  # buyer is maker -> sell aggressor
                    rec[2] += qty
                else:
                    rec[1] += qty
    elapsed = time.perf_counter() - t0
    n_days = len(days)
    sample_days = sorted(days)
    imbalance = {}
    for d in sample_days[:3] + sample_days[-3:]:
        b, s = days[d][1], days[d][2]
        imbalance[d] = (b - s) / (b + s) if (b + s) > 0 else 0.0
    return {
        "rows": sum(r[0] for r in days.values()),
        "columns": ncols,
        "distinct_days": n_days,
        "min_transact_time_ms": min_ts,
        "max_transact_time_ms": max_ts,
        "daily_imbalance_sample_head_tail": imbalance,
        "parse_seconds": round(elapsed, 2),
        "rows_per_second": round(sum(r[0] for r in days.values()) / elapsed, 0),
    }


def main() -> None:
    symbol, month = sys.argv[1], sys.argv[2]
    url = f"{BASE}/{symbol}/{symbol}-aggTrades-{month}.zip"
    dest = STAGING / f"{symbol}-aggTrades-{month}.zip"
    artifact_path = ARTIFACT_DIR / "aggtrades_precheck_sample.json"

    command = [sys.executable, str(Path(__file__).resolve()), symbol, month]
    with heavy_lock.acquire(
        cycle_id="CRYPTO-V16",
        role="P0_PRECHECK_STREAM_SAMPLE",
        worktree=str(WORKTREE),
        command=command,
        expected_artifacts=[str(artifact_path)],
    ):
        STAGING.mkdir(parents=True, exist_ok=True)
        try:
            nbytes, sha256, dl_s, expected = download_and_pin(url, dest)
            if expected != -1 and nbytes != expected:
                raise IOError(f"Content-Length {expected} != downloaded {nbytes}")
            reduction = stream_reduce(dest)
            peak_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss  # bytes on macOS
        finally:
            if dest.exists():
                dest.unlink()
            shutil.rmtree(STAGING, ignore_errors=True)

        artifact = {
            "schema": "v16_run_artifact_v1",
            "artifact": "p0_precheck_stream_sample",
            "generated_utc": utcnow(),
            "producer_role": "A1",
            "heavy_lock": {
                "cycle_id": "CRYPTO-V16",
                "role": "P0_PRECHECK_STREAM_SAMPLE",
                "runtime": str(heavy_lock.shared_runtime_dir()),
                "verdict": "ACQUIRED_AND_RELEASED_FINISHED",
            },
            "sample": {
                "url": url,
                "symbol": symbol,
                "month": month,
                "bytes_compressed": nbytes,
                "content_length_match": True,
                "sha256": sha256,
                "download_seconds": round(dl_s, 2),
                "download_MBps": round(nbytes / 1e6 / dl_s, 1),
            },
            "reduction": reduction,
            "peak_rss_bytes_macos": peak_rss,
            "peak_rss_MiB": round(peak_rss / 1048576, 1),
            "raw_archive_deleted": not dest.exists(),
            "staging_dir_removed": not STAGING.exists(),
            "no_pnl_fields": True,
        }
        ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
        artifact_path.write_text(json.dumps(artifact, indent=1) + "\n")
        print(json.dumps(artifact, indent=1))


if __name__ == "__main__":
    main()
