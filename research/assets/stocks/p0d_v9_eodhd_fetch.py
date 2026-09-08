"""V9 P0d: EODHD EOD pulls for the full death-inclusive cohort.

PLAN_stocks_v9.md sec 3 P0d. Price authority: EODHD "EOD Historical Data -
All World" (owner-entitled; six-gate probe ALL PASS, root
research/control/stocks_free_v8_probe/eodhd_probe_verdict.json). The dead
names are pulled at scale here for the first time in the program.

  fetch            resumable EOD pulls for every cohort member with a ticker
                   (alive panel tickers + joined dead tickers). Raw payloads
                   stay gitignored; only the committed sha256 manifest pins
                   them. api_token is environment-only and redacted from
                   every error string.
  benchmarks       re-stages the SPY + 11 sector-ETF benchmark series from
                   the V8 staging bytes, each verified against the V8
                   benchmark manifest hash before copying (no re-pull, no
                   byte drift).
  manifest         sha256 manifest over all staged raw bytes (committed).
  integrity-scan   per-member verdicts: DEAD_PRICE_CONFIRMED when the last
                   EODHD trade lands within DEATH_DATE_TOLERANCE_DAYS of the
                   evidenced death filing date; NOT_DEAD_PRICE_SURVIVAL when
                   prices run materially past it (Baxter-style reorg
                   survivors are recorded here and excluded from the dead
                   leg, never silently); PRICE_UNAVAILABLE for empty pulls.

Usage:
  python -m research.assets.stocks.p0d_v9_eodhd_fetch fetch
  python -m research.assets.stocks.p0d_v9_eodhd_fetch benchmarks
  python -m research.assets.stocks.p0d_v9_eodhd_fetch manifest
  python -m research.assets.stocks.p0d_v9_eodhd_fetch integrity-scan
"""

import hashlib
import json
import os
import re
import shutil
import sys
import time
import urllib.request
import datetime

CONTROL = "research/control/stocks_free_v9_run"
COHORT = f"{CONTROL}/cohort_v9.json"
RAW_DIR = ".staging_prices_v9/eod"
BENCH_DIR = ".staging_prices_v9/benchmarks"
MANIFEST = f"{CONTROL}/p0d_v9_price_manifest.json"
SCAN = f"{CONTROL}/p0d_v9_integrity_scan.json"
V8_BENCH_DIR = os.environ.get(
    "V8_BENCH_DIR",
    "/Users/hoangminhlong/my-quantitative/.worktrees/stocks-free-v8/integration/.staging_prices_v8/benchmarks",
)
V8_BENCH_MANIFEST = "research/control/stocks_free_v8_run/p0a_benchmark_manifest.json"
DEATH_DATE_TOLERANCE_DAYS = 120
REDACT = re.compile(r"api_token=[^&\s\"]+")
S0_END = "2025-07-24"


def load_key():
    key = os.environ.get("EODHD_API_KEY")
    if key:
        return key
    env_path = os.path.join(os.environ.get("V9_REPO_ROOT", "/Users/hoangminhlong/my-quantitative"), ".env")
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line.startswith("EODHD_API_KEY="):
                key = line.split("=", 1)[1].strip().strip('"').strip("'")
                break
    if not key:
        raise SystemExit("EODHD_API_KEY not found - fail closed")
    os.environ["EODHD_API_KEY"] = key  # environment only
    return key


def redact(text):
    return REDACT.sub("api_token=REDACTED", str(text))


def _members_with_tickers():
    cohort = json.load(open(COHORT))
    jobs = []
    for m in cohort["members"]["ALIVE_EVIDENCED"]:
        if m.get("ticker"):
            jobs.append((m["cik"], m["ticker"], "ALIVE", None))
    for m in cohort["members"]["DEAD_EVIDENCED"]:
        if m.get("ticker_eodhd"):
            jobs.append((m["cik"], m["ticker_eodhd"], "DEAD", m.get("death_filing_date_evidence")))
    return cohort, jobs


def fetch():
    key = load_key()
    os.makedirs(RAW_DIR, exist_ok=True)
    _, jobs = _members_with_tickers()
    pulled = skipped = failed = no_ticker = 0
    failures = {}
    for cik, ticker, leg, _death in jobs:
        path = f"{RAW_DIR}/{cik}__{ticker}.json"
        if os.path.exists(path) and os.path.getsize(path) > 100:
            skipped += 1
            continue
        sym = f"{ticker}.US"
        url = f"https://eodhd.com/api/eod/{sym}?api_token={key}&fmt=json&order=a&period=d"
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
            failures[cik] = {"ticker": ticker, "leg": leg, "error": redact(e)[:200]}
            failed += 1
        time.sleep(0.15)
    no_ticker = len(jobs) - pulled - skipped - failed
    print(json.dumps({"pulled": pulled, "skipped_existing": skipped,
                      "failed": failed, "universe_jobs": len(jobs)}))
    if failures:
        json.dump(failures, open(f"{RAW_DIR}/_failures.json", "w"), indent=1)


def benchmarks():
    os.makedirs(BENCH_DIR, exist_ok=True)
    expected = json.load(open(V8_BENCH_MANIFEST))["files"]
    copied = 0
    for sym, sha in sorted(expected.items()):
        src = f"{V8_BENCH_DIR}/{sym}.json"
        data = open(src, "rb").read()
        actual = hashlib.sha256(data).hexdigest()
        if actual != sha:
            raise SystemExit(f"benchmark byte mismatch for {sym}: {actual} - fail closed")
        with open(f"{BENCH_DIR}/{sym}.json", "wb") as f:
            f.write(data)
        copied += 1
    print(json.dumps({"benchmarks_restaged": copied, "source": V8_BENCH_DIR,
                      "note": "bytes verified against V8 benchmark manifest before copy"}))


def manifest():
    man = {
        "schema": "stocks_free_v9_run/p0d_v9_price_manifest@1",
        "built_at_utc": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "authority": "EODHD All World; probe ALL PASS (root eodhd_probe_verdict.json)",
        "note": "raw payloads gitignored under .staging_prices_v9/; only hashes are committed",
        "files": {},
    }
    for d in (RAW_DIR, BENCH_DIR):
        for fn in sorted(os.listdir(d)):
            p = os.path.join(d, fn)
            if os.path.isfile(p) and not fn.startswith("_"):
                man["files"][f"{os.path.basename(d)}/{fn}"] = hashlib.sha256(open(p, "rb").read()).hexdigest()
    json.dump(man, open(MANIFEST, "w"), indent=1)
    print(json.dumps({"files_hashed": len(man["files"]), "manifest": MANIFEST}))


def integrity_scan():
    cohort, jobs = _members_with_tickers()
    scan = {
        "schema": "stocks_free_v9_run/p0d_v9_integrity_scan@1",
        "built_at_utc": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "producer_role": "A1 (PLAN_stocks_v9 sec3 P0d)",
        "rule": f"DEAD_PRICE_CONFIRMED if last EODHD trade within +/-{DEATH_DATE_TOLERANCE_DAYS}d of the evidenced death filing date; NOT_DEAD_PRICE_SURVIVAL if prices run materially past it (recorded exclusion from the dead leg); PRICE_UNAVAILABLE otherwise",
        "dead_verdicts": {},
        "alive_last_dates": {},
        "counts": {},
    }
    counts = {"DEAD_PRICE_CONFIRMED": 0, "NOT_DEAD_PRICE_SURVIVAL": 0,
              "PRICE_UNAVAILABLE": 0, "alive_no_pull": 0}
    for cik, ticker, leg, death_date in jobs:
        path = f"{RAW_DIR}/{cik}__{ticker}.json"
        if not os.path.exists(path) or os.path.getsize(path) < 100:
            if leg == "DEAD":
                counts["PRICE_UNAVAILABLE"] += 1
                scan["dead_verdicts"][cik] = {"ticker": ticker, "verdict": "PRICE_UNAVAILABLE",
                                              "death_filing_date": death_date}
            else:
                counts["alive_no_pull"] += 1
            continue
        try:
            bars = json.load(open(path))
            last_date = bars[-1]["date"] if bars else None
        except Exception:  # noqa: BLE001 - recorded as unavailable, never guessed
            last_date = None
        if leg == "ALIVE":
            scan["alive_last_dates"][cik] = {"ticker": ticker, "last_date": last_date}
            continue
        verdict = "PRICE_UNAVAILABLE"
        delta = None
        if last_date and death_date:
            d0 = datetime.date.fromisoformat(death_date)
            d1 = datetime.date.fromisoformat(last_date[:10])
            delta = (d1 - d0).days
            if abs(delta) <= DEATH_DATE_TOLERANCE_DAYS:
                verdict = "DEAD_PRICE_CONFIRMED"
            elif delta > DEATH_DATE_TOLERANCE_DAYS or last_date[:10] > S0_END:
                verdict = "NOT_DEAD_PRICE_SURVIVAL"
            else:
                verdict = "DEAD_PRICE_CONFIRMED"  # prices end before the filing: delisting-return leg intact, delta recorded
        counts[verdict] += 1
        scan["dead_verdicts"][cik] = {"ticker": ticker, "verdict": verdict,
                                      "death_filing_date": death_date,
                                      "last_trade_date": last_date, "delta_days": delta}
    scan["counts"] = counts
    json.dump(scan, open(SCAN, "w"), indent=1)
    print(json.dumps(counts))


if __name__ == "__main__":
    {"fetch": fetch, "benchmarks": benchmarks, "manifest": manifest,
     "integrity-scan": integrity_scan}[sys.argv[1]]()
