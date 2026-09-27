#!/usr/bin/env python
"""DTP-CX-SOLUSDT-C1 data gate T2b — stage new monthly zips from Binance Vision.

Priority order: klines_1m, klines_15m (mandatory), then markPriceKlines_1m,
indexPriceKlines_1m (only while budget/disk remain). Guards:
  - hard floor: abort acquisition if free disk after a file would drop below
    5.0 GiB (BLOCKED_STORAGE, measured via df before each file)
  - staging budget: <=0.5 GB new bytes total (BLOCKED_BUDGET)
  - verify companion .CHECKSUM when served (else record absent)
  - own sha256 manifest per directory
State is written incrementally (resume-safe). ~0.5 s between requests.

Usage: dg_vision_stage.py <dataset>   (one of klines_1m klines_15m
       markPriceKlines_1m indexPriceKlines_1m)
"""
import hashlib, json, os, re, subprocess, sys, time
import requests

ROOT = ("/Users/hoangminhlong/my-quantitative/.worktrees/dtp-cx-solusdt-c1/"
        "integration/research/control/DTP-CX-SOLUSDT-C1/data_local")
STATE = os.path.join(ROOT, "vision", "_stage_state.jsonl")
BASE = "https://data.binance.vision/data/futures/um/monthly"
UA = {"User-Agent": "dtp-cx-solusdt-c1-data-gate/1.0 (research, keyless public archives)"}
FLOOR_BYTES = int(5.0 * 1024**3)          # 5.0 GiB
BUDGET_BYTES = 500_000_000                # 0.5 GB staging budget (new bytes)
DATASETS = {
    "klines_1m": ("klines", "1m", "klines_um_SOLUSDT_1m"),
    "klines_15m": ("klines", "15m", "klines_um_SOLUSDT_15m"),
    "markPriceKlines_1m": ("markPriceKlines", "1m", "markPriceKlines_um_SOLUSDT_1m"),
    "indexPriceKlines_1m": ("indexPriceKlines", "1m", "indexPriceKlines_um_SOLUSDT_1m"),
}


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


def append_state(row):
    with open(STATE, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(row) + "\n")


def already_done(dataset, tag):
    if not os.path.exists(STATE):
        return None
    with open(STATE, "r", encoding="utf-8") as fh:
        for line in fh:
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            if r.get("dataset") == dataset and r.get("month") == tag and r.get("status") == "STAGED":
                return r
    return None


def get(url, dest=None, attempts=3):
    for attempt in range(attempts):
        try:
            if dest is None:
                r = requests.get(url, headers=UA, timeout=30)
                return r.status_code, r.content
            with requests.get(url, headers=UA, timeout=60, stream=True) as r:
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


def parse_checksum(content):
    text = content.decode("utf-8", "replace")
    m = re.search(r"\b([0-9a-f]{64})\b", text)
    return m.group(1) if m else None


def main():
    dataset = sys.argv[1]
    endpoint, freq, dirname = DATASETS[dataset]
    outdir = os.path.join(ROOT, "vision", dirname)
    os.makedirs(outdir, exist_ok=True)
    # budget consumed so far (new bytes staged by this lane)
    staged = 0
    if os.path.exists(STATE):
        with open(STATE, "r", encoding="utf-8") as fh:
            for line in fh:
                try:
                    r = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if r.get("status") == "STAGED" and r.get("dataset") in DATASETS:
                    staged += r.get("bytes", 0)
    print(f"budget used before {dataset}: {staged} bytes; free={free_bytes()}", flush=True)
    for tag in months():
        if already_done(dataset, tag):
            continue
        fname = f"SOLUSDT-{freq}-{tag}.zip"
        fpath = os.path.join(outdir, fname)
        # probe size from prior HEAD probe for the guard
        head_url = f"{BASE}/{endpoint}/SOLUSDT/{freq}/{fname}"
        size_guess = None
        # hard disk-floor guard: measure free, require free - size >= floor
        fb = free_bytes()
        if size_guess is None:
            sc, head = get_head(head_url)
            time.sleep(0.5)
            if sc != 200:
                append_state({"dataset": dataset, "month": tag, "status": f"HTTP_{sc}",
                              "url": head_url})
                print(f"{dataset} {tag}: HTTP {sc}", flush=True)
                continue
            size_guess = head
        if fb - size_guess < FLOOR_BYTES:
            append_state({"dataset": dataset, "month": tag, "status": "BLOCKED_STORAGE",
                          "free_before": fb, "needed_bytes": size_guess,
                          "floor_bytes": FLOOR_BYTES, "url": head_url})
            print(f"{dataset} {tag}: BLOCKED_STORAGE (free {fb}, need {size_guess})", flush=True)
            sys.exit(2)
        if staged + size_guess > BUDGET_BYTES:
            append_state({"dataset": dataset, "month": tag, "status": "BLOCKED_BUDGET",
                          "staged_so_far": staged, "needed_bytes": size_guess,
                          "budget_bytes": BUDGET_BYTES, "url": head_url})
            print(f"{dataset} {tag}: BLOCKED_BUDGET (staged {staged} + {size_guess} > {BUDGET_BYTES})", flush=True)
            sys.exit(3)
        url = head_url
        st, _ = get(url, dest=fpath)
        if st != 200:
            append_state({"dataset": dataset, "month": tag, "status": f"HTTP_{st}",
                          "url": url})
            print(f"{dataset} {tag}: download HTTP {st}", flush=True)
            time.sleep(0.5)
            continue
        nbytes = os.path.getsize(fpath)
        digest = sha256_file(fpath)
        row = {"dataset": dataset, "month": tag, "file": os.path.relpath(fpath, ROOT),
               "bytes": nbytes, "sha256": digest, "url": url}
        # companion CHECKSUM
        cst, ccontent = get(url + ".CHECKSUM")
        time.sleep(0.5)
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
        staged += nbytes
        print(f"{dataset} {tag}: staged {nbytes}B sha={digest[:12]}.. {row['checksum_status']}", flush=True)
        time.sleep(0.5)
    print(f"{dataset} complete; staged_total={staged}", flush=True)


def get_head(url):
    try:
        r = requests.head(url, headers=UA, timeout=30, allow_redirects=True)
        return r.status_code, int(r.headers.get("Content-Length") or -1)
    except Exception:
        return -1, -1


if __name__ == "__main__":
    main()
