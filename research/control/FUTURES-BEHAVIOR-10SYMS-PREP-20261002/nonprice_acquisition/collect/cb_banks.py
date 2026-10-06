#!/usr/bin/env python
"""Central banks / stat offices collector (NONPRICE-DATA-ACQUISITION).

Verified key-free routes (probes 2026-10-02):
- ECB SDW data API (no key, CSV): ESTR daily + key ECB interest rates.
- BoJ: /en/mopo/mpmsche_minu/index.htm (MPM calendar),
       /en/mopo/mpmdeci/index.htm -> per-year /en/mopo/mpmdeci/mpr_{YYYY}/index.htm
       -> statement pages.
- MOF FEIO: /english/policy/international_policy/reference/feio/quarter/index.html
       -> {YYYY}_{Q}Qe.html quarterly intervention releases (+ historical data files).
- BoE: /boeapps/database/Bank-Rate.asp (official Bank Rate history),
       /-/media/boe/files/statistics/yield-curves/glcnominalddata.zip (nominal gilt
       daily curve data, latest-vintage official - DECLARED_LAG for PIT).
- ONS: releasecalendar page (current window) + CPI dataset page (current).
       Historical calendar/first-print route NOT_FOUND this session (typed MISSING).
- gov.uk: autumn-statement-documents collection (fiscal events); Budget collection
       route attempts recorded.
- RBA: rba.gov.au returns HTTP 403 to automated fetch (recorded gate; RBA decision
       dates/times already FACT in configs/symbols/6A.yaml from the dossier lane).

Usage:
  python cb_banks.py --smoke
  python cb_banks.py
"""
from __future__ import annotations
import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import common

FAMILY = "cb"
START_YEAR, END_YEAR = 2010, 2026


def ecb() -> list[dict]:
    recs = []
    recs.append(common.http_get(
        "https://data-api.ecb.europa.eu/service/data/EST/B.EU000A2X2A25.WT?format=csvdata",
        family=FAMILY, rel_path="ecb/estr_daily_full.csv", rate_limit_s=0.8,
        max_bytes=12 * 1024**2))
    recs.append(common.http_get(
        "https://data-api.ecb.europa.eu/service/data/FM/B.U2.EUR.4F.KR.MRR_FR.LEV?format=csvdata&startPeriod=2009-01-01",
        family=FAMILY, rel_path="ecb/key_ecb_interest_rates_mro.csv", rate_limit_s=0.8,
        max_bytes=4 * 1024**2))
    return recs


def boj() -> list[dict]:
    recs = []
    recs.append(common.http_get("https://www.boj.or.jp/en/mopo/mpmsche_minu/index.htm",
                                family=FAMILY, rel_path="boj/mpmsche_minu_index.html",
                                rate_limit_s=0.8, max_bytes=4 * 1024**2))
    recs.append(common.http_get("https://www.boj.or.jp/en/mopo/mpmdeci/index.htm",
                                family=FAMILY, rel_path="boj/mpmdeci_index.html",
                                rate_limit_s=0.8, max_bytes=4 * 1024**2))
    for y in range(START_YEAR, END_YEAR + 1):
        recs.append(common.http_get(
            f"https://www.boj.or.jp/en/mopo/mpmdeci/mpr_{y}/index.htm",
            family=FAMILY, rel_path=f"boj/mpmdeci/mpr_{y}_index.html",
            rate_limit_s=0.8, max_bytes=4 * 1024**2))
    return recs


def boj_statement_urls() -> list[str]:
    urls = set()
    for y in range(START_YEAR, END_YEAR + 1):
        p = common.RAW_ROOT / f"boj/mpmdeci/mpr_{y}_index.html"
        if not p.exists():
            continue
        text = p.read_text(errors="replace")
        # 2018+: /en/mopo/mpmdeci/state_{YYYY}/k{YYMMDD}a.htm
        for m in re.finditer(r'href="(/en/mopo/mpmdeci/state_\d{4}/k\d+[a-z]\.htm)"', text):
            urls.add(m.group(1))
        # 2010-2017: /en/mopo/mpmdeci/mpr_{YYYY}/k{YYMMDD}a.pdf
        for m in re.finditer(r'href="(/en/mopo/mpmdeci/mpr_\d{4}/k\d+[a-z]\.pdf)"', text):
            urls.add(m.group(1))
    return sorted(urls)


def boj_statements() -> list[dict]:
    urls = boj_statement_urls()
    print(f"boj statement urls: {len(urls)}")
    recs = []
    for i, u in enumerate(urls):
        fname = u.rsplit("/", 1)[-1]
        name = fname.replace(".htm", "").replace(".pdf", "")
        y = re.search(r"(?:state|mpr)_(\d{4})", u).group(1)
        ext = ".pdf" if u.endswith(".pdf") else ".html"
        recs.append(common.http_get(f"https://www.boj.or.jp{u}", family=FAMILY,
                                    rel_path=f"boj/statements/{y}/{name}{ext}",
                                    rate_limit_s=0.6, max_bytes=4 * 1024**2))
        if (i + 1) % 40 == 0:
            print(f"  boj stmts {i+1}/{len(urls)}")
    return recs


def mof() -> list[dict]:
    recs = []
    base = "https://www.mof.go.jp/english/policy/international_policy/reference/feio"
    idx = common.http_get(f"{base}/quarter/index.html", family=FAMILY,
                          rel_path="mof/feio_quarter_index.html", rate_limit_s=0.8,
                          max_bytes=4 * 1024**2)
    recs.append(idx)
    # Full official daily intervention operations history (CSV, key-free):
    recs.append(common.http_get(
        f"{base}/foreign_exchange_intervention_operations.csv", family=FAMILY,
        rel_path="mof/foreign_exchange_intervention_operations.csv",
        rate_limit_s=0.8, max_bytes=8 * 1024**2))
    # quarterly data archive index (as-published quarterly data pages)
    recs.append(common.http_get(
        f"{base}/data/quarter/index.html", family=FAMILY,
        rel_path="mof/feio_data_quarter_index.html", rate_limit_s=0.8,
        max_bytes=4 * 1024**2))
    # recent quarterly English release pages (2019+ pattern verified 2026; older
    # years 404 -> the CSV + data archive is the complete record)
    for y in range(2019, END_YEAR + 1):
        for q in (1, 2, 3, 4):
            recs.append(common.http_get(f"{base}/quarter/{y}_{q}Qe.html", family=FAMILY,
                                        rel_path=f"mof/quarters/{y}_{q}Qe.html",
                                        rate_limit_s=0.6, max_bytes=2 * 1024**2))
    # monthly release index (finer granularity)
    recs.append(common.http_get(f"{base}/monthly/index.html", family=FAMILY,
                                rel_path="mof/feio_monthly_index.html", rate_limit_s=0.8,
                                max_bytes=4 * 1024**2))
    return recs


def boe() -> list[dict]:
    recs = []
    recs.append(common.http_get(
        "https://www.bankofengland.co.uk/boeapps/database/Bank-Rate.asp",
        family=FAMILY, rel_path="boe/bank_rate_history.html", rate_limit_s=0.8,
        max_bytes=4 * 1024**2))
    recs.append(common.http_get(
        "https://www.bankofengland.co.uk/statistics/yield-curves",
        family=FAMILY, rel_path="boe/yield_curves_page.html", rate_limit_s=0.8,
        max_bytes=4 * 1024**2))
    recs.append(common.http_get(
        "https://www.bankofengland.co.uk/-/media/boe/files/statistics/yield-curves/glcnominalddata.zip",
        family=FAMILY, rel_path="boe/glcnominalddata.zip", rate_limit_s=0.8,
        max_bytes=40 * 1024**2))
    return recs


def ons_govuk() -> list[dict]:
    recs = []
    recs.append(common.http_get("https://www.ons.gov.uk/releasecalendar",
                                family=FAMILY, rel_path="ons/releasecalendar_current.html",
                                rate_limit_s=0.8, max_bytes=4 * 1024**2))
    recs.append(common.http_get(
        "https://www.ons.gov.uk/economy/inflationandpriceindices/datasets/consumerpriceinflation",
        family=FAMILY, rel_path="ons/cpi_dataset_current.html", rate_limit_s=0.8,
        max_bytes=4 * 1024**2))
    recs.append(common.http_get(
        "https://www.gov.uk/government/collections/autumn-statement-documents",
        family=FAMILY, rel_path="govuk/autumn_statement_collection.html",
        rate_limit_s=0.8, max_bytes=4 * 1024**2))
    # Budget collection route evidence (recorded attempts)
    recs.append(common.http_get(
        "https://www.gov.uk/government/collections/budget-documents",
        family=FAMILY, rel_path="govuk/budget_collection_attempt.html",
        rate_limit_s=0.8, max_bytes=1 * 1024**2, retries=1))
    return recs


def rba_gate() -> list[dict]:
    recs = []
    for url, rel in [
        ("https://www.rba.gov.au/monetary-policy/int-rate-decisions.html", "rba/int_rate_decisions_gate.html"),
        ("https://www.rba.gov.au/statistics/cash-rate/", "rba/cash_rate_gate.html"),
    ]:
        recs.append(common.http_get(url, family=FAMILY, rel_path=rel, rate_limit_s=1.0,
                                    retries=1, max_bytes=1 * 1024**2))
    return recs


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--statements-only", action="store_true")
    args = ap.parse_args()

    results = []
    if args.statements_only:
        results += boj_statements()
    elif args.smoke:
        results += ecb()[:1]
        results += mof()[:2]
    else:
        results += ecb()
        results += boj()
        results += boj_statements()
        results += mof()
        results += boe()
        results += ons_govuk()
        results += rba_gate()

    ok = [r for r in results if r.get("status") == "ok"]
    er = [r for r in results if r.get("status") == "http_error"]
    print(json.dumps({"ok": len(ok), "http_error": len(er),
                      "error_samples": [{"p": r["path"], "s": r.get("http_status")} for r in er[:10]],
                      "bytes": sum(int(r.get("bytes", 0)) for r in ok),
                      "summary": common.summary()}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
