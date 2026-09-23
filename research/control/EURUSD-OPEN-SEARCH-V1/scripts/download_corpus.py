"""Download the Dukascopy M1 BID/ASK candle corpus 2021-01-01..2025-12-31 UTC.

4 keep-alive worker connections, polite pacing, 429 backoff, resumable via
manifest + on-disk files. Raw bytes stay under data_local/ (gitignored);
only this manifest (sha256 per file) is committable.
"""
import datetime as dt
import hashlib
import json
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import duka_lib as dk

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data_local" / "duka" / "M1"
MANIFEST = ROOT / "data_local" / "duka" / "m1_manifest.json"

START = dt.date(2021, 1, 1)
END = dt.date(2025, 12, 31)
WORKERS = 4


def load_manifest():
    if MANIFEST.exists():
        return json.loads(MANIFEST.read_text())
    return {"schema": "eosv1.m1_manifest@1", "files": {}}


MAN = load_manifest()
FILES = MAN["files"]
LOCK = threading.Lock()
STATS = {"fetched": 0, "cached": 0, "missing": 0, "days": 0}


def fetch_one(args):
    y, m, d, side = args
    rel = f"{side}/{y}-{m:02d}-{d:02d}.bi5"
    path = RAW / rel
    if path.exists() and path.stat().st_size > 0:
        raw = path.read_bytes()
        with LOCK:
            STATS["cached"] += 1
            FILES[rel] = {
                "sha256": hashlib.sha256(raw).hexdigest(),
                "bytes": len(raw),
                "plain_bytes": -1,
            }
        return
    raw = WORKER_LOCAL.fetcher.fetch(dk.candle_path(y, m, d, side))
    if raw is None:
        with LOCK:
            FILES[f"MISSING/{y}-{m:02d}-{d:02d}.{side}"] = {"missing": True}
            STATS["missing"] += 1
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)
    with LOCK:
        STATS["fetched"] += 1
        FILES[rel] = {
            "sha256": hashlib.sha256(raw).hexdigest(),
            "bytes": len(raw),
            "plain_bytes": -1,
        }


class WorkerLocal(threading.local):
    def __init__(self):
        self.fetcher = dk.KeepAliveFetcher()


WORKER_LOCAL = WorkerLocal()


def main():
    t0 = time.time()
    days = [START + dt.timedelta(days=i) for i in range((END - START).days + 1)]
    jobs = [(d.year, d.month, d.day, side) for d in days for side in ("BID", "ASK")]
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        for i, _ in enumerate(ex.map(fetch_one, jobs)):
            if i % 400 == 0 and i:
                MAN["progress"] = {**STATS, "jobs_done": i, "elapsed_s": round(time.time() - t0, 1)}
                MANIFEST.write_text(json.dumps(MAN, indent=0))
                print(f"jobs={i}/{len(jobs)} fetched={STATS['fetched']} cached={STATS['cached']} missing={STATS['missing']} elapsed={time.time()-t0:.0f}s", flush=True)
    MAN["complete"] = True
    MAN["totals"] = {**STATS, "elapsed_s": round(time.time() - t0, 1)}
    MANIFEST.write_text(json.dumps(MAN, indent=0))
    print("DONE", MAN["totals"], flush=True)


if __name__ == "__main__":
    main()
