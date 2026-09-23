"""STOCKS-AMIHUD-V1 P0 heavy crawl: /eod per frozen-universe code, 2017-07-01..2022-12-31.

Machine-wide heavy lock REQUIRED (this is the heavy download worker).
Resumable: codes already recorded in crawl_census.jsonl with a stored raw
file are skipped on restart. Raw pulls stay OUT of git (staging dir has its
own .gitignore); the manifest (sha256 per raw) and census are the committed
evidence. Token never echoed.
"""
from __future__ import annotations

import hashlib
import json
import os
import random
import sys
import time
import traceback
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

REPO = Path("/Users/hoangminhlong/my-quantitative")
sys.path.insert(0, str(REPO))
from research.governance import heavy_lock  # noqa: E402

HERE = Path(__file__).resolve().parent          # .../research/control/stocks_amihud_v1/p0
STAGING = HERE / "staging_eod"
STAGING.mkdir(exist_ok=True)
(STAGING / ".gitignore").write_text("*\n!.gitignore\n")
CENSUS = HERE / "crawl_census.jsonl"
MANIFEST = HERE / "crawl_manifest.jsonl"
PROGRESS = HERE / "crawl_progress.log"
ENV_PATH = REPO / ".env"
BASE = "https://eodhd.com/api"
WINDOW = {"from": "2017-07-01", "to": "2022-12-31"}
SLEEP = 0.25
HEARTBEAT_EVERY = 100
EXTRA = ["SPY", "AAPL", "TSLA"]  # benchmark + in-window split fixtures (full window)


def load_token() -> str:
    for line in ENV_PATH.read_text().splitlines():
        if line.startswith("EODHD_API_KEY="):
            return line.split("=", 1)[1].strip()
    raise SystemExit("EODHD_API_KEY missing")


TOKEN = load_token()
_ERR_TAIL = [""]


def log(msg: str) -> None:
    with PROGRESS.open("a") as f:
        f.write(f"{datetime.now(timezone.utc).isoformat()} {msg}\n")


def fetch(code: str) -> tuple[int, bytes]:
    q = {"from": WINDOW["from"], "to": WINDOW["to"], "fmt": "json", "api_token": TOKEN}
    url = f"{BASE}/eod/{code}.US?{urllib.parse.urlencode(q)}"
    req = urllib.request.Request(url, headers={"User-Agent": "stocks-amihud-v1-p0-crawl/1.0"})
    last_err = None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                return r.status, r.read()
        except urllib.error.HTTPError as e:
            if e.code >= 500 and attempt < 2:
                last_err = f"HTTP{e.code}"
                time.sleep(2 * (attempt + 1) + random.random())
                continue
            return e.code, e.read()[:256]
        except Exception as e:  # timeouts, TLS resets
            last_err = repr(e)[:120]
            if attempt < 2:
                time.sleep(2 * (attempt + 1) + random.random())
                continue
            raise
    return 0, last_err.encode()


def parse_rows(payload: bytes):
    try:
        v = json.loads(payload)
        return v if isinstance(v, list) else []
    except Exception:
        return []


def main() -> int:
    uni = json.loads((HERE / "universe_frozen.json").read_text())
    codes = sorted(uni["codes"].keys())
    todo = list(codes) + [c for c in EXTRA if c not in codes]
    done: set[str] = set()
    if CENSUS.exists():
        for line in CENSUS.read_text().splitlines():
            try:
                rec = json.loads(line)
                if rec.get("stored") and (STAGING / f"{rec['code']}.json").exists():
                    done.add(rec["code"])
            except Exception:
                continue
    log(f"crawl start: universe={len(codes)} todo={len(todo)} already_done={len(done)}")
    handle = heavy_lock.acquire(
        cycle_id="STOCKS-AMIHUD-V1",
        role="p0-eod-crawl",
        worktree=str(REPO / ".worktrees/stocks-amihud-v1/integration"),
        command=[".venv/bin/python", str(Path(__file__))],
        expected_artifacts=[str(CENSUS), str(MANIFEST)],
    )
    n_new = 0
    try:
        with CENSUS.open("a") as cf, MANIFEST.open("a") as mf:
            for i, code in enumerate(todo):
                if code in done:
                    continue
                try:
                    st, b = fetch(code)
                except Exception as e:
                    _ERR_TAIL[0] = traceback.format_exc()[-2000:]
                    log(f"FATAL fetch {code}: {e!r}")
                    handle.release(status="FAILED", note=f"fetch {code} failed: {e!r}; stderr_tail={_ERR_TAIL[0][-500:]}")
                    return 2
                rows = parse_rows(b)
                p = STAGING / f"{code}.json"
                if rows:
                    p.write_bytes(b)
                rec = {"code": code, "http": st, "rows": len(rows),
                       "first": rows[0].get("date") if rows else None,
                       "last": rows[-1].get("date") if rows else None,
                       "stored": bool(rows), "sha256": hashlib.sha256(b).hexdigest() if rows else None}
                cf.write(json.dumps(rec) + "\n")
                if rows:
                    mf.write(json.dumps({"code": code, "sha256": rec["sha256"],
                                         "bytes": len(b)}) + "\n")
                n_new += 1
                if n_new % HEARTBEAT_EVERY == 0:
                    cf.flush(); mf.flush()
                    handle.heartbeat(extra={"done": len(done) + n_new, "todo_total": len(todo)})
                    log(f"progress {len(done)+n_new}/{len(todo)} (last={code} rows={len(rows)})")
                time.sleep(SLEEP + random.random() * 0.1)
        handle.heartbeat(extra={"done": len(done) + n_new, "todo_total": len(todo)})
        log(f"crawl complete: newly_pulled={n_new} total_covered={len(done)+n_new}/{len(todo)}")
        handle.release(status="FINISHED", note=f"p0 /eod crawl complete: {len(done)+n_new}/{len(todo)} codes covered")
        return 0
    except Exception:
        _ERR_TAIL[0] = traceback.format_exc()[-2000:]
        log("FATAL: " + _ERR_TAIL[0])
        handle.release(status="TECHABORT", note=f"stderr_tail={_ERR_TAIL[0][-800:]}")
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
