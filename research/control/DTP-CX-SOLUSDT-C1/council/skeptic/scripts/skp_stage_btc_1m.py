#!/usr/bin/env python
"""DTP-CX-SOLUSDT-C1 skeptic court (lane SKP) — stage BTCUSDT 1m monthly zips
from Binance Vision into data_local/vision/klines_um_BTCUSDT_1m/.

Conventions copied from dg_vision_stage.py (dg lane); skeptic lane keeps its OWN
state file and manifest INSIDE the staged directory (lane write boundary).
Guards (dispatch hard laws):
  - df guard before every file: if free_bytes - size < 5.0 GiB => NO staging,
    status NOT_RUN_DISK (censuses must then be marked NOT_RUN_DISK).
  - skeptic staging budget: <=150 MB new bytes (dispatch est. 110-130 MB).
  - companion .CHECKSUM fetched + verified per file; sha256 manifest written.
Usage: skp_stage_btc_1m.py [probe]
"""
import hashlib, json, os, re, sys, time
import requests

ROOT = ("/Users/hoangminhlong/my-quantitative/.worktrees/dtp-cx-solusdt-c1/"
        "integration/research/control/DTP-CX-SOLUSDT-C1/data_local/vision")
OUTDIR = os.path.join(ROOT, "klines_um_BTCUSDT_1m")
STATE = os.path.join(OUTDIR, "_stage_state_skp.jsonl")
BASE = "https://data.binance.vision/data/futures/um/monthly"
UA = {"User-Agent": "dtp-cx-solusdt-c1-skeptic/1.0 (research, keyless public archives)"}
FLOOR_BYTES = int(5.0 * 1024**3)
BUDGET_BYTES = 150_000_000


def free_bytes():
    st = os.statvfs("/")
    return st.f_bavail * st.f_frsize


def months():
    out = []
    for y in range(2020, 2027):
        for m in range(1, 13):
            tag = f"{y}-{m:02d}"
            if "2020-09" <= tag <= "2026-08":
                out.append(tag)
    return out


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        while True:
            b = fh.read(8 * 1024 * 1024)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def already_done(tag):
    if not os.path.exists(STATE):
        return None
    with open(STATE, encoding="utf-8") as fh:
        for line in fh:
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            if r.get("month") == tag and r.get("status") == "STAGED":
                return r
    return None


def get(url, dest=None, attempts=3):
    for attempt in range(attempts):
        try:
            if dest is None:
                r = requests.get(url, headers=UA, timeout=30)
                return r.status_code, r.content
            with requests.get(url, headers=UA, timeout=120, stream=True) as r:
                if r.status_code != 200:
                    return r.status_code, None
                tmp = dest + ".tmp"
                with open(tmp, "wb") as fh:
                    for chunk in r.iter_content(1024 * 1024):
                        fh.write(chunk)
                os.replace(tmp, dest)
                return 200, None
        except Exception:
            if dest and os.path.exists(dest + ".tmp"):
                try:
                    os.remove(dest + ".tmp")
                except OSError:
                    pass
            if attempt == attempts - 1:
                raise
            time.sleep(2.0 * (attempt + 1))
    raise RuntimeError("unreachable")


def head(url):
    try:
        r = requests.head(url, headers=UA, timeout=30, allow_redirects=True)
        return r.status_code, int(r.headers.get("Content-Length") or -1)
    except Exception:
        return -1, -1


def parse_checksum(content):
    m = re.search(r"\b([0-9a-f]{64})\b", content.decode("utf-8", "replace"))
    return m.group(1) if m else None


def append_state(row):
    with open(STATE, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(row) + "\n")


def main():
    probe_only = len(sys.argv) > 1 and sys.argv[1] == "probe"
    os.makedirs(OUTDIR, exist_ok=True)
    staged = 0
    if os.path.exists(STATE):
        with open(STATE, encoding="utf-8") as fh:
            for line in fh:
                try:
                    r = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if r.get("status") == "STAGED":
                    staged += r.get("bytes", 0)
    fb = free_bytes()
    print(f"free_before={fb} ({fb/1024**3:.2f} GiB); staged_prior={staged}", flush=True)
    if probe_only:
        total = 0
        for tag in months():
            url = f"{BASE}/klines/BTCUSDT/1m/BTCUSDT-1m-{tag}.zip"
            sc, size = head(url)
            total += max(size, 0)
            print(f"probe {tag}: HTTP {sc} {size}B", flush=True)
            time.sleep(0.4)
        print(f"probe_total_bytes={total} free_after={free_bytes()}", flush=True)
        return
    rows = []
    blocked = False
    for tag in months():
        if already_done(tag):
            continue
        fname = f"BTCUSDT-1m-{tag}.zip"
        fpath = os.path.join(OUTDIR, fname)
        url = f"{BASE}/klines/BTCUSDT/1m/{fname}"
        sc, size = head(url)
        time.sleep(0.4)
        if sc != 200:
            append_state({"month": tag, "status": f"HTTP_{sc}", "url": url})
            print(f"{tag}: HTTP {sc}", flush=True)
            continue
        if free_bytes() - size < FLOOR_BYTES:
            append_state({"month": tag, "status": "NOT_RUN_DISK", "free_before": free_bytes(),
                          "needed_bytes": size, "floor_bytes": FLOOR_BYTES, "url": url})
            print(f"{tag}: NOT_RUN_DISK (free {free_bytes()}, need {size})", flush=True)
            blocked = True
            break
        if staged + size > BUDGET_BYTES:
            append_state({"month": tag, "status": "BLOCKED_BUDGET", "staged_so_far": staged,
                          "needed_bytes": size, "budget_bytes": BUDGET_BYTES, "url": url})
            print(f"{tag}: BLOCKED_BUDGET", flush=True)
            blocked = True
            break
        st, _ = get(url, dest=fpath)
        if st != 200:
            append_state({"month": tag, "status": f"HTTP_{st}", "url": url})
            print(f"{tag}: download HTTP {st}", flush=True)
            time.sleep(0.5)
            continue
        nbytes = os.path.getsize(fpath)
        digest = sha256_file(fpath)
        row = {"month": tag, "file": os.path.relpath(fpath, ROOT), "bytes": nbytes,
               "sha256": digest, "url": url}
        cst, ccontent = get(url + ".CHECKSUM")
        time.sleep(0.4)
        if cst == 200:
            expected = parse_checksum(ccontent)
            row["checksum_status"] = "MATCH" if expected == digest else (
                "MISMATCH" if expected else "CHECKSUM_UNPARSED")
            if expected and expected != digest:
                row["checksum_expected"] = expected
        else:
            row["checksum_status"] = f"CHECKSUM_HTTP_{cst}"
        row["status"] = "STAGED"
        append_state(row)
        rows.append(row)
        staged += nbytes
        print(f"{tag}: staged {nbytes}B sha={digest[:12]}.. {row['checksum_status']}", flush=True)
        time.sleep(0.4)
    # manifest
    with open(STATE, encoding="utf-8") as fh:
        all_rows = [json.loads(l) for l in fh if l.strip()]
    manifest = {
        "schema": "dtp/skp_sha256_manifest@1",
        "cycle_id": "DTP-CX-SOLUSDT-C1",
        "lane": "skp (economic skeptic)",
        "dataset": "klines_um_BTCUSDT_1m",
        "source_base": BASE,
        "span": "2020-09..2026-08",
        "n_files_expected": 72,
        "n_files_staged": sum(1 for r in all_rows if r.get("status") == "STAGED"),
        "bytes_total": sum(r.get("bytes", 0) for r in all_rows if r.get("status") == "STAGED"),
        "checksum_match": sum(1 for r in all_rows if r.get("status") == "STAGED" and r.get("checksum_status") == "MATCH"),
        "free_before_bytes": fb,
        "free_after_bytes": free_bytes(),
        "floor_bytes": FLOOR_BYTES,
        "blocked": blocked,
        "rows": [r for r in all_rows if r.get("status") == "STAGED"],
    }
    with open(os.path.join(OUTDIR, "MANIFEST_sha256.json"), "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=1)
    print(f"manifest written; staged_total={manifest['bytes_total']} free_after={free_bytes()}", flush=True)


if __name__ == "__main__":
    main()
