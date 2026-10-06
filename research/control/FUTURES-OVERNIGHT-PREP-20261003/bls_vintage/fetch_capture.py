#!/usr/bin/env python3
"""Fetch helper for P2C-BLS-VINTAGE: fetch URL -> save raw -> sha256 -> append fetch_log.jsonl.
Usage: fetch_capture.py <url> <outfile-basename> [timeout_sec]
Logs every attempt (success or failure) to fetch_log.jsonl in this directory.
Method is 'curl-direct' (plain curl, default UA, no spoofing) or noted in log.
"""
import hashlib
import json
import subprocess
import sys
import datetime
import os

BASE = os.path.dirname(os.path.abspath(__file__))


def utcnow():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def main():
    url, name = sys.argv[1], sys.argv[2]
    timeout = sys.argv[3] if len(sys.argv) > 3 else "45"
    out = os.path.join(BASE, "captures", name)
    attempt = 1  # caller ensures this URL+method is attempted <=2 times
    cmd = ["curl", "-sSL", "--max-time", timeout, "--compressed", url]
    try:
        r = subprocess.run(cmd, capture_output=True, timeout=int(timeout) + 15)
        body = r.stdout
        rc = r.returncode
        nbytes = len(body)
        if rc == 0 and nbytes > 0 and not body.startswith(b"<!DOCTYPE html>\n<html>\n<head>\n<meta charset=\"utf-8\" />\n<meta http-equiv=\"refresh\" content=\"0"):
            with open(out, "wb") as f:
                f.write(body)
            sha = hashlib.sha256(body).hexdigest()
            entry = {
                "utc": utcnow(), "method": "curl-direct", "attempt": attempt,
                "url": url, "outcome": f"OK saved {nbytes} bytes", "file": os.path.relpath(out, BASE),
                "sha256": sha,
            }
        else:
            err = r.stderr.decode("utf-8", "replace")[:300]
            entry = {
                "utc": utcnow(), "method": "curl-direct", "attempt": attempt,
                "url": url, "outcome": f"FAIL rc={rc} bytes={nbytes} err={err}",
            }
    except Exception as e:
        entry = {"utc": utcnow(), "method": "curl-direct", "attempt": attempt,
                 "url": url, "outcome": f"EXC {type(e).__name__}: {str(e)[:200]}"}
    with open(os.path.join(BASE, "fetch_log.jsonl"), "a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    print(json.dumps({k: entry.get(k) for k in ("utc", "url", "outcome", "sha256")}))


if __name__ == "__main__":
    main()
