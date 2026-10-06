#!/usr/bin/env python
"""NOAA collector (NONPRICE-DATA-ACQUISITION) - CPC issued forecasts + observed.

Sources (access 2026-10-02):
- CPC issued 6-10/8-14-day TEMP forecast zips (shapefile sets, ~daily issuance
  since 2012-09-11): https://ftp.cpc.ncep.noaa.gov/GIS/us_tempprcpfcst/
  {610|814}temp_{YYYYMMDD}.zip  <- ISSUED forecasts; issued_at = file date
  (forecast issue date). ISSUED != OBSERVED != REFORECAST (separate tables).
- Observed monthly CONUS climate-division temps (key-free bulk single files):
  https://www.ncei.noaa.gov/pub/data/cirs/climdiv/climdiv-tavg-v1.0.0-{YYYYMMDD}
  (+ tmin/tmax + division->state mapping). OBSERVED data - never an entry
  feature; HDD/CDD weights are PRE-DECLARED (see normalize/hdd_cdd_weights.py).
- NDFD forecast-vintage pilot (bounded): AWS Open Data noaa-ndfd-pds bucket
  (public HTTPS listing, from 2020-04-16 per registry.opendata.aws/noaa-ndfd,
  re-verify at collection), CONUS 2m temp, 00Z cycle, last 30 days only.

Disk law: NOAA family subcap 1.1 GiB. Plan:
  - 610temp FULL daily 2012-09-11..2025-06-30 (small-file regime ~115KB)
  - 610temp weekly sample (every 7th day) 2025-07-01..now (3.3MB big-file
    regime) -> daily continuity there typed WAIT_STORAGE
  - 814temp 30-day pilot (2026-09-01..now) -> full history typed WAIT_STORAGE
  - climdiv tavg/tmin/tmax + mapping
  - NDFD pilot last 30 days 00Z (sub-bounded)
"""
from __future__ import annotations
import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import common

FAMILY = "noaa"
FTP = "https://ftp.cpc.ncep.noaa.gov/GIS/us_tempprcpfcst/"
CLIMDIV = "https://www.ncei.noaa.gov/pub/data/cirs/climdiv/"
NDFD_BUCKET = "https://noaa-ndfd-pds.s3.amazonaws.com"


def ftp_listing() -> list[str]:
    rel = "noaa/cpc/ftp_dir_listing.html"
    rec = common.http_get(FTP, family=FAMILY, rel_path=rel, rate_limit_s=1.0,
                          max_bytes=12 * 1024**2)
    if rec.get("status") != "ok":
        return []
    text = (common.RAW_ROOT / rel).read_text(errors="replace")
    return sorted(set(re.findall(r'href="([^"]+\.zip)"', text)))


def daterange(d1: dt.date, d2: dt.date):
    d = d1
    while d <= d2:
        yield d
        d += dt.timedelta(days=1)


def fetch_610_full():
    """2012-09-11 .. 2025-06-30 daily (files that exist on the FTP)."""
    listing = set(ftp_listing())
    have = {f for f in listing if f.startswith("610temp")}
    recs = []
    d1, d2 = dt.date(2012, 9, 11), dt.date(2025, 6, 30)
    targets = [f"610temp_{d.isoformat().replace('-', '')}.zip" for d in daterange(d1, d2)]
    targets = [t for t in targets if t in have]
    print(f"610temp full-window targets present on FTP: {len(targets)}")
    for i, t in enumerate(targets):
        recs.append(common.http_get(FTP + t, family=FAMILY,
                                    rel_path=f"noaa/cpc/610temp/{t}",
                                    rate_limit_s=0.25, retries=3, timeout=90,
                                    max_bytes=1 * 1024**2))
        if (i + 1) % 400 == 0:
            print(f"  610temp {i+1}/{len(targets)} ({common.summary()['total_bytes']/1e6:.0f}MB total)")
    return recs


def fetch_610_recent_weekly():
    listing = set(ftp_listing())
    have = {f for f in listing if f.startswith("610temp")}
    recs = []
    d1, d2 = dt.date(2025, 7, 1), dt.date(2026, 10, 1)
    targets = [f"610temp_{d.isoformat().replace('-', '')}.zip"
               for d in daterange(d1, d2) if d.weekday() == 0]  # weekly Mondays
    targets = [t for t in targets if t in have]
    print(f"610temp weekly-sample targets (big-file regime): {len(targets)}")
    for i, t in enumerate(targets):
        recs.append(common.http_get(FTP + t, family=FAMILY,
                                    rel_path=f"noaa/cpc/610temp_recent_weekly/{t}",
                                    rate_limit_s=0.25, retries=3, timeout=120,
                                    max_bytes=8 * 1024**2))
    return recs


def fetch_814_pilot():
    listing = set(ftp_listing())
    have = {f for f in listing if f.startswith("814temp")}
    recs = []
    d1, d2 = dt.date(2026, 9, 1), dt.date(2026, 10, 1)
    targets = [f"814temp_{d.isoformat().replace('-', '')}.zip" for d in daterange(d1, d2)]
    targets = [t for t in targets if t in have]
    print(f"814temp pilot targets: {len(targets)}")
    for t in targets:
        recs.append(common.http_get(FTP + t, family=FAMILY,
                                    rel_path=f"noaa/cpc/814temp_pilot/{t}",
                                    rate_limit_s=0.4, retries=3, timeout=120,
                                    max_bytes=8 * 1024**2))
    return recs


def fetch_climdiv() -> list[dict]:
    recs = []
    for code, name in [("climdiv-tavg-v1.0.0-", "tavg"), ("climdiv-tmax-v1.0.0-", "tmax"),
                       ("climdiv-tmin-v1.0.0-", "tmin")]:
        # directory listing first to get the current file date suffix
        lst = common.http_get(CLIMDIV, family=FAMILY, rel_path=f"noaa/ncei/climdiv_dir_{name}.html",
                              rate_limit_s=0.8, max_bytes=4 * 1024**2)
        fname = None
        if lst.get("status") == "ok":
            text = (common.RAW_ROOT / f"noaa/ncei/climdiv_dir_{name}.html").read_text(errors="replace")
            m = re.search(code + r"(\d{8})", text)
            if m:
                fname = code + m.group(1)
        if fname:
            recs.append(common.http_get(CLIMDIV + fname, family=FAMILY,
                                        rel_path=f"noaa/ncei/{fname}",
                                        rate_limit_s=0.8, max_bytes=8 * 1024**2))
    # division -> state code mapping (official readme)
    recs.append(common.http_get("https://www.ncei.noaa.gov/pub/data/cirs/climdiv/divisional-readme.txt",
                                family=FAMILY, rel_path="noaa/ncei/divisional-readme.txt",
                                rate_limit_s=0.8, max_bytes=1 * 1024**2, retries=2))
    return recs


def fetch_ndfd_pilot(days: int = 30) -> list[dict]:
    """NDFD CURRENT-snapshot only (AWS Open Data noaa-ndfd-pds).

    MEASURED 2026-10-02: the public bucket keys (opnl/AR.conus/VP.{period}/
    ds.temp.bin) carry NO issue-date and the bucket is NOT S3-versioned
    (ListObjectVersions returns a single current version) -> historical NDFD
    forecast vintages are NOT retrievable from this free route; the official
    archive is NCEI AIRS (request-based, not bulk). Multi-year GFS/NDFD
    forecast vintages are therefore typed MISSING/NOT_RUN_PIT; CPC issued
    6-10/8-14 archives (2012-09+) are the PIT-legal forecast series we hold.
    We store one current snapshot as evidence of format/structure.
    """
    recs = []
    for vp in ["VP.001-003", "VP.004-007"]:
        recs.append(common.http_get(
            f"{NDFD_BUCKET}/opnl/AR.conus/{vp}/ds.temp.bin", family=FAMILY,
            rel_path=f"noaa/ndfd_current/AR.conus_{vp}_ds.temp.bin",
            rate_limit_s=0.5, retries=2, timeout=300,
            max_bytes=80 * 1024**2))
    return recs


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--only", choices=["610full", "610recent", "814pilot", "climdiv", "ndfd"])
    args = ap.parse_args()

    results = []
    if args.smoke:
        listing = ftp_listing()
        t610 = [f for f in listing if f.startswith("610temp")]
        print(json.dumps({"ftp_zips_total": len(listing), "610temp_files": len(t610),
                          "first": t610[:1], "last": t610[-1:]}))
        if t610:
            mid = t610[len(t610) // 2]
            results.append(common.http_get(FTP + mid, family=FAMILY,
                                           rel_path=f"noaa/cpc/610temp_smoke/{mid}",
                                           rate_limit_s=0.5, max_bytes=1 * 1024**2))
        results += fetch_climdiv()
    else:
        jobs = {"610full": fetch_610_full, "610recent": fetch_610_recent_weekly,
                "814pilot": fetch_814_pilot, "climdiv": fetch_climdiv,
                "ndfd": fetch_ndfd_pilot}
        if args.only:
            results += jobs[args.only]()
        else:
            for name in ["610full", "climdiv", "814pilot", "610recent", "ndfd"]:
                print(f"== {name}")
                results += jobs[name]()

    ok = [r for r in results if r.get("status") == "ok"]
    er = [r for r in results if r.get("status") == "http_error"]
    ws = [r for r in results if r.get("status") == "wait_storage"]
    print(json.dumps({"ok": len(ok), "http_error": len(er), "wait_storage": len(ws),
                      "bytes": sum(int(r.get("bytes", 0)) for r in ok),
                      "summary": common.summary()}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
