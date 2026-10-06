#!/usr/bin/env python3
"""CALCOST lane fetch helper — plain curl only, full logging, sha256 pinning.
Transport law: permitted routes = plain curl / web.archive.org / WebFetch / web_reader.
Every HTTP attempt must go through log_fetch() (or be retro-logged identically).
MAX 2 attempts per URL enforced by attempts index in fetch_log.jsonl.
"""
import hashlib, json, subprocess, sys, time
from datetime import datetime, timezone
from pathlib import Path

LANE = Path(__file__).resolve().parent
LOG = LANE / "fetch_log.jsonl"
CAP = LANE / "captures"
CAP.mkdir(exist_ok=True)


def url_attempts(url):
    n = 0
    if LOG.exists():
        for line in LOG.read_text().splitlines():
            if not line.strip():
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if rec.get("url") == url:
                n += 1
    return n


def log_fetch(tool, url, status, nbytes, saved_path=None, sha256=None, note=""):
    rec = {
        "utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "tool": tool,
        "url": url,
        "http_status": status,
        "bytes": nbytes,
        "saved_path": saved_path,
        "sha256": sha256,
        "note": note,
    }
    with LOG.open("a") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return rec


def curl_fetch(url, save_name, note="", max_bytes=80_000_000, timeout=90):
    """Plain curl GET. Enforces <=2 attempts per URL (fails hard on 3rd)."""
    used = url_attempts(url)
    if used >= 2:
        raise RuntimeError(f"transport-law violation refused: {url} already attempted {used}x")
    dest = CAP / save_name
    t0 = time.time()
    p = subprocess.run(
        ["curl", "-sSL", "--max-time", str(timeout), "-w", "%{http_code}", "-o", str(dest), url],
        capture_output=True, text=True, timeout=timeout + 30,
    )
    status = p.stdout.strip()[-3:] if p.stdout.strip() else "ERR"
    err = p.stderr.strip()[:200]
    if dest.exists():
        data = dest.read_bytes()[:max_bytes]
        nbytes = dest.stat().st_size
        sha = hashlib.sha256(data).hexdigest()
    else:
        nbytes, sha = 0, None
    rec = log_fetch("curl", url, status, nbytes, str(dest.relative_to(LANE)) if dest.exists() else None, sha,
                    note=note + (f" | curl_stderr={err}" if err and status in ("ERR", "000") else ""))
    print(json.dumps(rec))
    return rec, dest


if __name__ == "__main__":
    url, save_name = sys.argv[1], sys.argv[2]
    note = sys.argv[3] if len(sys.argv) > 3 else ""
    rec, dest = curl_fetch(url, save_name, note)
    sys.exit(0 if rec["http_status"].startswith("2") else 1)
