"""STOCKS-AMIHUD-V1 P0 heavy crawl v2: 8-thread CSV /eod pull, 2017-07-01..2022-12-31.

v1 (sequential JSON) measured ~5-13s/request on this host — per-connection
throttling (6 parallel probes: ~88KB/s aggregate vs ~15KB/s single-stream,
measured 2026-09-23, see P0 notes). v2: fmt=csv (2.2x smaller), 8 workers,
per-thread persistent HTTPS connections. Same resumable census/manifest
(CSV staging). Machine-wide heavy lock REQUIRED. Token never echoed.
"""
from __future__ import annotations

import hashlib
import http.client
import json
import os
import queue
import random
import sys
import threading
import time
import traceback
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path

REPO = Path("/Users/hoangminhlong/my-quantitative")
sys.path.insert(0, str(REPO))
from research.governance import heavy_lock  # noqa: E402

HERE = Path(__file__).resolve().parent
STAGING = HERE / "staging_eod_csv"
STAGING.mkdir(exist_ok=True)
(STAGING / ".gitignore").write_text("*\n!.gitignore\n")
CENSUS = HERE / "crawl_census_v2.jsonl"
MANIFEST = HERE / "crawl_manifest_v2.jsonl"
PROGRESS = HERE / "crawl_progress.log"
ENV_PATH = REPO / ".env"
HOST = "eodhd.com"
PATH_TMPL = "/api/eod/{}.US?{}"
WINDOW = {"from": "2017-07-01", "to": "2022-12-31"}
N_WORKERS = 8
HEARTBEAT_EVERY = 250
EXTRA = ["SPY", "AAPL", "TSLA"]

UA = "stocks-amihud-v1-p0-crawl/2.0"


def load_token() -> str:
    for line in ENV_PATH.read_text().splitlines():
        if line.startswith("EODHD_API_KEY="):
            return line.split("=", 1)[1].strip()
    raise SystemExit("EODHD_API_KEY missing")


TOKEN = load_token()
QUERY = urllib.parse.urlencode({"from": WINDOW["from"], "to": WINDOW["to"],
                                "fmt": "csv", "api_token": TOKEN})
write_lock = threading.Lock()
out_q: "queue.Queue[dict]" = queue.Queue()


class Worker(threading.Thread):
    def __init__(self, inbox: "queue.Queue[str]"):
        super().__init__(daemon=True)
        self.inbox = inbox
        self.conn: http.client.HTTPSConnection | None = None

    def _get(self, code: str) -> tuple[int, bytes]:
        path = PATH_TMPL.format(code, QUERY)
        for attempt in range(3):
            try:
                if self.conn is None:
                    self.conn = http.client.HTTPSConnection(HOST, timeout=60)
                self.conn.request("GET", path, headers={"User-Agent": UA,
                                                        "Accept": "text/csv"})
                r = self.conn.getresponse()
                body = r.read()
                return r.status, body
            except Exception:
                try:
                    if self.conn:
                        self.conn.close()
                except Exception:
                    pass
                self.conn = None
                if attempt == 2:
                    raise
                time.sleep(1.5 * (attempt + 1) + random.random())
        return 0, b""

    def run(self) -> None:
        while True:
            try:
                code = self.inbox.get_nowait()
            except queue.Empty:
                return
            try:
                st, b = self._get(code)
            except Exception as e:
                out_q.put({"code": code, "fatal": repr(e)[:200]})
                return
            n_lines = b.count(b"\n") if b else 0
            has_header = b.startswith(b"Date,")
            rows = max(n_lines - 1, 0) if has_header else 0
            first = last = None
            if has_header and rows:
                lines = b.decode("utf-8", errors="replace").splitlines()
                first = lines[1].split(",", 1)[0]
                last = lines[-1].split(",", 1)[0]
            if rows:
                (STAGING / f"{code}.csv").write_bytes(b)
            out_q.put({"code": code, "http": st, "rows": rows,
                       "first": first, "last": last, "stored": bool(rows),
                       "sha256": hashlib.sha256(b).hexdigest() if rows else None,
                       "bytes": len(b)})
            self.inbox.task_done()


def log(msg: str) -> None:
    with PROGRESS.open("a") as f:
        f.write(f"{datetime.now(timezone.utc).isoformat()} {msg}\n")


def main() -> int:
    uni = json.loads((HERE / "universe_frozen.json").read_text())
    codes = sorted(uni["codes"].keys())
    todo = list(codes) + [c for c in EXTRA if c not in codes]
    done: set[str] = set()
    if CENSUS.exists():
        for line in CENSUS.read_text().splitlines():
            try:
                rec = json.loads(line)
                if rec.get("stored") and (STAGING / f"{rec['code']}.csv").exists():
                    done.add(rec["code"])
            except Exception:
                continue
    inbox: "queue.Queue[str]" = queue.Queue()
    remaining = 0
    for c in todo:
        if c not in done:
            inbox.put(c)
            remaining += 1
    log(f"crawl v2 start: universe={len(codes)} todo_total={len(todo)} "
        f"already_done={len(done)} remaining={remaining} workers={N_WORKERS}")
    handle = heavy_lock.acquire(
        cycle_id="STOCKS-AMIHUD-V1",
        role="p0-eod-crawl-v2",
        worktree=str(REPO / ".worktrees/stocks-amihud-v1/integration"),
        command=[".venv/bin/python", str(Path(__file__))],
        expected_artifacts=[str(CENSUS), str(MANIFEST)],
    )
    fatal: list[str] = []
    processed = 0
    try:
        workers = [Worker(inbox) for _ in range(N_WORKERS)]
        for w in workers:
            w.start()
        with CENSUS.open("a") as cf, MANIFEST.open("a") as mf:
            while any(w.is_alive() for w in workers) or not out_q.empty():
                try:
                    rec = out_q.get(timeout=5)
                except queue.Empty:
                    continue
                if rec.get("fatal"):
                    fatal.append(f"{rec['code']}: {rec['fatal']}")
                    break
                cf.write(json.dumps(rec) + "\n")
                if rec.get("stored"):
                    mf.write(json.dumps({"code": rec["code"], "sha256": rec["sha256"],
                                         "bytes": rec["bytes"]}) + "\n")
                processed += 1
                if processed % HEARTBEAT_EVERY == 0:
                    cf.flush(); mf.flush()
                    handle.heartbeat(extra={"done": len(done) + processed,
                                            "todo_total": len(todo)})
                    log(f"progress {len(done)+processed}/{len(todo)} "
                        f"(last={rec['code']} rows={rec['rows']})")
                if inbox.empty() and not any(w.is_alive() for w in workers):
                    break
            cf.flush(); mf.flush()
        if fatal:
            handle.release(status="FAILED",
                           note=f"worker fatal: {fatal[0][:300]}; processed={processed}")
            log(f"FATAL: {fatal[0]}")
            return 2
        handle.heartbeat(extra={"done": len(done) + processed, "todo_total": len(todo)})
        log(f"crawl v2 complete: newly_pulled={processed} "
            f"total_covered={len(done)+processed}/{len(todo)}")
        handle.release(status="FINISHED",
                       note=f"p0 /eod csv crawl complete: {len(done)+processed}/{len(todo)} codes")
        return 0
    except Exception:
        tail = traceback.format_exc()[-1500:]
        log("FATAL: " + tail)
        handle.release(status="TECHABORT", note=f"stderr_tail={tail[-800:]}")
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
