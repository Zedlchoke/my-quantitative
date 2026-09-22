#!/usr/bin/env python
"""EDQ1 P1 bounded probe — Dukascopy EURUSD hourly tick archives.

Fetches raw .bi5 bytes (IMMUTABLE, stored under data_local/, gitignored),
records sha256/HTTP status/retrieval times per file, decodes LZMA '>5i'
tick records, and downsamples to 1-minute bid/ask bars (no interpolation).

Concurrency: 8 I/O-bound workers (server TTFB measured 10-20 s/file; serial
would be ~1 h). Retry: up to 5 attempts on 503/429/network with backoff.
404 is a terminal, RECORDED behavior (weekend hours).

Read-only research under cycle EURUSD-DATA-QUALIFICATION-V1 (plan §1, §3 P1).
"""
import concurrent.futures as cf
import datetime as dt
import hashlib
import json
import lzma
import os
import random
import struct
import sys
import threading
import time
import urllib.error
import urllib.request

WORKTREE = "/Users/hoangminhlong/my-quantitative/.worktrees/eurusd-data-qualification-v1/integration"
CYCLE = os.path.join(WORKTREE, "research/control/eurusd_data_qualification_v1")
RAW_DIR = os.path.join(CYCLE, "data_local/dukascopy")
PROBE_DIR = os.path.join(CYCLE, "probe")
LOG_PATH = os.path.join(RAW_DIR, "fetch_log.jsonl")

BASE_URL = "https://datafeed.dukascopy.com/datafeed/EURUSD"
UA = "edq1-data-qualification-probe/1 (internal research; contact via repo owner)"
POINT_SCALE = 1e5  # verified below: decoded EURUSD range ~1.08-1.09 for Mar 2024
RECORD_LEN = 20
RETRIES = 5
WORKERS = 8

WINDOW_START = dt.datetime(2024, 3, 4, 0, 0, 0, tzinfo=dt.timezone.utc)
WINDOW_END = dt.datetime(2024, 3, 14, 0, 0, 0, tzinfo=dt.timezone.utc)  # exclusive

BOUNDARY_FILES = [
    ("boundary_2023-06-15T08", "https://datafeed.dukascopy.com/datafeed/EURUSD/2023/05/15/08h_ticks.bi5",
     "20230615_08h_ticks.bi5"),
    ("boundary_2025-06-13T08", "https://datafeed.dukascopy.com/datafeed/EURUSD/2025/05/13/08h_ticks.bi5",
     "20250613_08h_ticks.bi5"),
]

_log_lock = threading.Lock()
_log_f = None


def utcnow_iso():
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def target_hours():
    out = []
    cur = WINDOW_START
    while cur < WINDOW_END:
        y, m, d, h = cur.year, cur.month, cur.day, cur.hour
        url = f"{BASE_URL}/{y}/{m-1:02d}/{d:02d}/{h:02d}h_ticks.bi5"  # month 0-INDEXED
        label = cur.strftime("%Y%m%d_%H") + "h"
        out.append((label, url, cur.replace(tzinfo=None)))
        cur += dt.timedelta(hours=1)
    return out


def fetch(url: str):
    """GET with <=5 retries/backoff on 5xx/429/network. 404 terminal."""
    for attempt in range(1, RETRIES + 1):
        t0 = utcnow_iso()
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=60) as resp:
                content = resp.read()
                status = resp.status
            return status, content, t0, utcnow_iso(), None
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504):
                if attempt < RETRIES:
                    time.sleep(min(2 ** attempt, 30) + random.random())
                continue
            return e.code, b"", t0, utcnow_iso(), f"HTTPError {e.code}"
        except Exception as e:
            if attempt < RETRIES:
                time.sleep(min(2 ** attempt, 30) + random.random())
            else:
                return None, b"", t0, utcnow_iso(), f"FAILED_AFTER_{RETRIES}_RETRIES: {type(e).__name__}: {e}"
    return None, b"", t0, utcnow_iso(), f"FAILED_AFTER_{RETRIES}_RETRIES: persistent 5xx/429"


def decode_bi5(raw: bytes):
    if len(raw) == 0:
        return [], "EMPTY_FILE_NO_TICKS"
    try:
        out = lzma.LZMADecompressor(format=lzma.FORMAT_AUTO).decompress(raw)
    except lzma.LZMAError as e:
        return [], f"DECODE_ERROR:{e}"
    if len(out) % RECORD_LEN != 0:
        return [], f"DECODE_ERROR:residual={len(out) % RECORD_LEN}"
    n = len(out) // RECORD_LEN
    ticks = [struct.unpack(">5i", out[i * RECORD_LEN:(i + 1) * RECORD_LEN]) for i in range(n)]
    return ticks, "OK"


def downsample_1min(hour_start_naive_utc, ticks):
    """1-min bars per side: open=first, close=last, high/low=extremes, tick_count.

    Bar key = epoch ms of the minute START. No interpolation.
    """
    hour_ms = int(hour_start_naive_utc.replace(tzinfo=dt.timezone.utc).timestamp() * 1000)
    buckets = {}
    for off_ms, ask_int, bid_int, _, _ in ticks:
        minute = (hour_ms + off_ms) // 60000
        b = buckets.setdefault(minute, {"bid": [], "ask": []})
        b["bid"].append(bid_int / POINT_SCALE)
        b["ask"].append(ask_int / POINT_SCALE)
    bid_bars, ask_bars = {}, {}
    for minute, sides in sorted(buckets.items()):
        for side, store in (("bid", bid_bars), ("ask", ask_bars)):
            px = sides[side]
            store[str(minute)] = {
                "open": px[0], "close": px[-1],
                "high": max(px), "low": min(px),
                "tick_count": len(px),
            }
    return bid_bars, ask_bars


def process(job):
    role, url, hour_dt, store_name = job
    status, content, t0, t1, err = fetch(url)
    rel = os.path.join("2024" if hour_dt is not None else "boundary", store_name)
    raw_path = os.path.join(RAW_DIR, rel)
    os.makedirs(os.path.dirname(raw_path), exist_ok=True)
    with open(raw_path, "wb") as f:  # raw bytes immutable from here on
        f.write(content)

    ticks, decode_status = decode_bi5(content)
    int_min = int_max = None
    if ticks:
        ints = [min(t[1], t[2]) for t in ticks] + [max(t[1], t[2]) for t in ticks]
        int_min, int_max = min(ints), max(ints)

    rec = {
        "schema": "edq1_retrieval_manifest@1",
        "file_role": role,
        "source": "dukascopy_public_datafeed",
        "url": url,  # public endpoint, no credential material
        "local_relpath": f"data_local/dukascopy/{rel}",
        "retrieval_start_utc": t0,
        "retrieval_end_utc": t1,
        "http_status": status,
        "byte_count": len(content),
        "sha256": sha256(content),
        "decode_status": decode_status,
        "tick_count": len(ticks),
        "price_int_min": int_min,
        "price_int_max": int_max,
        "error": err,
    }
    with _log_lock:
        _log_f.write(json.dumps(rec) + "\n")
        _log_f.flush()
    return rec


def main():
    global _log_f
    os.makedirs(RAW_DIR, exist_ok=True)
    os.makedirs(PROBE_DIR, exist_ok=True)

    # resume: keep prior entries that are definitive successes only
    prior, done_urls = [], set()
    if os.path.exists(LOG_PATH):
        with open(LOG_PATH) as f:
            for line in f:
                rec = json.loads(line)
                if rec["http_status"] == 200 and rec["decode_status"] in ("OK", "EMPTY_FILE_NO_TICKS"):
                    prior.append(rec)
                    done_urls.add(rec["url"])
        os.rename(LOG_PATH, LOG_PATH + f".prev.{int(time.time())}")

    targets = [("2024_20240304_20240314", u, d, d.strftime("%Y%m%d_") + u.rsplit("/", 1)[-1])
               for (_, u, d) in target_hours()]
    targets += [(name, url, None, store) for (name, url, store) in BOUNDARY_FILES]
    todo = [j for j in targets if j[1] not in done_urls]

    _log_f = open(LOG_PATH, "a")
    for rec in prior:
        _log_f.write(json.dumps(rec) + "\n")
    _log_f.flush()

    results = list(prior)
    with cf.ThreadPoolExecutor(max_workers=WORKERS) as ex:
        for i, rec in enumerate(ex.map(process, todo), 1):
            results.append(rec)
            if i % 25 == 0:
                print(f"progress {i}/{len(todo)}", flush=True)
    _log_f.close()

    # deterministic order for manifest + bars
    results.sort(key=lambda r: r["url"])

    all_bid, all_ask = {}, {}
    scale_evidence = {"files_with_ticks": 0, "int_min": None, "int_max": None,
                      "decoded_price_min": None, "decoded_price_max": None}
    for rec in results:
        if rec["file_role"] != "2024_20240304_20240314" or rec["tick_count"] == 0:
            continue
        label = os.path.basename(rec["local_relpath"]).split("_ticks")[0]
        hour_dt = dt.datetime.strptime(label, "%Y%m%d_%Hh")
        raw = open(os.path.join(CYCLE, rec["local_relpath"]), "rb").read()
        ticks, st = decode_bi5(raw)
        assert st == "OK", f"re-decode mismatch {label}: {st}"
        bid, ask = downsample_1min(hour_dt, ticks)
        all_bid.update(bid)
        all_ask.update(ask)
        lo, hi = rec["price_int_min"], rec["price_int_max"]
        scale_evidence["files_with_ticks"] += 1
        scale_evidence["int_min"] = lo if scale_evidence["int_min"] is None else min(scale_evidence["int_min"], lo)
        scale_evidence["int_max"] = hi if scale_evidence["int_max"] is None else max(scale_evidence["int_max"], hi)

    if scale_evidence["int_min"] is not None:
        scale_evidence["decoded_price_min"] = scale_evidence["int_min"] / POINT_SCALE
        scale_evidence["decoded_price_max"] = scale_evidence["int_max"] / POINT_SCALE

    with open(os.path.join(RAW_DIR, "bars_1min_bid.json"), "w") as f:
        json.dump(all_bid, f, sort_keys=True)
    with open(os.path.join(RAW_DIR, "bars_1min_ask.json"), "w") as f:
        json.dump(all_ask, f, sort_keys=True)
    with open(os.path.join(RAW_DIR, "scale_evidence.json"), "w") as f:
        json.dump({"candidate_point_scale": POINT_SCALE, **scale_evidence}, f, indent=2)

    with open(os.path.join(PROBE_DIR, "retrieval_manifest.json"), "w") as f:
        json.dump({
            "schema": "edq1_retrieval_manifest@1",
            "source": "dukascopy_public_datafeed",
            "window_utc": [WINDOW_START.isoformat().replace("+00:00", "Z"),
                           WINDOW_END.isoformat().replace("+00:00", "Z")],
            "boundary_files": [name for (name, _, _) in BOUNDARY_FILES],
            "entries": results,
        }, f, indent=2)

    ok = sum(1 for r in results if r["decode_status"] == "OK")
    empty = sum(1 for r in results if r["decode_status"] == "EMPTY_FILE_NO_TICKS")
    e404 = sum(1 for r in results if r["http_status"] == 404)
    errs = [r for r in results if r["error"]]
    print(json.dumps({
        "total_targets": len(targets), "decode_ok": ok, "empty_no_ticks": empty,
        "http_404": e404, "failed": len(errs),
        "bars_1min_bid": len(all_bid), "bars_1min_ask": len(all_ask),
        "scale_evidence": scale_evidence,
    }, indent=2))
    if errs:
        print("ERRORS:", json.dumps(errs, indent=2))
        sys.exit(1)


if __name__ == "__main__":
    main()
