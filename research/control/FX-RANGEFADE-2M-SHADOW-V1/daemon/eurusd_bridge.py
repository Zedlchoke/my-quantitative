"""Download Dukascopy M1 BID/ASK candle corpora for GBPUSD + USDJPY,
2021-01-01..2026-06-30. 2 keep-alive workers per pair (4 total), polite
pacing, resumable per-pair manifests: data_local/<PAIR>/m1_manifest.json.
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
import duka_lib as duka
import datetime as _dt
PAIRS = {"EURUSD": {"scale": 1e5, "pip": 1e-4, "range": (0.95, 1.45)}}
ROOT = Path('/Users/hoangminhlong/my-quantitative/.worktrees/fx-rangefade-2m-shadow-v1/research/control/FX-RANGEFADE-2M-SHADOW-V1')
START = _dt.date(2026, 7, 1)
END = _dt.date(2026, 9, 23)

def candle_path(pair, y, m, d, side):
    return f"/datafeed/{pair}/{y}/{m-1:02d}/{d:02d}/{side}_candles_min_1.bi5"

ROOT = Path(__file__).resolve().parent.parent
WORKERS_PER_PAIR = 2

STATS = {}
LOCKS = {p: threading.Lock() for p in PAIRS}


def load_manifest(pair):
    p = ROOT / "data_local" / pair / "m1_manifest.json"
    if p.exists():
        return json.loads(p.read_text())
    return {"schema": "fxm.m1_manifest@1", "pair": pair, "files": {}}


MANS = {p: load_manifest(p) for p in PAIRS}


class WorkerLocal(threading.local):
    def __init__(self):
        self.fetcher = duka.KeepAliveFetcher()


WORKER_LOCAL = WorkerLocal()


def fetch_one(args):
    pair, y, m, d, side = args
    rel = f"M1/{side}/{y}-{m:02d}-{d:02d}.bi5"
    path = ROOT / "data_local" / pair / rel
    man = MANS[pair]
    with LOCKS[pair]:
        if path.exists() and path.stat().st_size > 0:
            raw = path.read_bytes()
            man["files"][rel] = {"sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}
            man["totals"]["cached"] = man["totals"].get("cached", 0) + 1
            return
    raw = WORKER_LOCAL.fetcher.fetch(candle_path(pair, y, m, d, side))  # local 5-arg def
    with LOCKS[pair]:
        if raw is None:
            man["files"][f"MISSING/{y}-{m:02d}-{d:02d}.{side}"] = {"missing": True}
            man["totals"]["missing"] = man["totals"].get("missing", 0) + 1
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
        man["files"][rel] = {"sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}
        man["totals"]["fetched"] = man["totals"].get("fetched", 0) + 1


def main():
    t0 = time.time()
    days = [START + dt.timedelta(days=i) for i in range((END - START).days + 1)]
    jobs = []
    for pair in PAIRS:
        MANS[pair]["totals"] = {}
        jobs.extend((pair, d.year, d.month, d.day, side) for d in days for side in ("BID", "ASK"))
    done = [0]
    with ThreadPoolExecutor(max_workers=WORKERS_PER_PAIR * len(PAIRS)) as ex:
        for _ in ex.map(fetch_one, jobs):
            done[0] += 1
            if done[0] % 1000 == 0:
                for pair in PAIRS:
                    mp = ROOT / "data_local" / pair / "m1_manifest.json"
                    MANS[pair]["progress"] = {"jobs_done": done[0], "elapsed_s": round(time.time() - t0, 1)}
                    mp.parent.mkdir(parents=True, exist_ok=True)
                    mp.write_text(json.dumps(MANS[pair], indent=0))
                print(f"jobs={done[0]}/{len(jobs)} elapsed={time.time()-t0:.0f}s " +
                      " ".join(f"{p}:f{MANS[p]['totals'].get('fetched',0)}" for p in PAIRS), flush=True)
    for pair in PAIRS:
        MANS[pair]["complete"] = True
        MANS[pair]["totals"]["elapsed_s"] = round(time.time() - t0, 1)
        (ROOT / "data_local" / pair / "m1_manifest.json").write_text(json.dumps(MANS[pair], indent=0))
        print("DONE", pair, MANS[pair]["totals"], flush=True)


if __name__ == "__main__":
    main()
