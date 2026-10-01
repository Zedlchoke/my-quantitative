#!/usr/bin/env python
"""Bounded keyless acquisition of independent daily archives for the 7 blocked
PC12A assets. Session PC12A-7ASSET-DATA-UNBLOCK-2026-10-01 (UNREGISTERED
owner-instructed data lane; no eligibility/registry/GO write).

Sources (all measured reachable 2026-10-01 except where recorded BLOCKED):
  ECB   eurofxref-hist.zip        (official ECB daily reference rates, 16:00 CET)
  FRED  DEXUSNZ DEXSZUS DCOILBRENTEU DCOILWTICO DHHNGSP (fredgraph.csv, keyless)
  BoE   XUDLNZ XUDLSF             (official daily spot, keyless CSV)
  EIA   RBRTEd.xls                (official daily Brent spot FOB; raw archive
                                   only - venv has no xls parser; numbers come
                                   from FRED DCOILBRENTEU which is EIA-sourced)
  TwelveData XAG/USD 1day full    (owner entitlement TWELVE_DATA_API_KEY in
                                   .env, FOREX-NG6 p0_census_run.py pattern:
                                   key never echoed; paginated 5000; canary +
                                   double-pull identity check like NG6)

Pace: sleep between calls; <25 HTTP requests total; no heavy lock needed.
Every landed file is sha256-hashed into MANIFEST_RAW.json with its URL,
retrieved_at, http status, license note and authority status per CLAUDE.md 13.4
(free != authorized; TwelveData under owner entitlement = CANDIDATE evidence
channel, not a research authorization).
"""
from __future__ import annotations
import hashlib
import io
import json
import os
import sys
import time
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import requests

WT = Path("/Users/hoangminhlong/my-quantitative/.worktrees/pc12a-7asset-unblock-20261001")
CTL = WT / "research/control/PC12A-7ASSET-DATA-UNBLOCK-2026-10-01"
RAW = Path.home() / ".my-quantitative-data/pc12a-7asset-data-unblock-2026-10-01/raw"
RAW.mkdir(parents=True, exist_ok=True)
CTL.mkdir(parents=True, exist_ok=True)

UA = {"User-Agent": "Mozilla/5.0 (my-quantitative bounded research acquisition 2026-10-01)"}
S = requests.Session()
S.headers.update(UA)
manifest: list[dict] = []
now = lambda: datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def land(name: str, url: str, body: bytes, status: int, license_note: str,
         authority_status: str, note: str = "") -> dict:
    p = RAW / name
    if any(m["file"] == name for m in manifest):
        print(f"SKIP {name}: already landed this session")
        return next(m for m in manifest if m["file"] == name)
    if p.exists():
        # file landed by an earlier partial run of this same session script:
        # re-hash from disk rather than re-writing (bytes already archived)
        body = p.read_bytes()
        row = {
            "file": name, "path": str(p), "url": url,
            "retrieved_at_utc": datetime.fromtimestamp(
                p.stat().st_mtime, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "bytes": len(body), "sha256": sha256_bytes(body),
            "http_status": status, "license_note": license_note,
            "authority_status": authority_status,
            "note": (note + " | re-hashed from disk on session rerun").strip(" |"),
        }
        manifest.append(row)
        print(f"REHASHED {name}: {len(body)} B sha256={row['sha256'][:12]}...")
        return row
    p.write_bytes(body)
    row = {
        "file": name,
        "path": str(p),
        "url": url,
        "retrieved_at_utc": now(),
        "bytes": len(body),
        "sha256": sha256_bytes(body),
        "http_status": status,
        "license_note": license_note,
        "authority_status": authority_status,
        "note": note,
    }
    manifest.append(row)
    print(f"LANDED {name}: {len(body)} B http={status} sha256={row['sha256'][:12]}...")
    return row


class CurlResp:
    def __init__(self, status: int, content: bytes):
        self.status_code = status
        self.content = content

    def json(self):
        return json.loads(self.content)


def get(url: str, timeout: int = 60) -> requests.Response:
    # requests first; FRED is intermittently throttled for python-requests on
    # this host (3x ReadTimeout 2026-10-01) while curl succeeds - fall back to
    # curl without ever printing the url (keyed urls stay redacted in logs).
    try:
        return S.get(url, timeout=timeout)
    except Exception as e:
        print(f"  requests failed ({type(e).__name__}); curl fallback")
        import subprocess
        for attempt in range(3):
            cp = subprocess.run(
                ["curl", "-sS", "--http1.1", "-L", "--max-time", str(timeout),
                 "-A", UA["User-Agent"], "-w", "\n%{http_code}", url],
                capture_output=True)
            if cp.returncode == 0 and cp.stdout:
                body, _, code = cp.stdout.rpartition(b"\n")
                return CurlResp(int(code or 0), body)
            print(f"  curl retry {attempt + 1} rc={cp.returncode}")
            time.sleep(4)
        raise RuntimeError("GET failed after requests+curl retries")


# ---------------------------------------------------------------- 1. ECB ----
r = get("https://www.ecb.europa.eu/stats/eurofxref/eurofxref-hist.zip")
if r.status_code == 200:
    land("ecb_eurofxref_hist.zip", "https://www.ecb.europa.eu/stats/eurofxref/eurofxref-hist.zip",
         r.content, 200,
         "ECB reference rates: (c) European Central Bank, reproduction permitted with acknowledgment; free public download",
         "DOCUMENTED_CANDIDATE")
    zf = zipfile.ZipFile(io.BytesIO(r.content))
    inner = zf.namelist()
    csv_name = [n for n in inner if n.endswith(".csv")][0]
    csv_bytes = zf.read(csv_name)
    land("ecb_eurofxref_hist.csv", f"zip://{csv_name}",
         csv_bytes, 200,
         "extracted from the landed zip (sha above); same ECB license",
         "DOCUMENTED_CANDIDATE",
         note="extraction performed locally from the archived zip bytes")
else:
    print(f"ECB BLOCKED http={r.status_code}")
time.sleep(3)

# --------------------------------------------------------------- 2. FRED ----
FRED = {
    "DEXUSNZ": "H.10 noon buying rate, USD per 1 NZD == NZDUSD directly (verified from bytes 2026-09-25=0.5667 vs IBKR zone)",
    "DEXSZUS": "H.10 noon buying rate, CHF per 1 USD -> USDCHF = 1/x (kept as inverse consistency check)",
    "DEXUSSZ": "H.10 noon buying rate, USD per 1 CHF == USDCHF directly (added after DEXUSNZ direction lesson)",
    "DCOILBRENTEU": "Europe Brent spot FOB, USD/bbl, daily (EIA-sourced)",
    "DCOILWTICO": "Cushing WTI spot FOB, USD/bbl, daily (EIA-sourced)",
    "DHHNGSP": "Henry Hub natural gas spot, USD/MMBtu, daily (Thomson Reuters/Refinitiv-sourced)",
}


def get_curl(url: str, timeout: int = 60) -> CurlResp:
    # FRED throttles this host's python-requests TLS fingerprint (3x ReadTimeout
    # 2026-10-01) while curl succeeds 3/3 - measured, not guessed.
    import subprocess
    last = None
    for attempt in range(5):
        cp = subprocess.run(
            # FRED CDN filters non-default UAs (measured 2026-10-01: curl
            # default 200; custom/Mozilla UA -> rc=28 timeout) - no -A here.
            ["curl", "-sS", "--http1.1", "-L", "--max-time", str(timeout),
             "-w", "\n%{http_code}", url],
            capture_output=True)
        if cp.returncode == 0 and cp.stdout:
            body, _, code = cp.stdout.rpartition(b"\n")
            return CurlResp(int(code or 0), body)
        last = cp.returncode
        print(f"  curl retry {attempt + 1} rc={cp.returncode}")
        time.sleep(45)  # measured burst throttle: cool-down is ~2-4 min
    raise RuntimeError(f"curl GET failed rc={last}")


for sid, desc in FRED.items():
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={sid}"
    r = get_curl(url)
    if r.status_code == 200 and len(r.content) > 1000:
        land(f"fred_{sid}.csv", url, r.content, 200,
             "FRED terms: free, attribution requested; series metadata per " + desc,
             "DOCUMENTED_CANDIDATE", note=desc)
    else:
        print(f"FRED {sid} FAIL http={r.status_code} bytes={len(r.content)}")
    time.sleep(12)

# ---------------------------------------------------------------- 3. BoE ----
BOE = {
    "XUDLNZ": "BoE daily spot exchange rate series XUDLNZ (NZ dollar / US dollar) - direction verified post-parse",
    "XUDLSF": "BoE daily spot exchange rate series XUDLSF (Swiss franc / US dollar) - direction verified post-parse",
}
for code, desc in BOE.items():
    url = ("https://www.bankofengland.co.uk/boeapps/database/fromshowcolumns.asp"
           "?Travel=NIxAZxSUx&FromSeries=1&ToSeries=50&DAT=RNG&FD=1&FM=Jan&FY=2020"
           "&TD=31&TM=Dec&TY=2026&FNY=Y&CSVF=TT&html.x=66&html.y=26"
           f"&SeriesCodes={code}&UsingCodes=Y&Filter=N&title={code}&VPD=Y&VFD=N")
    r = get(url)
    if r.status_code == 200 and len(r.content) > 1000:
        land(f"boe_{code}.csv", url, r.content, 200,
             "Bank of England Database terms: free with attribution",
             "DOCUMENTED_CANDIDATE", note=desc)
    else:
        print(f"BoE {code} FAIL http={r.status_code} bytes={len(r.content)}")
    time.sleep(3)

# ---------------------------------------------------------------- 4. EIA ----
r = get("https://www.eia.gov/dnav/pet/hist_xls/RBRTEd.xls", timeout=90)
if r.status_code == 200 and len(r.content) > 10000:
    land("eia_RBRTEd_daily_brent.xls", "https://www.eia.gov/dnav/pet/hist_xls/RBRTEd.xls",
         r.content, 200,
         "U.S. EIA public data (U.S. Government work); free download",
         "DOCUMENTED_CANDIDATE",
         note="RAW ARCHIVE ONLY: venv lacks an xls parser; numeric use comes from FRED DCOILBRENTEU (EIA-sourced). RWTCLd/RNGWHHDd returned 404 this session - recorded in reachability log")
else:
    print(f"EIA RBRTEd FAIL http={r.status_code} bytes={len(r.content)}")
time.sleep(3)

# --------------------------------------------------------- 5. TwelveData ----
env_path = Path("/Users/hoangminhlong/my-quantitative/.env")
key = None
if env_path.exists():
    for line in env_path.read_text().splitlines():
        if line.startswith("TWELVE_DATA_API_KEY="):
            key = line.split("=", 1)[1].strip().strip('"').strip("'")
            break
if not key:
    print("TWELVE_DATA_API_KEY absent from .env -> TwelveData XAG acquisition NOT_RUN_NO_CREDENTIAL (no signup attempted: keyed signup is owner-only)")
else:
    base = "https://api.twelvedata.com/time_series"
    collected: list[dict] = []
    meta = None
    status = None
    for offset in range(0, 20000, 5000):
        url = (f"{base}?symbol=XAG/USD&interval=1day&outputsize=5000"
               f"&apikey={key}&order=ASC&format=JSON&start_date=1979-12-01")
        if offset:
            url = (f"{base}?symbol=XAG/USD&interval=1day&outputsize=5000"
                   f"&apikey={key}&order=ASC&format=JSON"
                   f"&start_date=1979-12-01&end_date={collected[-1]['datetime']}")
        resp = get(url)
        j = resp.json()
        status = resp.status_code
        if j.get("status") != "ok":
            print(f"TwelveData page FAIL: status={j.get('status')} code={j.get('code')} message={j.get('message')}")
            break
        meta = j.get("meta", meta)
        vals = [v for v in j.get("values", []) if v["datetime"] < (collected[-1]["datetime"] if offset else "9999")]
        if offset and len(vals) == len(j.get("values", [])):
            vals = j.get("values", [])[:-1]  # drop the overlapping boundary row
        collected.extend(vals)
        print(f"  TwelveData chunk n={len(j.get('values', []))} kept={len(vals)} total={len(collected)}")
        if len(j.get("values", [])) < 5000:
            break
        time.sleep(9)  # free-tier pace
    if collected:
        payload = {"meta": {**meta, "acquisition_note": "paginated 5000 asc, dedup keep-first, key never stored"},
                   "values": collected}
        land("twelvedata_XAGUSD_1day_full.json", "https://api.twelvedata.com/time_series?symbol=XAG/USD&interval=1day&outputsize=5000&apikey=[REDACTED]&order=ASC&format=JSON",
             (json.dumps(payload, separators=(",", ":"))).encode(),
             status,
             "TwelveData API under OWNER entitlement TWELVE_DATA_API_KEY (FOREX-NG6 precedent, plan PLAN_forex_ng6.md; key read from .env, never echoed); free-tier key, no purchase this session",
             "CANDIDATE_NOT_AUTHORIZED",
             note="channel provenance mirrors XAUUSD_1day_full.json sha 49c2684e... (NG6 staging); authority to use as CROSS_CHECK archive is an owner declaration away")
        # identity double-pull on most recent 30 bars (NG6 pattern)
        time.sleep(9)
        url = f"{base}?symbol=XAG/USD&interval=1day&outputsize=30&apikey={key}&format=JSON"
        resp = get(url)
        j = resp.json()
        recent = [v for v in j.get("values", [])]
        overlap = [v for v in collected[-60:] if any(r_["datetime"] == v["datetime"] for r_ in recent)]
        identical = all(
            all(str(r_[k]) == str(v[k]) for k in ("open", "high", "low", "close"))
            for v in overlap for r_ in recent if r_["datetime"] == v["datetime"])
        land("twelvedata_XAGUSD_doublepull30.json",
             "https://api.twelvedata.com/time_series?symbol=XAG/USD&interval=1day&outputsize=30&apikey=[REDACTED]&format=JSON",
             resp.content, resp.status_code,
             "same as above", "CANDIDATE_NOT_AUTHORIZED",
             note=f"order-normalized value identity check: {len(overlap)} shared dates, values identical={identical}")
        # never-existed canary (fabrication test)
        time.sleep(9)
        url = f"{base}?symbol=XAGUSDX/USD&interval=1day&outputsize=10&apikey={key}&format=JSON"
        resp = get(url)
        land("twelvedata_canary_never_existed.json",
             "https://api.twelvedata.com/time_series?symbol=XAGUSDX/USD&interval=1day&outputsize=10&apikey=[REDACTED]&format=JSON",
             resp.content, resp.status_code,
             "same as above", "CANDIDATE_NOT_AUTHORIZED",
             note="canary: symbol never existed; expect non-ok status / empty values, not fabricated rows")

out = CTL / "MANIFEST_RAW.json"
out.write_text(json.dumps({
    "schema": "pc12a_7asset_unblock_manifest@1",
    "session": "PC12A-7ASSET-DATA-UNBLOCK-2026-10-01",
    "generated_at_utc": now(),
    "worktree": str(WT),
    "branch": "orca/pc12a-7asset-unblock-20261001",
    "raw_dir": str(RAW),
    "files": manifest,
}, indent=1))
print(f"\nMANIFEST written: {out} ({len(manifest)} files)")
