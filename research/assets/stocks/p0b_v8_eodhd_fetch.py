"""V8 P0a leg 3: EODHD single-name daily price pull for the 410-filer panel.

Price authority: EODHD "EOD Historical Data - All World" (owner-purchased
2026-09-05; six-gate probe ALL PASS - root research/control/
stocks_free_v8_probe/eodhd_probe_verdict.json). Key lives in the
environment only (.env EODHD_API_KEY loaded into os.environ; never
printed, logged, or written to any artifact).

Fetch is resumable and per-symbol deterministic (probe G6 double-pull
evidence). Every failure record is REDACTED: the api_token never appears
in any written byte. Raw payloads stay gitignored; a committed sha256
manifest pins the bytes.

Usage:
  python -m research.assets.stocks.p0b_v8_eodhd_fetch fetch
  python -m research.assets.stocks.p0b_v8_eodhd_fetch manifest
"""

import hashlib
import json
import os
import re
import sys
import time
import urllib.request
import datetime

RAW_DIR = ".staging_prices_v8/eod"
CENSUS = "research/control/stocks_free_v8_run/p0a_submissions_cohort_census.json"
MANIFEST = "research/control/stocks_free_v8_run/p0a_eodhd_price_manifest.json"
REPO_ROOT = os.environ.get("V8_REPO_ROOT", "/Users/hoangminhlong/my-quantitative")
REDACT = re.compile(r"api_token=[^&\s\"]+")


def load_key():
    key = os.environ.get("EODHD_API_KEY")
    if key:
        return key
    env_path = os.path.join(REPO_ROOT, ".env")
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line.startswith("EODHD_API_KEY="):
                key = line.split("=", 1)[1].strip().strip('"').strip("'")
                break
    if not key:
        raise SystemExit("EODHD_API_KEY not found in environment or .env - fail closed")
    os.environ["EODHD_API_KEY"] = key  # environment only
    return key


def redact(text):
    return REDACT.sub("api_token=REDACTED", text)


def tickers_from_census():
    d = json.load(open(CENSUS))
    out = {}
    for cik, v in d["filers"].items():
        tks = v.get("tickers_current") or []
        out[cik] = {"tickers": tks, "status": v.get("status")}
    return out


def fetch():
    key = load_key()
    os.makedirs(RAW_DIR, exist_ok=True)
    universe = tickers_from_census()
    pulled = skipped = no_ticker = failed = 0
    failures = {}
    for cik, info in sorted(universe.items()):
        tks = info["tickers"]
        if not tks:
            no_ticker += 1
            continue
        ticker = tks[0]  # primary listing ticker per SEC submissions
        sym = f"{ticker}.US"
        path = f"{RAW_DIR}/{cik}__{ticker}.json"
        if os.path.exists(path) and os.path.getsize(path) > 100:
            skipped += 1
            continue
        url = (
            f"https://eodhd.com/api/eod/{sym}?api_token={key}"
            "&fmt=json&order=a&period=d"
        )
        req = urllib.request.Request(url, headers={"User-Agent": "my-quantitative-research/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = resp.read()
            if data[:1] == b"{" and b"errorMessage" in data[:200]:
                raise RuntimeError(redact(data[:300].decode("utf-8", "replace")))
            with open(path, "wb") as f:
                f.write(data)
            pulled += 1
        except Exception as e:  # noqa: BLE001 - recorded redacted, never retried blind
            failures[cik] = {"ticker": ticker, "error": redact(str(e))[:200]}
            failed += 1
        time.sleep(0.15)
    print(json.dumps({
        "pulled": pulled, "skipped_existing": skipped,
        "no_ticker_in_census": no_ticker, "failed": failed,
        "universe": len(universe),
    }))


def manifest():
    man = {
        "schema": "stocks_free_v8_run/p0a_eodhd_price_manifest@1",
        "built_at_utc": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "authority": "EODHD All World; probe ALL PASS (root eodhd_probe_verdict.json)",
        "note": "raw payloads gitignored under .staging_prices_v8/eod; only hashes are committed",
        "files": {},
    }
    for fn in sorted(os.listdir(RAW_DIR)):
        p = os.path.join(RAW_DIR, fn)
        if os.path.isfile(p):
            man["files"][fn] = hashlib.sha256(open(p, "rb").read()).hexdigest()
    json.dump(man, open(MANIFEST, "w"), indent=1)
    print(json.dumps({"files_hashed": len(man["files"]), "manifest": MANIFEST}))


if __name__ == "__main__":
    {"fetch": fetch, "manifest": manifest}[sys.argv[1]]()
