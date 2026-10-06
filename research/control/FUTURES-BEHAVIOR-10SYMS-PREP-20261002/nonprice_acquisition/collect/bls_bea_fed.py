#!/usr/bin/env python
"""BLS / Fed collector (NONPRICE-DATA-ACQUISITION).

Findings (probes, 2026-10-02, browser-like UA):
- www.bls.gov returns HTTP 403 for news-release archives, /schedule, and
  download.bls.gov flat files -> LAWFUL GATE, recorded, NOT bypassed.
  Fallback (typed in readiness): ALFRED realtime vintages for CPIAUCSL and
  PAYEMS (fred_alfred.py collects them; each vintage date = a release date,
  first vintage per observation = first print).
- federalreserve.gov pages are reachable (200): fomccalendars.htm covers
  recent years; fomchistorical{YYYY}.htm covers 2010+; statements follow
  /newsevents/pressreleases/monetary{YYYYMMDD}a.htm.

Usage:
  python bls_bea_fed.py --smoke
  python bls_bea_fed.py            # FOMC calendars+historical+statements 2010..2026,
                                    # BLS 403 evidence probes (bounded), BEA skipped (not required)
"""
from __future__ import annotations
import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import common

FAMILY = "bls_fed"
FED = "https://www.federalreserve.gov"
START_YEAR, END_YEAR = 2010, 2026

BLS_PROBES = [
    "https://www.bls.gov/schedule/news-release/2026_schedule.htm",
    "https://www.bls.gov/news-release/archives/cpi_09112024.htm",
    "https://www.bls.gov/news-release/archives/empsit_09112024.htm",
    "https://download.bls.gov/pub/time.series/cu/cu.data.1.AllItems",
]


def fed_calendars() -> list[dict]:
    recs = []
    recs.append(common.http_get(f"{FED}/monetarypolicy/fomccalendars.htm", family=FAMILY,
                                rel_path="fed/fomccalendars.htm", rate_limit_s=0.8,
                                max_bytes=8 * 1024**2))
    for y in range(START_YEAR, 2021):  # historical pages cover through 2020; calendars.htm carries 2021+
        recs.append(common.http_get(f"{FED}/monetarypolicy/fomchistorical{y}.htm", family=FAMILY,
                                    rel_path=f"fed/fomchistorical{y}.htm", rate_limit_s=0.8,
                                    max_bytes=8 * 1024**2))
    return recs


def statement_urls() -> list[str]:
    """Collect monetary policy statement URLs from the downloaded calendar pages."""
    urls = set()
    for rel in ["fed/fomccalendars.htm"] + [f"fed/fomchistorical{y}.htm" for y in range(START_YEAR, 2021)]:
        p = common.RAW_ROOT / rel
        if not p.exists():
            continue
        text = p.read_text(errors="replace")
        for m in re.finditer(r'href="(/newsevents/pressreleases/monetary\d{8}[a-z]?\.htm)"', text):
            urls.add(m.group(1))
        # historical pages also link chair-ish press releases; keep only monetary ones
    return sorted(urls)


def fetch_statements(urls: list[str]) -> list[dict]:
    recs = []
    for i, u in enumerate(urls):
        name = u.rsplit("/", 1)[-1].replace(".htm", "")
        recs.append(common.http_get(f"{FED}{u}", family=FAMILY,
                                    rel_path=f"fed/statements/{name}.html",
                                    rate_limit_s=0.6, max_bytes=2 * 1024**2))
        if (i + 1) % 40 == 0:
            print(f"  statements {i+1}/{len(urls)}")
    return recs


def bls_gate_probes() -> list[dict]:
    """Bounded evidence of the BLS 403 gate (4 requests max, no hammering)."""
    recs = []
    for url in BLS_PROBES:
        recs.append(common.http_get(url, family=FAMILY,
                                    rel_path=f"bls_gate/{url.split('//')[1].replace('/', '_')}",
                                    rate_limit_s=1.0, retries=1, max_bytes=1 * 1024**2))
    return recs


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--statements-only", action="store_true")
    args = ap.parse_args()

    results = []
    if args.statements_only:
        urls = statement_urls()
        print(f"statement urls: {len(urls)}")
        results += fetch_statements(urls)
    elif args.smoke:
        results += fed_calendars()[:1]
        results += bls_gate_probes()[:1]
    else:
        results += fed_calendars()
        urls = statement_urls()
        print(f"statement urls: {len(urls)}")
        results += fetch_statements(urls)
        results += bls_gate_probes()

    ok = [r for r in results if r.get("status") == "ok"]
    er = [r for r in results if r.get("status") == "http_error"]
    print(json.dumps({"ok": len(ok), "http_error": len(er),
                      "error_samples": [r["path"] for r in er[:6]],
                      "bytes": sum(int(r.get("bytes", 0)) for r in ok),
                      "summary": common.summary()}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
