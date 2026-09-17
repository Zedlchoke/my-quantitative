#!/usr/bin/env python3
"""fxf-a2 lane fetch harness.

Etiquette frozen in canary_manifest.json: sequential, >=1s spacing,
<=2 retries exponential backoff (1s,2s) on network error / 5xx / 429,
no concurrency, single session, honest curl client, raw bytes as served.

Usage:
  lane_fetch.py fetch  <plan.json>          # plan: [{key, url, method, header?, save_as?}]
  lane_fetch.py probe   <plan.json>         # plan: [{key, url, method(HEAD|GET-range), ...}] -> census probes
  lane_fetch.py rehash  <rehash_plan.json>  # determinism: re-fetch listed raw files, compare sha256
All state lives in the lane dir (transcripts, index, counters).
"""
import json, os, subprocess, sys, time, hashlib
from datetime import datetime, timezone
from urllib.parse import urlparse

LANE = os.path.dirname(os.path.abspath(__file__))
RAW_ROOT = "/Users/hoangminhlong/.my-quantitative-data/fx-futures-frontier-v1/raw/lane-a2"
TRANSCRIPTS = os.path.join(LANE, "fetch_transcripts.jsonl")
INDEX = os.path.join(LANE, "raw_byte_index.json")
COUNTERS = os.path.join(LANE, "_counters.json")
BYTE_CAP = 300_000_000

def utcnow():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def load_json(p, default):
    if os.path.exists(p):
        with open(p) as f:
            return json.load(f)
    return default

def save_json(p, obj):
    tmp = p + ".tmp"
    with open(tmp, "w") as f:
        json.dump(obj, f, indent=2, sort_keys=True)
    os.replace(tmp, p)

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

def load_counters():
    return load_json(COUNTERS, {"bytes_downloaded_total": 0, "fetches": 0, "last_request_epoch": 0.0})

def save_counters(c):
    save_json(COUNTERS, c)

def log_transcript(rec):
    with open(TRANSCRIPTS, "a") as f:
        f.write(json.dumps(rec, sort_keys=True) + "\n")

def curl_once(url, method, headers, timeout=45):
    cmd = ["curl", "-sS", "--max-time", str(timeout), "-X", method,
           "-D", "-", "-o", "-", "-A", "curl/8.7.1 (research identity/canary fetch; raw-bytes evidence)"]
    cmd += ["-H", "Accept: */*"]
    for h in headers or []:
        cmd += ["-H", h]
    cmd.append(url)
    t0 = time.time()
    try:
        p = subprocess.run(cmd, capture_output=True, timeout=timeout + 10)
    except subprocess.TimeoutExpired:
        return {"net_error": "timeout", "elapsed": round(time.time() - t0, 3)}
    raw = p.stdout
    sep = raw.find(b"\r\n\r\n")
    head_b, body = (raw[:sep], raw[sep + 4:]) if sep >= 0 else (b"", raw)
    status = 0
    ctype = ""
    for line in head_b.decode("utf-8", "replace").splitlines():
        if line.upper().startswith("HTTP/"):
            parts = line.split()
            if len(parts) >= 2:
                status = int(parts[1])
        elif line.lower().startswith("content-type:"):
            ctype = line.split(":", 1)[1].strip()
        elif line.lower().startswith("location:"):
            pass
    return {"status": status, "content_type": ctype, "body": body, "head": head_b.decode("utf-8", "replace"),
            "elapsed": round(time.time() - t0, 3),
            "curl_err": p.stderr.decode("utf-8", "replace").strip() if p.returncode != 0 else ""}

def do_fetch(key, url, method="GET", headers=None, save_as=None, is_probe=False):
    c = load_counters()
    if c["bytes_downloaded_total"] > BYTE_CAP:
        print(json.dumps({"fatal": "BYTE_CAP_REACHED", "bytes": c["bytes_downloaded_total"]}))
        sys.exit(2)
    wait = c["last_request_epoch"] + 1.0 - time.time()
    if wait > 0:
        time.sleep(wait)
    attempt, backoff = 0, [1, 2]
    while True:
        r = curl_once(url, method, headers)
        c["last_request_epoch"] = time.time()
        retriable = (r.get("net_error") or (200 <= (r.get("status") or 0) < 300) is False and (
            r.get("status", 0) in (429,) or 500 <= r.get("status", 0) < 600 or r.get("net_error")))
        if retriable and attempt < 2:
            time.sleep(backoff[attempt]); attempt += 1; continue
        break
    body = r.get("body", b"")
    n = len(body)
    c["bytes_downloaded_total"] += n
    c["fetches"] += 1
    sha = hashlib.sha256(body).hexdigest() if body else None
    rec = {"key": key, "url": url, "method": method, "http_status": r.get("status"),
           "content_type": r.get("content_type", ""), "byte_size": n, "sha256": sha,
           "fetched_at_utc": utcnow(), "attempt": attempt, "elapsed_s": r.get("elapsed"),
           "net_error": r.get("net_error") or r.get("curl_err") or None,
           "is_probe": is_probe}
    saved_path = None
    if save_as and not r.get("net_error"):
        path = os.path.join(RAW_ROOT, save_as)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            f.write(body)
        rec["saved_as"] = save_as
        saved_path = path
    log_transcript(rec)
    save_counters(c)
    idx = load_json(INDEX, [])
    if saved_path:
        idx.append({"path": saved_path, "bytes": n, "sha256": sha, "url": url,
                    "method": method, "fetched_at_utc": rec["fetched_at_utc"], "key": key})
        save_json(INDEX, idx)
    print(json.dumps(rec))
    return rec, r

def main():
    mode, plan_path = sys.argv[1], sys.argv[2]
    plan = load_json(plan_path, [])
    if mode in ("fetch", "probe"):
        for spec in plan:
            do_fetch(spec["key"], spec["url"], spec.get("method", "GET"),
                     spec.get("headers"), spec.get("save_as"), is_probe=(mode == "probe"))
    elif mode == "rehash":
        results = []
        for spec in plan:
            orig = spec["path"]
            with open(orig, "rb") as f:
                orig_sha = hashlib.sha256(f.read()).hexdigest()
            rec, r = do_fetch("REHASH:" + spec["key"], spec["url"], spec.get("method", "GET"),
                              spec.get("headers"), save_as=None)
            new_sha = rec.get("sha256")
            results.append({"key": spec["key"], "url": spec["url"], "original_sha256": orig_sha,
                            "refetched_sha256": new_sha, "match": (orig_sha == new_sha),
                            "refetch_status": rec.get("http_status"),
                            "refetch_byte_size": rec.get("byte_size")})
        save_json(os.path.join(LANE, "determinism_refetch.json"),
                  {"mode": "re-fetch re-hash", "checked_at_utc": utcnow(), "results": results})
        print(json.dumps({"all_match": all(x["match"] for x in results)}))
    else:
        sys.exit("unknown mode")

if __name__ == "__main__":
    main()
