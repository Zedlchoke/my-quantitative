#!/usr/bin/env python
"""EIA collector (NONPRICE-DATA-ACQUISITION) - key-free www.eia.gov routes.

Primary evidence (access 2026-10-02):
- WNGSR weekly archive (as-published issues, 1996..2026, 1506 entries):
    index: https://www.eia.gov/naturalgas/weekly/includes/archive.php
    issue: https://www.eia.gov/naturalgas/weekly/archivenew_ngwu/{YYYY}/{MM_DD}/
- WPSR weekly archive (as-published issues, 2011..2026, 792 entries):
    index: https://www.eia.gov/petroleum/supply/weekly/archive/
    issue: .../archive/{YYYY}/{YYYY_MM_DD}/wpsr_{YYYY_MM_DD}.php (2011: .html)
- WNGSR schedule (holiday moves): https://ir.eia.gov/ngs/schedule.html
- dnav revised-latest weekly series (cross-check only, NOT PIT):
    https://www.eia.gov/dnav/pet/hist_xls/{CODE}.xls  e.g. WCRSTUS1w
- BLOCKED: ir.eia.gov host returns HTTP 403 for ngshistory.xlsx / wpsr tables
  (recorded blocker; the www.eia.gov archives above are the lawful fallback
  and are strictly better: as-published vintages).

Usage:
  python eia.py --smoke
  python eia.py                 # archives + schedule + dnav cross-check series
  python eia.py --wpsr-only | --wngsr-only
"""
from __future__ import annotations
import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import common

FAMILY = "eia"
BASE = "https://www.eia.gov"

DNAV_SERIES = {
    "WCRSTUS1w": "US crude oil stocks, weekly (revised-latest cross-check)",
    "WDISTUS1w": "US distillate stocks, weekly (revised-latest cross-check)",
}


def fetch_ng_archive_index() -> str | None:
    url = f"{BASE}/naturalgas/weekly/includes/archive.php"
    rel = "eia/wngsr/archive_index.html"
    rec = common.http_get(url, family=FAMILY, rel_path=rel, rate_limit_s=0.8,
                          max_bytes=8 * 1024**2)
    if rec.get("status") != "ok":
        return None
    text = (common.RAW_ROOT / rel).read_text(errors="replace")
    return text


def ng_issue_urls(html: str) -> list[str]:
    urls = re.findall(r'href="(/naturalgas/weekly/archivenew_ngwu/[^"]+)"', html)
    # keep issue roots and html pages; dedupe to the issue directory level
    out = []
    seen = set()
    for u in urls:
        m = re.match(r"(/naturalgas/weekly/archivenew_ngwu/(\d{4})/(\d{2})_(\d{2}))", u)
        if not m:
            continue
        root = m.group(1)
        if root in seen:
            continue
        seen.add(root)
        out.append(root)
    return out


def fetch_ng_issue(root: str) -> dict:
    # archive entries point at the issue page (some list a specific file)
    candidates = [f"{BASE}{root}", f"{BASE}{root}/ngwu_archive.php"]
    for url in candidates:
        name = url.rstrip("/").split("/")[-1]
        rel = f"eia/wngsr/issues/{root.split('archivenew_ngwu/')[1].replace('/', '_')}.html"
        rec = common.http_get(url, family=FAMILY, rel_path=rel, rate_limit_s=0.5,
                              max_bytes=4 * 1024**2)
        if rec.get("status") == "ok":
            return rec
    return rec


def fetch_wpsr_index() -> str | None:
    url = f"{BASE}/petroleum/supply/weekly/archive/"
    rel = "eia/wpsr/archive_index.html"
    rec = common.http_get(url, family=FAMILY, rel_path=rel, rate_limit_s=0.8,
                          max_bytes=8 * 1024**2)
    if rec.get("status") != "ok":
        return None
    return (common.RAW_ROOT / rel).read_text(errors="replace")


def wpsr_issue_urls(html: str) -> list[str]:
    urls = re.findall(r'href="(/petroleum/supply/weekly/archive/[^"]+)"', html)
    out, seen = [], set()
    for u in urls:
        m = re.match(r"(/petroleum/supply/weekly/archive/(\d{4})/\d{4}_\d{2}_\d{2}/wpsr_\d{4}_\d{2}_\d{2})\.(?:php|html)", u)
        if m and m.group(1) not in seen:
            seen.add(m.group(1))
            out.append(m.group(1))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--wpsr-only", action="store_true")
    ap.add_argument("--wngsr-only", action="store_true")
    args = ap.parse_args()

    results = []

    def show(label, recs):
        ok = [r for r in recs if r.get("status") == "ok"]
        er = [r for r in recs if r.get("status") == "http_error"]
        ws = [r for r in recs if r.get("status") == "wait_storage"]
        print(json.dumps({label: {"ok": len(ok), "http_error": len(er),
                                  "wait_storage": len(ws),
                                  "bytes": sum(int(r.get("bytes", 0)) for r in ok)}}, indent=1))

    # schedule + reference pages (ir.eia.gov may 403 - recorded, not bypassed)
    if not args.wpsr_only:
        results.append(common.http_get("https://ir.eia.gov/ngs/schedule.html", family=FAMILY,
                                       rel_path="eia/wngsr/schedule.html", rate_limit_s=0.8,
                                       max_bytes=2 * 1024**2))
        results.append(common.http_get(f"{BASE}/naturalgas/weekly/", family=FAMILY,
                                       rel_path="eia/wngsr/current_week.html", rate_limit_s=0.8,
                                       max_bytes=2 * 1024**2))

    if not args.smoke:
        if not args.wpsr_only:
            html = fetch_ng_archive_index()
            if html:
                roots = ng_issue_urls(html)
                print(f"WNGSR issues found: {len(roots)}")
                recs = []
                for i, root in enumerate(roots):
                    recs.append(fetch_ng_issue(root))
                    if i % 200 == 0:
                        print(f"  wngsr {i+1}/{len(roots)}")
                show("wngsr_issues", recs)
                results += recs
        if not args.wngsr_only:
            html = fetch_wpsr_index()
            if html:
                pages = wpsr_issue_urls(html)
                print(f"WPSR issues found: {len(pages)}")
                recs = []
                for i, page in enumerate(pages):
                    rel = f"eia/wpsr/issues/{page.split('/')[-1]}.html"
                    recs.append(common.http_get(f"{BASE}{page}", family=FAMILY,
                                                rel_path=rel, rate_limit_s=0.5,
                                                max_bytes=6 * 1024**2))
                    if i % 200 == 0:
                        print(f"  wpsr {i+1}/{len(pages)}")
                show("wpsr_issues", recs)
                results += recs
            # errata sheet (vintage-relevant corrections)
            results.append(common.http_get(f"{BASE}/petroleum/supply/weekly/WPSR_ErrataSheet.xlsx",
                                           family=FAMILY, rel_path="eia/wpsr/WPSR_ErrataSheet.xlsx",
                                           rate_limit_s=0.8, max_bytes=8 * 1024**2))
            # dnav revised-latest weekly cross-check series
            for code, desc in DNAV_SERIES.items():
                results.append(common.http_get(f"{BASE}/dnav/pet/hist_xls/{code}.xls",
                                               family=FAMILY, rel_path=f"eia/dnav_latest/{code}.xls",
                                               rate_limit_s=0.8, max_bytes=4 * 1024**2))

    ok = [r for r in results if r.get("status") == "ok"]
    print(json.dumps({"total_ok": len(ok),
                      "total_bytes": sum(int(r.get("bytes", 0)) for r in ok),
                      "summary": common.summary()}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
