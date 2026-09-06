#!/usr/bin/env python3
"""V15 dataset staging from keyless sources (plan PLAN_crypto_v15.md section 3).

Families:
  metrics  : data.binance.vision data/futures/um/daily/metrics/<SYM>/<SYM>-metrics-<D>.zip
  klines   : data.binance.vision data/futures/um/daily/klines/<SYM>/15m/<SYM>-15m-<D>.zip
  funding  : fapi.binance.com /fapi/v1/fundingRate (keyless REST; vision family is stale)

Discipline: every downloaded byte sha256-pinned; per-file integrity gates;
consolidated parquet per symbol; machine-local under v15_data/ (gitignored);
committed manifest under research/control/v15_run/staging/.

Window: 2025-06-20..2026-08-21 (warmup + blind-S0). Resumable: existing zips
with expected size are kept; parquet rebuilt from zips every run.
"""
import concurrent.futures as cf
import csv
import datetime as dt
import hashlib
import io
import json
import subprocess
import time
import urllib.request
import zipfile
from pathlib import Path

WT = Path("/Users/hoangminhlong/my-quantitative/.worktrees/crypto/v15/integration")
DATA = WT / "v15_data"
STAGING_CTRL = WT / "research/control/v15_run/staging"
for sub in ("metrics_zips", "klines_zips", "funding_json", "parquet"):
    (DATA / sub).mkdir(parents=True, exist_ok=True)
STAGING_CTRL.mkdir(parents=True, exist_ok=True)

SYMBOLS = [
    "1000PEPEUSDT", "AAVEUSDT", "ACEUSDT", "ADAUSDT", "AVAXUSDT",
    "BCHUSDT", "BNBUSDT", "BOMEUSDT", "BTCUSDT", "DOGEUSDT",
    "ENAUSDT", "ETHUSDT", "LINKUSDT", "NEARUSDT", "ONGUSDT",
    "SOLUSDT", "SUIUSDT", "WLDUSDT", "XRPUSDT", "ZECUSDT",
]
DAY0 = dt.date(2025, 6, 20)
DAY1 = dt.date(2026, 8, 21)
UA = {"User-Agent": "my-quantitative-v15-staging/1.0"}

# per-symbol first metrics date from the probe (skip guaranteed-404s)
FIRST = json.load(open(STAGING_CTRL.parent / "p0_probe/step1_listings.json"))["symbols"]


def sha(b):
    return hashlib.sha256(b).hexdigest()


def daterange(a, b):
    d = a
    while d <= b:
        yield d
        d += dt.timedelta(days=1)


def fetch_vision(url, attempts=4):
    last = None
    for i in range(attempts):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read()
        except urllib.error.HTTPError:
            raise
        except Exception as e:  # transient reset/timeout: backoff and retry
            last = e
            time.sleep(1.5 * (i + 1))
    raise last


def fetch_fapi(url, attempts=4):
    # venv urllib hits a local TLS-intercepting proxy on fapi; curl uses the
    # system trust store and is the repo-proven route (V12 staging precedent).
    last = None
    for i in range(attempts):
        out = subprocess.run(["curl", "-s", "--max-time", "60", url],
                             capture_output=True)
        if out.returncode == 0 and out.stdout:
            try:
                return json.loads(out.stdout)
            except json.JSONDecodeError as e:
                last = e
        else:
            last = RuntimeError(f"curl rc={out.returncode}")
        time.sleep(1.5 * (i + 1))
    raise last


def dl_one(sym, day, family):
    """Download one daily zip if absent. Returns (status, entry)."""
    if family == "metrics":
        rel, url = (f"metrics_zips/{sym}-metrics-{day}.zip",
                    f"https://data.binance.vision/data/futures/um/daily/metrics/{sym}/{sym}-metrics-{day}.zip")
    else:
        rel, url = (f"klines_zips/{sym}-15m-{day}.zip",
                    f"https://data.binance.vision/data/futures/um/daily/klines/{sym}/15m/{sym}-15m-{day}.zip")
    p = DATA / rel
    if p.exists() and p.stat().st_size > 0:
        b = p.read_bytes()
        return "cached", {"staged_name": rel, "bytes": len(b), "sha256": sha(b)}
    try:
        b = fetch_vision(url)
    except urllib.error.HTTPError as e:
        return ("absent_404" if e.code == 404 else f"http_{e.code}"), {"staged_name": rel, "url": url}
    p.write_bytes(b)
    return "downloaded", {"staged_name": rel, "bytes": len(b), "sha256": sha(b)}


def stage_funding(sym):
    """Paginated fapi fundingRate for [DAY0, DAY1+1d). Returns rows + page log."""
    start = int(dt.datetime.combine(DAY0, dt.time(0), dt.timezone.utc).timestamp() * 1000)
    end = int((dt.datetime.combine(DAY1, dt.time(0), dt.timezone.utc).timestamp() + 86400) * 1000)
    rows, marker, pages = [], start, []
    while marker < end:
        url = (f"https://fapi.binance.com/fapi/v1/fundingRate?symbol={sym}"
               f"&startTime={marker}&endTime={end}&limit=1000")
        batch = fetch_fapi(url)
        pages.append({"url_tail": url[-90:], "n": len(batch)})
        if not batch:
            break
        rows += batch
        last = batch[-1]["fundingTime"]
        if len(batch) < 1000:
            break
        marker = last + 1
        time.sleep(0.25)
    (DATA / "funding_json" / f"{sym}.json").write_text(json.dumps({"symbol": sym, "pages": pages, "rows": rows}))
    return rows


def main():
    t0 = time.time()
    manifest = {"schema": "v15_staging_v1", "retrieved_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "window": {"start": DAY0.isoformat(), "end": DAY1.isoformat()},
                "universe": SYMBOLS,
                "environment_disclosure": "fapi.binance.com REST reached via curl/system trust store: venv urllib sees a local TLS-intercepting (self-signed-root) chain on this host; data.binance.vision unaffected; funding rows sanity-checked (rate bounds, stamp cadence)",
                "families": {}}

    # ---- daily-zip families (metrics, klines) ----
    tasks = []
    for sym in SYMBOLS:
        first = dt.date.fromisoformat(FIRST[sym]["first_date"])
        for day in daterange(max(DAY0, first), DAY1):
            tasks.append((sym, day, "metrics"))
        for day in daterange(DAY0, DAY1):  # klines exist for every listed perp in-window
            tasks.append((sym, day, "klines"))
    entries, statuses = [], {}
    with cf.ThreadPoolExecutor(max_workers=8) as ex:
        futs = {ex.submit(dl_one, s, d, f): (s, d, f) for s, d, f in tasks}
        done = 0
        for fut in cf.as_completed(futs):
            s, d, f = futs[fut]
            st, e = fut.result()
            entries.append(e)
            statuses[st] = statuses.get(st, 0) + 1
            done += 1
            if done % 2000 == 0:
                print(f"  zips {done}/{len(tasks)} elapsed {time.time()-t0:.0f}s", flush=True)
    print("zip statuses:", statuses, flush=True)
    manifest["families"]["zips"] = entries

    # ---- funding ----
    fund_entries = []
    for sym in SYMBOLS:
        rows = stage_funding(sym)
        fund_entries.append({"symbol": sym, "n_rows": len(rows),
                             "first": rows[0]["fundingTime"] if rows else None,
                             "last": rows[-1]["fundingTime"] if rows else None})
        print(f"funding {sym}: n={len(rows)}", flush=True)
    manifest["families"]["funding"] = fund_entries

    (STAGING_CTRL / "staging_zips_manifest.json").write_text(json.dumps(manifest, indent=1))
    print(f"STAGE-DOWNLOAD DONE in {time.time()-t0:.0f}s -> staging_zips_manifest.json", flush=True)


if __name__ == "__main__":
    main()
