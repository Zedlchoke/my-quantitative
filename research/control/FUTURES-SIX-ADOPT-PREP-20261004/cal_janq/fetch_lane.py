#!/usr/bin/env python
"""CAL-JANQ lane fetch driver.

TRANSPORT LAW (hard, from dispatch packet):
  permitted = WebFetch / web_reader / web.archive.org (CDX + snapshots) / plain curl ONLY
  <=2 attempts per URL/method; block => BLOCKED_TRANSPORT + stop that route; never bypass
  budget <=35 attempts total (counted here as every HTTP attempt)

Each attempt appends one JSONL line to fetch_log.jsonl with sha256 of saved bytes.
"""
import hashlib
import json
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

LANE = Path(__file__).resolve().parent
CAP = LANE / "captures"
LOG = LANE / "fetch_log.jsonl"
CAP.mkdir(exist_ok=True)

ATTEMPTS = {"n": 0}
BUDGET = 35
_TRIES: dict[str, int] = {}


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def log(line: dict) -> None:
    with LOG.open("a") as f:
        f.write(json.dumps(line) + "\n")


def curl(url: str, capture_name: str | None, note: str, method: str = "curl(web.archive.org)") -> dict:
    """One plain-curl attempt. Returns attempt record. Enforces <=2 tries/URL and budget."""
    key = f"{method}|{url}"
    if _TRIES.get(key, 0) >= 2:
        rec = {"utc": now(), "url": url, "method": method, "attempt": _TRIES[key] + 1,
               "outcome": "SKIP_METHOD_EXHAUSTED", "note": note + " [>=2 prior attempts, not sent]"}
        log(rec)
        return rec
    if ATTEMPTS["n"] >= BUDGET:
        rec = {"utc": now(), "url": url, "method": method, "attempt": 0,
               "outcome": "SKIP_BUDGET", "note": note + " [budget exhausted, not sent]"}
        log(rec)
        return rec
    ATTEMPTS["n"] += 1
    _TRIES[key] = _TRIES.get(key, 0) + 1
    t0 = time.time()
    r = subprocess.run(
        ["curl", "-sS", "-L", "--max-time", "50", "-w", "\n%{http_code}", url],
        capture_output=True, timeout=60,
    )
    out = r.stdout
    elapsed = round(time.time() - t0, 1)
    rc = r.returncode
    if rc != 0:
        rec = {"utc": now(), "url": url, "method": method, "attempt": _TRIES[key],
               "status": None, "curl_rc": rc, "bytes": 0, "sha256": None, "elapsed_s": elapsed,
               "outcome": "BLOCKED_TRANSPORT" if rc in (6, 7, 28, 35, 56) else "FAILED",
               "capture": None, "note": note + f" (curl rc={rc}: {r.stderr.decode()[:120]})"}
        log(rec)
        return rec
    body, _, code = out.rpartition(b"\n")
    http_code = code.strip().decode() or "000"
    sha = sha256_bytes(body)
    ok = http_code == "200" and len(body) > 0 and b"404" != http_code.encode()
    # Wayback interstitial detection: id_ replays of missing captures return small error bodies
    looks_bad = (len(body) < 60) or (b"<!DOCTYPE html" in body[:200] and capture_name and capture_name.endswith((".json", ".xls", ".txt")) and b"CmeWS" not in body[:4000] and len(body) < 200000 and capture_name is None)
    rec = {"utc": now(), "url": url, "method": method, "attempt": _TRIES[key],
           "status": http_code, "curl_rc": rc, "bytes": len(body), "sha256": sha,
           "elapsed_s": elapsed,
           "outcome": "SAVED" if (ok and not looks_bad) else ("FAILED" if http_code == "200" else f"FAILED(http={http_code})"),
           "capture": None, "note": note}
    if ok and not looks_bad and capture_name:
        (CAP / capture_name).write_bytes(body)
        rec["capture"] = f"captures/{capture_name}"
    if not ok:
        rec["outcome"] = f"FAILED(http={http_code})" if http_code != "200" else "FAILED_EMPTY_OR_INTERSTITIAL"
        if http_code == "404":
            rec["outcome"] = "NOT_IN_ARCHIVE(404)"
    log(rec)
    return rec


def now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


if __name__ == "__main__":
    import sys
    print(f"usage: import fetch_lane; fetch_lane.curl(url, name, note). attempts so far: {ATTEMPTS['n']}")
