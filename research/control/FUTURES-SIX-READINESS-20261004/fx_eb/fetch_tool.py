#!/usr/bin/env python
"""FX-EB-CALENDAR lane fetch tool.

TRANSPORT LAW (binding):
- permitted routes ONLY: plain curl to web.archive.org (this tool), WebFetch
  tool, mcp web_reader. This tool implements curl-to-web.archive.org only.
- max 2 attempts per URL per method; on connection-level block record
  BLOCKED_TRANSPORT and move on. No SNI tricks, no proxies, no logins.
- every attempt logged to fetch_log.jsonl (utc/url/method/status/bytes/sha256).

Usage:
  fetch_tool.py <url> <out_name> [note]

Saves to captures/<out_name> relative to the fx_eb lane dir.
Refuses non web.archive.org targets (unmodified identity curl; no UA spoof).
"""
import hashlib
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

LANE = Path(__file__).resolve().parent
CAPTURES = LANE / "captures"
LOG = LANE / "fetch_log.jsonl"


def log(record):
    with open(LOG, "a") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def now_utc():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def fetch_once(url, out_path):
    """Single curl attempt, unmodified identity, plain https to web.archive.org."""
    cmd = [
        "curl", "-sS", "-L", "--max-time", "90", "-o", str(out_path),
        "-w", "%{http_code}", url,
    ]
    t0 = time.time()
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    dt = round(time.time() - t0, 1)
    rc = proc.returncode
    code = proc.stdout.strip()[-3:] if proc.stdout.strip() else "000"
    size = out_path.stat().st_size if out_path.exists() else 0
    return rc, code, size, dt, proc.stderr.strip()[:200]


def main():
    url, out_name = sys.argv[1], sys.argv[2]
    note = sys.argv[3] if len(sys.argv) > 3 else ""
    if "web.archive.org" not in url:
        print("REFUSED: this tool only fetches web.archive.org (permitted route)")
        sys.exit(2)
    CAPTURES.mkdir(exist_ok=True)
    out_path = CAPTURES / out_name
    for attempt in (1, 2):
        rc, code, size, dt, err = fetch_once(url, out_path)
        sha = hashlib.sha256(out_path.read_bytes()).hexdigest() if size else ""
        ok = rc == 0 and code == "200" and size > 0
        rec = {
            "utc": now_utc(),
            "url": url,
            "method": "curl(web.archive.org)",
            "attempt": attempt,
            "status": code,
            "curl_rc": rc,
            "bytes": size,
            "sha256": sha,
            "elapsed_s": dt,
            "outcome": "SAVED" if ok else "FAILED",
            "capture": f"captures/{out_name}" if ok else "",
            "note": note,
        }
        if err:
            rec["stderr"] = err
        log(rec)
        print(json.dumps({k: rec[k] for k in ("utc", "status", "curl_rc", "bytes", "outcome", "attempt")}))
        if ok:
            return
        if rc == 7:  # connection refused -> archive rate-limit; backoff once
            time.sleep(45)
        else:
            time.sleep(6)
    # both attempts exhausted -> leave FAILED records (no 0-byte leftovers)
    if out_path.exists() and out_path.stat().st_size == 0:
        out_path.unlink()
    sys.exit(1)


if __name__ == "__main__":
    main()
