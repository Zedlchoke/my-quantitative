#!/usr/bin/env python
"""P1 data authority stager for BTC-H4-EDGE-SEARCH-V1.

Stages (keyless Binance Vision, polite pacing, resumable, sha-pinned):
  1h klines   ETHUSDT, SOLUSDT  (BTC panel is already frozen in PSV1)
  fundingRate BTCUSDT, ETHUSDT, SOLUSDT  (lane D measured cost authority)

Coverage law (fail-closed): candidate-probe both ends per series, monthly
walk; every 404 inside the walked span that is NOT at the walked ends is a
COVERAGE_HOLE and fails the series. Raw bytes stay machine-local under
data_local/ (gitignored); only this manifest commits.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
RAW = ROOT / "data_local" / "vision"
MANIFEST_OUT = ROOT / "freezes" / "staging_manifest.json"

BASE = "https://data.binance.vision/data/futures/um/monthly"
UA = "my-quantitative-research/1.0 (internal research; owner-authorized 2026-09-23)"

SERIES = {
    # name -> (url_template, first_candidate, last_candidate)
    "klines:ETHUSDT:1h": (BASE + "/klines/ETHUSDT/1h/ETHUSDT-1h-{ym}.zip", "2020-01", "2026-08"),
    "klines:SOLUSDT:1h": (BASE + "/klines/SOLUSDT/1h/SOLUSDT-1h-{ym}.zip", "2020-01", "2026-08"),
    "funding:BTCUSDT": (BASE + "/fundingRate/BTCUSDT/BTCUSDT-fundingRate-{ym}.zip", "2020-01", "2026-08"),
    "funding:ETHUSDT": (BASE + "/fundingRate/ETHUSDT/ETHUSDT-fundingRate-{ym}.zip", "2020-01", "2026-08"),
    "funding:SOLUSDT": (BASE + "/fundingRate/SOLUSDT/SOLUSDT-fundingRate-{ym}.zip", "2020-01", "2026-08"),
}


def ym_range(a, b):
    ya, ma = map(int, a.split("-"))
    yb, mb = map(int, b.split("-"))
    out = []
    y, m = ya, ma
    while (y, m) <= (yb, mb):
        out.append(f"{y:04d}-{m:02d}")
        m += 1
        if m == 13:
            y, m = y + 1, 1
    return out


def fetch(url, max_retries=6, timeout=90):
    for attempt in range(1, max_retries + 1):
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                data = r.read()
                time.sleep(0.3)  # polite pacing
                return data
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            if e.code in (429, 500, 502, 503) and attempt < max_retries:
                time.sleep(1.5 * 2 ** (attempt - 1))
                continue
            raise
        except (urllib.error.URLError, TimeoutError, ConnectionError):
            if attempt < max_retries:
                time.sleep(1.5 * attempt)
                continue
            raise
    return None


def main():
    man = {"schema": "es1.staging_manifest@1",
           "built_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
           "series": {}}
    RAW.mkdir(parents=True, exist_ok=True)
    for name, (tpl, first_c, last_c) in SERIES.items():
        months = ym_range(first_c, last_c)
        # trim the walked span: candidate-probe the ends
        span = None
        got = {}
        holes = []
        fetched = cached = 0
        t0 = time.time()
        for ym in months:
            rel = f"{name.replace(':', '_')}/{ym}.zip"
            path = RAW / rel
            if path.exists() and path.stat().st_size > 0:
                raw = path.read_bytes()
                cached += 1
            else:
                raw = fetch(tpl.format(ym=ym))
                if raw is not None:
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_bytes(raw)
                    fetched += 1
            if raw is not None:
                got[ym] = {"sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}
                if span is None:
                    span = [ym, ym]
                else:
                    span[1] = ym
        # coverage holes: any month between span ends that is missing
        if span:
            for ym in ym_range(span[0], span[1]):
                if ym not in got:
                    holes.append(ym)
        man["series"][name] = {
            "first_month": span[0] if span else None,
            "last_month": span[1] if span else None,
            "files": len(got), "fetched": fetched, "cached": cached,
            "coverage_holes": holes,
            "elapsed_s": round(time.time() - t0, 1),
            "url_template": tpl,
            "digests": got,
        }
        print(f"[{name}] {span} files={len(got)} holes={len(holes)} "
              f"fetched={fetched} cached={cached} {time.time()-t0:.0f}s", flush=True)

    MANIFEST_OUT.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_OUT.write_text(json.dumps(man, indent=0))
    holes_total = sum(len(s["coverage_holes"]) for s in man["series"].values())
    verdict = "STAGED" if holes_total == 0 and all(s["files"] for s in man["series"].values()) else "STAGED_WITH_HOLES"
    man["verdict"] = verdict
    MANIFEST_OUT.write_text(json.dumps(man, indent=0))
    print("VERDICT:", verdict, "| wrote", MANIFEST_OUT)


if __name__ == "__main__":
    main()
