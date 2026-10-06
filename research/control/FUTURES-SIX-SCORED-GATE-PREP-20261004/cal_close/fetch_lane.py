#!/usr/bin/env python3
"""CAL-CLOSE lane fetch tool — plain curl via web.archive.org or official domains (bls.gov).
Logs EVERY attempt to fetch_log.jsonl (ts,url,method,tool,http_status,bytes,save_path).
<=2 attempts per (url,method) enforced by the caller's plan; <=30 attempts total.
No proxies, no SNI tricks, no logins, no live cmegroup.com."""
import json, subprocess, sys, hashlib, os, datetime, shlex

LANE = os.path.dirname(os.path.abspath(__file__))
LOG = os.path.join(LANE, "fetch_log.jsonl")

def attempt(url, save_path=None, method="curl(web.archive.org)", note="", timeout=90):
    cmd = ["curl", "-sS", "-L", "--max-time", str(timeout), "-w", "%{http_code}", "-o", "/tmp/ccl_body.bin", url]
    t0 = datetime.datetime.now(datetime.timezone.utc)
    r = subprocess.run(cmd, capture_output=True)
    dt = (datetime.datetime.now(datetime.timezone.utc) - t0).total_seconds()
    body = open("/tmp/ccl_body.bin", "rb").read() if os.path.exists("/tmp/ccl_body.bin") else b""
    http_status = None
    err = r.stderr.decode(errors="replace").strip()
    # last token of stdout is the -w http_code (body went to file)
    out = r.stdout.decode(errors="replace").strip()
    if out and out.split()[-1].isdigit():
        http_status = int(out.split()[-1])
    sha = hashlib.sha256(body).hexdigest() if body else None
    saved = None
    if save_path and http_status == 200 and body:
        p = os.path.join(LANE, save_path)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        open(p, "wb").write(body)
        saved = save_path
    rec = {
        "ts": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "url": url, "method": method, "tool": "curl",
        "http_status": http_status, "curl_rc": r.returncode,
        "bytes": len(body) if body else 0, "sha256": sha,
        "elapsed_s": round(dt, 1), "save_path": saved, "note": note,
    }
    if err and http_status is None:
        rec["error"] = err[:300]
    with open(LOG, "a") as f:
        f.write(json.dumps(rec) + "\n")
    print(json.dumps(rec))
    return rec

if __name__ == "__main__":
    plan = json.load(open(sys.argv[1]))
    for step in plan:
        attempt(**step)
