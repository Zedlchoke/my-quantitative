#!/usr/bin/env python
"""V5-P0a: consolidate per-economy CPI release-date evidence into the
availability table + emit the P0 verdict bundle.

Taxonomy (P-1): EVIDENCED (official archived bytes naming the release
date), ASSERTED (schedule/rule, never authorized), UNEVIDENCED (no
official evidence located).  A bloc whose evidenced release dates do not
cover the S0 conditioning window is OUT of the per-print conditional
universe (recorded, not inferred).
"""
import hashlib
import json
import re
from datetime import date
from pathlib import Path

RUN = Path(__file__).resolve().parent
S0_START = date(2018, 4, 4)
S0_END = date(2025, 7, 24)


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def parse_gb():
    rows = json.load(open(RUN / "gb_ons_cpi_release_dates.json"))
    MONTHS = ["January", "February", "March", "April", "May", "June", "July",
              "August", "September", "October", "November", "December"]
    out = []
    for r in rows:
        if r["class"] != "EVIDENCED":
            continue
        dd, mon, yy = r["release_date_display"].split()
        d = date(int(yy), MONTHS.index(mon) + 1, int(dd))
        out.append({"reference_period": r["reference_period"],
                    "release_date": d.isoformat(),
                    "available_time_utc": d.isoformat() + "T23:59:59Z",
                    "precision": "DAY (ONS bulletin Release date field)",
                    "source": "ons.gov.uk bulletin page",
                    "archive_path": r["archive_path"],
                    "archive_sha256": r["archive_sha256"],
                    "class": "EVIDENCED"})
    return out


def parse_ca():
    rows = json.load(open(RUN / "ca_statcan_cpi_release_dates.json"))
    out = []
    for r in rows:
        d = date.fromisoformat(r["release_date"])
        main = "18100001" in r["cpi_products"]
        out.append({"reference_period": r["release_date"],
                    "release_date": r["release_date"],
                    "available_time_utc": r["release_time_utc_display"][0] + ":00Z",
                    "precision": "INSTANT (WDS releaseTime, America/Toronto 08:30)",
                    "source": "statcan.gc.ca WDS getChangedCubeList",
                    "archive_path": r["archive_path"],
                    "archive_sha256": r["archive_sha256"],
                    "class": "EVIDENCED",
                    "main_monthly_cube": main})
    return out


def parse_au():
    rows = json.load(open(RUN / "au_abs_cpi_release_dates.json"))
    out = []
    for r in rows:
        if r["class"] != "EVIDENCED":
            out.append({"reference_period": r["slug"], "class": "UNEVIDENCED",
                        "note": "Released field not present on page"})
            continue
        d = date(*map(int, r["release_date"].split("-")))
        out.append({"reference_period": r["slug"],
                    "release_date": r["release_date"],
                    "available_time_utc": r["release_date"] + "T23:59:59Z",
                    "precision": "DAY (ABS Released field)",
                    "source": "abs.gov.au release page",
                    "archive_path": r["archive_path"],
                    "archive_sha256": r["archive_sha256"],
                    "class": "EVIDENCED"})
    return out


def parse_nz():
    rows = json.load(open(RUN / "nz_statsnz_cpi_release_dates.json"))
    out = []
    for r in rows:
        if r["class"] != "EVIDENCED":
            out.append({"reference_period": r["slug"], "class": "UNEVIDENCED"})
            continue
        d = date(*map(int, r["release_date"].split("-")))
        t = r.get("release_time_local") or "10:45"
        out.append({"reference_period": r["slug"],
                    "release_date": r["release_date"],
                    "available_time_utc": r["release_date"] + "T" + t + ":45+12:00",
                    "precision": "INSTANT (Stats NZ PublicationDate)",
                    "source": "stats.govt.nz release page",
                    "archive_path": r["archive_path"],
                    "archive_sha256": r["archive_sha256"],
                    "class": "EVIDENCED"})
    return out


def bloc_summary(name, rows, status, note):
    ev = [r for r in rows if r.get("class") == "EVIDENCED"]
    inwin = [r for r in ev
             if r.get("release_date")
             and S0_START <= date.fromisoformat(r["release_date"]) <= S0_END]
    return {
        "economy": name,
        "channel_status": status,
        "note": note,
        "evidenced_prints_total": len(ev),
        "evidenced_prints_with_release_in_S0": len(inwin),
        "window": {"S0_start": S0_START.isoformat(), "S0_end": S0_END.isoformat()},
        "class": "EVIDENCED" if len(inwin) >= 12 else
                 ("PARTIAL" if ev else "UNEVIDENCED"),
        "per_print_axis_eligible": len(inwin) >= 12,
    }, rows


def main():
    gb = parse_gb()
    ca = parse_ca()
    au = parse_au()
    nz = parse_nz()

    summaries = {}
    tables = {}
    summaries["GB"], tables["GB"] = bloc_summary(
        "GB", gb, "OK (server-rendered ONS bulletin pages)",
        "ONS 'Consumer price inflation, UK' bulletins 2018-01..2025-08; "
        "official Release date field per print; 92/92 evidenced")
    summaries["CA"], tables["CA"] = bloc_summary(
        "CA", ca, "OK (WDS getChangedCubeList API)",
        "Official StatCan WDS releaseTime stamps; 107 CPI-cube release dates; "
        "scanned 1957 weekdays 2018-03..2025-08")
    summaries["AU"], tables["AU"] = bloc_summary(
        "AU", au, "PARTIAL (ABS sitemap/lists only reach 2022Q3 + monthly indicators)",
        "Pre-2023 quarterlies not discoverable (404 on constructed slugs, absent "
        "from official sitemap) -> recorded gap, not inferred")
    summaries["NZ"], tables["NZ"] = bloc_summary(
        "NZ", nz, "OK (Stats NZ sitemap + release pages)",
        "Quarterly CPI release pages; machine-readable PublicationDate")
    summaries["US"], tables["US"] = bloc_summary(
        "US", [], "UNAVAILABLE_FAIL_CLOSED",
        "BLS www+download hosts return HTTP 403 with explicit anti-bot policy "
        "(archived); api.bls.gov carries no per-print release dates; Federal "
        "Register holds OMB paperwork notices only. Per-print release dates "
        "NOT evidenced by any keyless scripted official channel. "
        "Owner option: hand-provide BLS archival pages (V8 precedent).")
    summaries["JP"], tables["JP"] = bloc_summary(
        "JP", [], "FORWARD_SCHEDULE_ONLY",
        "stat.go.jp Schedule of Release covers Jan 2026..Mar 2027 (fetched); "
        "no scripted-keyless archive of 2018-2025 release dates located. "
        "Historical S0 prints remain UNEVIDENCED.")
    summaries["CH"], tables["CH"] = bloc_summary(
        "CH", [], "UNEVIDENCED",
        "BFS site is a JS application; press-release archive not scriptable "
        "keyless; no per-print release dates located.")
    summaries["EMU"], tables["EMU"] = bloc_summary(
        "EMU", [], "DATA_YES_TIMING_NO",
        "Eurostat dissemination API serves HICP values keyless, but the "
        "release calendar is JS-rendered and news pages sit behind an EU "
        "Login interstitial; per-print release dates NOT evidenced. "
        "(EMU *policy* announcements were upgraded in P0c; this row is the "
        "CPI print axis.)")

    out = {
        "schema": "forex_free_v5_p0a_cpi_availability_v1",
        "measured_at_utc": __import__("datetime").datetime.utcnow().isoformat() + "Z",
        "producer": "A1_FOREX_CONTROLLER",
        "authority": "PLAN_forex_v5.md section 3 P0a; LESSONS.md P-1 taxonomy",
        "taxonomy": "EVIDENCED / ASSERTED(never authorized) / UNEVIDENCED",
        "blocs": summaries,
        "per_print_conditional_universe": [k for k, v in summaries.items()
                                           if v["per_print_axis_eligible"]],
        "out_blocs": [k for k, v in summaries.items()
                      if not v["per_print_axis_eligible"]],
        "asserted_bounds_used": "NONE (asserted bounds never authorized)",
    }
    (RUN / "p0a_cpi_availability_table.json").write_text(json.dumps(out, indent=1))
    (RUN / "p0a_cpi_prints_gb.json").write_text(json.dumps(tables["GB"], indent=1))
    (RUN / "p0a_cpi_prints_ca.json").write_text(json.dumps(tables["CA"], indent=1))
    (RUN / "p0a_cpi_prints_au.json").write_text(json.dumps(tables["AU"], indent=1))
    (RUN / "p0a_cpi_prints_nz.json").write_text(json.dumps(tables["NZ"], indent=1))
    print(json.dumps({k: {kk: v[kk] for kk in ("channel_status", "evidenced_prints_total",
                                               "evidenced_prints_with_release_in_S0", "class",
                                               "per_print_axis_eligible")}
                      for k, v in summaries.items()}, indent=1))


if __name__ == "__main__":
    main()
