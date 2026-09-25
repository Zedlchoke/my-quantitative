"""Heavy-locked, resumable full M1 download per pair — ERP1-TRACKA-COHORT-1.

Downloads Dukascopy M1 BID+ASK day bi5 files for [start, end] into
  data_local/duka/M1/{BID,ASK}/{SYMBOL}/YYYY-MM-DD.bi5   (machine-local,
  gitignored raw bytes) and sha256-manifests every file (atomically,
  incrementally) into
  data_local/duka/m1_manifest_{SYMBOL}.json              (COMMITTED).

Governance (plan §5.2 bounded heavy job):
  - machine-wide heavy lock via ROOT research/governance.heavy_lock,
    heartbeat thread keeps the registry fresh, release in finally with
    FINISHED/FAILED status (FAILED carries a stderr note);
  - LockBusyError -> NOT_RUN_RESOURCE_CONFLICT verdict, exit 4, no work;
  - --budget-seconds soft window: after it elapses the run checkpoints,
    releases the lock and exits 3 (PARTIAL) — the caller re-acquires and
    re-invokes (idempotent: files already present with matching manifest
    sha are skipped, so resume is exact).

Exit codes: 0 complete | 3 budget PARTIAL (re-acquire + re-run) |
            4 NOT_RUN_RESOURCE_CONFLICT | 2 argument/manifest error.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import sys
import threading
import time
from pathlib import Path

LANE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(LANE / "scripts"))
sys.path.insert(0, "/Users/hoangminhlong/my-quantitative/research")

import duka_lib as D  # noqa: E402
from governance import heavy_lock  # noqa: E402

RAW_ROOT = LANE / "data_local" / "duka" / "M1"
DEFAULT_START, DEFAULT_END = dt.date(2021, 1, 1), dt.date(2026, 6, 30)


def daterange(a, b):
    d = a
    while d <= b:
        yield d
        d += dt.timedelta(days=1)


def atomic_write(path: Path, text: str) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text)
    tmp.replace(path)


def load_manifest(symbol: str) -> dict:
    p = LANE / "data_local" / "duka" / f"m1_manifest_{symbol}.json"
    if p.exists():
        return json.loads(p.read_text())
    return {
        "schema": "tracka_m1_manifest@1",
        "symbol": symbol,
        "window": [DEFAULT_START.isoformat(), DEFAULT_END.isoformat()],
        "files": {},
        "days_missing": [],
        "updated_at": None,
    }


def main() -> int:
    args = sys.argv[1:]
    if not args:
        print("usage: download_m1.py SYMBOL [START END] [budget_seconds]")
        return 2
    symbol = args[0]
    start = dt.date.fromisoformat(args[1]) if len(args) > 1 else DEFAULT_START
    end = dt.date.fromisoformat(args[2]) if len(args) > 2 else DEFAULT_END
    budget = float(args[3]) if len(args) > 3 else 480.0

    man_path = LANE / "data_local" / "duka" / f"m1_manifest_{symbol}.json"
    man = load_manifest(symbol)
    man["window"] = [min(man["window"][0], start.isoformat()),
                     max(man["window"][1], end.isoformat())]

    (RAW_ROOT / "BID" / symbol).mkdir(parents=True, exist_ok=True)
    (RAW_ROOT / "ASK" / symbol).mkdir(parents=True, exist_ok=True)

    lock = None
    status, note = "FAILED", ""
    try:
        try:
            lock = heavy_lock.acquire(
                cycle_id="ERP1-TRACKA-COHORT-1",
                role="datagate-download",
                worktree=str(LANE),
                command=[sys.executable, str(Path(__file__).resolve()), *args],
                expected_artifacts=[str(man_path)],
            )
        except heavy_lock.LockBusyError as e:
            print(json.dumps({"verdict": "NOT_RUN_RESOURCE_CONFLICT", "reason": str(e)}))
            return 4

        stop = threading.Event()

        def beat():
            while not stop.wait(30):
                try:
                    lock.heartbeat(extra={"symbol": symbol})
                except Exception:
                    pass

        threading.Thread(target=beat, daemon=True).start()

        fetcher = D.KeepAliveFetcher()
        t0 = time.time()
        fetched = skipped = missing = 0
        try:
            days = list(daterange(start, end))
            for i, day in enumerate(days):
                if time.time() - t0 > budget:
                    man["updated_at"] = dt.datetime.now(dt.timezone.utc).isoformat()
                    atomic_write(man_path, json.dumps(man, indent=1, sort_keys=True))
                    print(json.dumps({
                        "status": "PARTIAL", "symbol": symbol,
                        "fetched_this_run": fetched, "skipped": skipped,
                        "elapsed_s": round(time.time() - t0, 1),
                        "note": "budget exhausted — re-acquire lock and re-run"}))
                    stop.set()
                    fetcher.close()
                    lock.release(status="FINISHED",
                                 note=f"PARTIAL checkpoint after {fetched} files (budget)")
                    lock = None  # released explicitly; finally must not double-release
                    return 3
                y, m, d = day.year, day.month, day.day
                day0 = f"{y:04d}-{m:02d}-{d:02d}.bi5"
                for side in ("BID", "ASK"):
                    rel = f"{side}/{day0}"
                    key = f"{symbol}/{rel}"
                    dest = RAW_ROOT / side / symbol / day0
                    if dest.exists() and (prev := man["files"].get(key)) \
                            and prev.get("sha256") == hashlib.sha256(dest.read_bytes()).hexdigest():
                        skipped += 1
                        continue
                    raw = fetcher.fetch(D.candle_path(symbol, y, m, d, side))
                    if raw is None:
                        missing += 1
                        if day.isoformat() not in man["days_missing"]:
                            man["days_missing"].append(day.isoformat())
                        continue
                    dest.write_bytes(raw)
                    man["files"][key] = {
                        "sha256": hashlib.sha256(raw).hexdigest(),
                        "bytes": len(raw),
                        "remote": D.candle_path(symbol, y, m, d, side),
                    }
                    fetched += 1
                if i % 40 == 0:  # incremental checkpoint, atomic
                    man["updated_at"] = dt.datetime.now(dt.timezone.utc).isoformat()
                    atomic_write(man_path, json.dumps(man, indent=1, sort_keys=True))
                    lock.heartbeat(extra={"symbol": symbol, "day": day.isoformat()})
            man["updated_at"] = dt.datetime.now(dt.timezone.utc).isoformat()
            atomic_write(man_path, json.dumps(man, indent=1, sort_keys=True))
            n_files = len(man["files"])
            print(json.dumps({
                "status": "COMPLETE", "symbol": symbol, "files": n_files,
                "fetched_this_run": fetched, "skipped": skipped,
                "days_missing": man["days_missing"], "missing_count": missing,
                "elapsed_s": round(time.time() - t0, 1)}))
            status = "FINISHED" if not man["days_missing"] else "FINISHED_WITH_MISSING"
            if man["days_missing"]:
                note = f"{len(man['days_missing'])} day files 404"
            return 0
        finally:
            fetcher.close()
            stop.set()
    except Exception as e:  # noqa: BLE001
        status, note = "FAILED", f"{type(e).__name__}: {e}"[:400]
        raise
    finally:
        if lock is not None:
            lock.release(status=status, note=note)


if __name__ == "__main__":
    sys.exit(main())
