"""V8 P0a leg 2: SEC submissions survivorship cohort census.

The leg never yet run in the stocks program (PLAN_stocks_v7.md section 6 P0c,
inherited by PLAN_stocks_v8.md section 4): per filer SEC-recorded status
history -- names, ticker lineage, termination-of-registration filings --
so delisted names keep their history and the cohort is survivorship-aware.

Evidence taxonomy (LESSONS P-1): every census field is tagged
  EVIDENCED  - copied from the SEC submissions record (dates, forms, names)
  DERIVED    - computed by the rules stated in STATUS_RULES below
Nothing about delisting is inferred beyond SEC-recorded facts; a filer with
no Form 15 is never called delisted by this script.

Usage:
  python p0a_v8_submissions_census.py fetch   # resumable raw pulls
  python p0a_v8_submissions_census.py build   # census artifact + manifest
"""

import hashlib
import json
import os
import sys
import time
import urllib.request
import datetime

RAW_DIR = ".staging_sec_v8/submissions"
ENTITIES = ".staging_sec_v8/_panel_entities.json"
OUT = "research/control/stocks_free_v8_run/p0a_submissions_cohort_census.json"
RAW_MANIFEST = "research/control/stocks_free_v8_run/p0a_raw_hash_manifest.json"
UA = "my-quantitative internal research agent (owner-directed; contact via repo)"
S0_START, S0_END = "2018-04-04", "2025-07-24"

STATUS_RULES = (
    "TERMINATED_REGISTRATION: >=1 SEC-recorded Form 15-12B/15-12G (or 15F-12B/15F-12G) filing; "
    "termination_date = earliest such filing date (EVIDENCED). "
    "ACTIVE_FILER: no Form 15 and >=1 filing on/after S0_END minus 400 days (DERIVED). "
    "FILINGS_STALE: no Form 15 and last filing older than that bound (DERIVED; no delist claim). "
    "FETCH_FAILED: submissions record unavailable (fail-closed, never guessed)."
)


def load_ciks():
    ents = json.load(open(ENTITIES))
    return sorted(ents.keys())


def fetch():
    os.makedirs(RAW_DIR, exist_ok=True)
    ciks = load_ciks()
    pulled = skipped = failed = 0
    for cik in ciks:
        num = cik[3:]  # CIK0000001800 -> 0000001800
        path = f"{RAW_DIR}/{cik}.json"
        if os.path.exists(path) and os.path.getsize(path) > 100:
            skipped += 1
            continue
        url = f"https://data.sec.gov/submissions/CIK{num}.json"
        req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Encoding": "gzip, deflate"})
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = resp.read()
                if resp.headers.get("Content-Encoding") == "gzip":
                    import gzip
                    data = gzip.decompress(data)
            with open(path, "wb") as f:
                f.write(data)
            pulled += 1
        except Exception as e:  # noqa: BLE001 - recorded, never guessed
            with open(f"{RAW_DIR}/{cik}.FAILED", "w") as f:
                f.write(f"{type(e).__name__}: {e}\n")
            failed += 1
        time.sleep(0.25)
    print(json.dumps({"pulled": pulled, "skipped_existing": skipped, "failed": failed, "total": len(ciks)}))


def build():
    ciks = load_ciks()
    filers = {}
    for cik in ciks:
        path = f"{RAW_DIR}/{cik}.json"
        if not os.path.exists(path):
            filers[cik] = {"status": "FETCH_FAILED", "evidence": "no raw submissions file"}
            continue
        raw = open(path, "rb").read()
        try:
            d = json.loads(raw)
        except json.JSONDecodeError:
            filers[cik] = {"status": "FETCH_FAILED", "evidence": "unparseable submissions payload"}
            continue
        recent = d.get("filings", {}).get("recent", {})
        forms = recent.get("form", []) or []
        fdates = recent.get("filingDate", []) or []
        term_forms = {"15-12B", "15-12G", "15F-12B", "15F-12G"}
        term_dates = sorted(fd for fm, fd in zip(forms, fdates) if fm in term_forms)
        last_filing = max(fdates) if fdates else None
        in_window_10k = any(
            fm in ("10-K", "10-K/A") and S0_START <= fd <= S0_END
            for fm, fd in zip(forms, fdates)
        )
        stale_bound = (datetime.date.fromisoformat(S0_END) - datetime.timedelta(days=400)).isoformat()
        if term_dates:
            status = "TERMINATED_REGISTRATION"
        elif last_filing and last_filing >= stale_bound:
            status = "ACTIVE_FILER"
        else:
            status = "FILINGS_STALE"
        filers[cik] = {
            "status": status,
            "status_taxonomy": "EVIDENCED" if status == "TERMINATED_REGISTRATION" else "DERIVED",
            "name": d.get("name"),
            "sic": d.get("sicDescription"),
            "tickers_current": d.get("tickers") or [],
            "exchanges_current": d.get("exchanges") or [],
            "former_names": [
                {"name": fn.get("name"), "from": fn.get("from"), "to": fn.get("to")}
                for fn in (d.get("formerNames") or [])
            ],
            "termination_form_dates": term_dates,
            "last_filing_date": last_filing,
            "has_10k_in_S0_window": in_window_10k,
            "n_filings_recent": len(forms),
        }
    counts = {}
    for v in filers.values():
        counts[v["status"]] = counts.get(v["status"], 0) + 1
    census = {
        "schema": "stocks_free_v8_run/p0a_submissions_cohort_census@1",
        "built_at_utc": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "producer_role": "A1 (inlined light lane p0-a4-cohort)",
        "source": "https://data.sec.gov/submissions/CIK##########.json (SEC EDGAR; raw per-filer payloads staged gitignored with hash manifest)",
        "universe": "the frozen 410-filer multi-vintage panel entities (panel sha256 1cb115d3...)",
        "status_rules": STATUS_RULES,
        "s0_window": [S0_START, S0_END],
        "status_counts": counts,
        "filers": filers,
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(census, open(OUT, "w"), indent=1)
    # raw hash manifest (raw bytes stay gitignored; hashes are committed)
    man = {
        "schema": "stocks_free_v8_run/p0a_raw_hash_manifest@1",
        "built_at_utc": census["built_at_utc"],
        "files": {},
    }
    for fn in sorted(os.listdir(RAW_DIR)):
        p = os.path.join(RAW_DIR, fn)
        if os.path.isfile(p):
            man["files"][fn] = hashlib.sha256(open(p, "rb").read()).hexdigest()
    json.dump(man, open(RAW_MANIFEST, "w"), indent=1)
    print(json.dumps({"status_counts": counts, "census": OUT, "manifest_files": len(man["files"])}))


if __name__ == "__main__":
    {"fetch": fetch, "build": build}[sys.argv[1]]()
