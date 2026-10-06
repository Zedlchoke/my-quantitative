#!/usr/bin/env python
"""CAL-EB lane fetch tool (FUTURES-SIX-ADOPT-PREP-20261004).

Transport law (hard):
  permitted = plain curl to web.archive.org ONLY (CDX queries + id_ snapshots).
  <=2 attempts per URL per method; on connection-level block => BLOCKED_TRANSPORT
  and STOP that route. No proxies, no SNI tricks, no logins, no live cmegroup.com.
  Lane budget: <=35 total attempts.

Every fetch: raw bytes saved under captures/ (when 200 + non-empty), sha256
recorded, one JSON line appended to fetch_log.jsonl.
"""
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

LANE = Path(__file__).resolve().parent
CAP = LANE / "captures"
CAP.mkdir(exist_ok=True)
LOG = LANE / "fetch_log.jsonl"
BUDGET_FILE = LANE / ".budget_state.json"


def load_state():
    if BUDGET_FILE.exists():
        return json.loads(BUDGET_FILE.read_text())
    return {"total_attempts": 0, "per_url": {}}


def save_state(s):
    BUDGET_FILE.write_text(json.dumps(s, indent=1))


def fetch(url, capture_name=None, note="", method="curl(web.archive.org)"):
    state = load_state()
    if state["total_attempts"] >= 35:
        print(json.dumps({"outcome": "BUDGET_EXHAUSTED", "url": url}))
        return None
    n = state["per_url"].get(f"{method}|{url}", 0)
    if n >= 2:
        print(json.dumps({"outcome": "ATTEMPT_LIMIT_REACHED", "url": url}))
        return None
    state["total_attempts"] += 1
    state["per_url"][f"{method}|{url}"] = n + 1
    save_state(state)

    t0 = time.time()
    p = subprocess.run(
        ["curl", "-sS", "--max-time", "90", "-w", "\n%{http_code}", url],
        capture_output=True,
    )
    elapsed = round(time.time() - t0, 1)
    out = p.stdout
    rc = p.returncode
    # split trailing status line
    if b"\n" in out:
        body, _, code = out.rpartition(b"\n")
    else:
        body, code = out, b"0"
    code = code.decode().strip() or "0"
    rec = {
        "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "url": url,
        "method": method,
        "attempt": n + 1,
        "status": code,
        "curl_rc": rc,
        "bytes": len(body),
        "sha256": hashlib.sha256(body).hexdigest() if body else "",
        "elapsed_s": elapsed,
    }
    if rc != 0:
        rec["outcome"] = "CURL_ERROR"
        rec["note"] = f"curl rc={rc}: connection-level failure => BLOCKED_TRANSPORT if persistent"
        rec["stderr_tail"] = p.stderr.decode(errors="replace")[-200:]
    elif code == "200" and body:
        rec["outcome"] = "SAVED"
        capture_name = capture_name or ("cap_%d.bin" % state["total_attempts"])
        (CAP / capture_name).write_bytes(body)
        rec["capture"] = f"captures/{capture_name}"
    elif code == "200" and not body:
        rec["outcome"] = "EMPTY_200"
    else:
        rec["outcome"] = f"HTTP_{code}"
    rec["note"] = note
    with LOG.open("a") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(json.dumps(rec, ensure_ascii=False)[:400])
    return rec


if __name__ == "__main__":
    url = sys.argv[1]
    cap = sys.argv[2] if len(sys.argv) > 2 else None
    note = sys.argv[3] if len(sys.argv) > 3 else ""
    fetch(url, cap, note)
