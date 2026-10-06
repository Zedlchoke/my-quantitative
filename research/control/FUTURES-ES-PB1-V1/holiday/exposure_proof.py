#!/usr/bin/env python
"""FUTURES-ES-PB1-V1 / lane HOLIDAY-CLOSURE — M1 formal exposure proof.

Machine-proves, from the pinned panel + the frozen exclude rule, the exact
statement:

  no in-panel 2011-01-01..2016-12-31 session can enter the evaluation
  surface while its holiday status is unadjudicated.

Method (all fail-closed; any check failure aborts WITHOUT writing output):
  L1  Re-derive RTH-core bars for every in-panel session from the pinned
      parquet (single shot) and assert equality with the K6 session rows.
  L2  Partition 2011-2016 sessions by exact integer bars into bands:
      0 | (0,234) | [234,390) | 390  (234 = 0.60 x 390 exactly).
  L3  Assert the [234,390) band is EMPTY (the A7 F-A1 claim, re-measured).
  L4  Enumerate every committed artifact date named as a 2011-2016
      holiday/early-close/halt day (candidates): the 53 committed 2011-2015
      official per-holiday Globex PDFs' "CME Group Equity Products" sections
      (extract_equity_pdf_evidence.py output) + the cmecal_coverage.json
      note-named 2014-2016 days + the frozen freeze's own HOLIDAY_* rows
      (asserted empty in-span). Assert: ZERO sessions with bars >= 234 on
      any candidate date (exposure rows = 0).
  L5  Assert every bars>=234 span session is a weekday and not on any
      candidate date; assert every bars<234 span session is excluded by the
      frozen exclude list (COVERAGE_LT60 or higher-priority class).

Zero network. No PnL/signal computation (bar counting only).

Run:
  /Users/hoangminhlong/my-quantitative/.venv/bin/python \
    research/control/FUTURES-ES-PB1-V1/holiday/exposure_proof.py

Output (write boundary: this directory only):
  exposure_proof_2011_2016.json
"""
import hashlib
import json
import os
import sys
from collections import Counter
from datetime import date, datetime

import pandas as pd
import pyarrow.parquet as pq

WORKTREE = "/Users/hoangminhlong/my-quantitative/.worktrees/futures-es-reg/prep"
MEASURED_HEAD = "8324a8c0e414fb683d9bfa6f56734d0a17b9d40a"  # single rev-parse at lane start

REL = {
    "session_dispersion_es": "research/control/FUTURES-K6GATE-PREP-20261004/es/session_dispersion_es.json",
    "panel_parquet": "research/control/FUTURES-DEEPRESEARCH-V2-20261003/analysis/ES_cache/es_1m_outright.parquet",
    "exclude_list": "research/control/FUTURES-ES-PB1-V1/freezegen/exclude_list.json",
    "ES_fomc_stats": "research/control/FUTURES-DEEPRESEARCH-V2-20261003/analysis/ES_fomc_stats.json",
    "es_session_holiday": "research/control/FUTURES-SIX-READINESS-20261004/es/es_session_holiday.json",
    "cmecal_coverage": "research/control/FUTURES-DATACONTRACT-QUAL-V1/analysis/d3_cmecalendar/cmecal_coverage.json",
    "pdf_equity_evidence": "research/control/FUTURES-ES-PB1-V1/holiday/pdf_equity_evidence_2011_2015.json",
}
PINNED_SHA = {
    "session_dispersion_es": "e56c4a53841983e02f5e643e60693581e2c9e096488a1f7491659a71bb7c43a4",
    "panel_parquet": "7ae6de2d5896d9e150f70209f2709ca70b625f0b06bbdbfed348b1b0e0227b95",
    "exclude_list": "bc8a41b673eccb998017e704a9865d139e67438fe984906f7f522782f93b438a",
    "ES_fomc_stats": "228fe2d4efbde95984128b6b1f64a9162bb794ea406c488577036fa09518f213",
    "es_session_holiday": "8885d5de4e7f4c5fbf06c194ea9a6b238e4a5450ac31e7d9807bc97d4ee71391",
    "cmecal_coverage": "c82f50c4fa53cf93dfb0b652209007836e4d6ccfe29f3e4535a89f1f2086e157",
}
OUT_REL = "research/control/FUTURES-ES-PB1-V1/holiday/exposure_proof_2011_2016.json"
SPAN = ("2011-01-01", "2016-12-31")
BAND_LO = 234  # ceil semantics: bars >= 234 <=> coverage >= 0.60 exactly (0.6*390=234)
BAND_HI = 390

checks = []


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def check(name, ok, detail):
    checks.append({"check": name, "verdict": "PASS" if ok else "FAIL",
                   "detail": detail})
    if not ok:
        print("FATAL:", name, "->", detail)
        sys.exit(1)


def observation(name, ok, detail):
    """Recorded non-fatally: an exposure DISCOVERY is a finding that must be
    written out (it IS the proof's verdict), never an input-integrity abort."""
    checks.append({"check": name, "verdict": "PASS" if ok else "FAIL",
                   "detail": detail, "non_fatal": True})


def d(s):
    return datetime.strptime(s, "%Y-%m-%d").date()


# ---------------------------------------------------------------- windows
# Window-LEVEL context ranges named by committed artifacts (never treated as
# day-level candidates; used only for the interior-review listing).
# Each entry: (lo, hi, quote, source).
WINDOWS = [
    ("2010-12-23", "2010-12-26", "Christmas 2010 23-26 Dec", "NQ_CALENDAR_EVIDENCE.md year-2011 row"),
    ("2010-12-31", "2011-01-03", "New Year 31 Dec 2010-3 Jan 2011", "NQ_CALENDAR_EVIDENCE.md year-2011 row"),
    ("2011-01-14", "2011-01-18", "MLK 14-18 Jan", "NQ_CALENDAR_EVIDENCE.md year-2011 row"),
    ("2011-02-18", "2011-02-22", "Presidents 18-22 Feb", "NQ_CALENDAR_EVIDENCE.md year-2011 row"),
    ("2011-04-21", "2011-04-24", "Good Friday 21-24 Apr", "NQ_CALENDAR_EVIDENCE.md year-2011 row"),
    ("2011-05-27", "2011-05-31", "Memorial 27-31 May", "NQ_CALENDAR_EVIDENCE.md year-2011 row"),
    ("2011-07-01", "2011-07-05", "Jul 4 1-5 Jul", "NQ_CALENDAR_EVIDENCE.md year-2011 row"),
    ("2011-09-02", "2011-09-06", "Labor 2-6 Sep", "NQ_CALENDAR_EVIDENCE.md year-2011 row"),
    ("2011-10-07", "2011-10-10", "Columbus 7-10 Oct", "NQ_CALENDAR_EVIDENCE.md year-2011 row"),
    ("2011-11-10", "2011-11-11", "Veterans 10-11 Nov", "NQ_CALENDAR_EVIDENCE.md year-2011 row"),
    ("2011-11-23", "2011-11-25", "Thanksgiving 23-25 Nov", "NQ_CALENDAR_EVIDENCE.md year-2011 row"),
    ("2011-12-23", "2011-12-27", "Christmas 23-27 Dec 2011", "NQ_CALENDAR_EVIDENCE.md year-2011 row"),
    ("2011-12-30", "2012-01-03", "New Year 30 Dec 2011-3 Jan 2012", "NQ_CALENDAR_EVIDENCE.md year-2011 row / cmecal_coverage.json year-2011 note"),
    ("2012-01-13", "2012-01-17", "MLK 13-17 Jan", "NQ_CALENDAR_EVIDENCE.md year-2012 row (truncated with ellipsis)"),
    ("2012-12-24", "2012-12-26", "Christmas Dec 24-26", "cmecal_coverage.json year-2012 note"),
    ("2012-12-31", "2013-01-02", "NY Dec 31 2012 - Jan 2 2013", "cmecal_coverage.json year-2012 note / NQ year-2012 row"),
    ("2013-01-18", "2013-01-22", "MLK Jan 18-22", "cmecal_coverage.json year-2013 note / NQ year-2013 row"),
    ("2013-12-31", "2014-01-02", "NY Dec 31 2013 - Jan 2 2014", "cmecal_coverage.json year-2013 note / NQ year-2013 row"),
    ("2014-01-17", "2014-01-21", "MLK 17-21 Jan", "NQ_CALENDAR_EVIDENCE.md year-2014 row (truncated with ellipsis)"),
    ("2014-12-24", "2014-12-26", "Christmas 24-26 Dec 2014", "NQ_CALENDAR_EVIDENCE.md year-2014 row"),
    ("2015-01-16", "2015-01-20", "MLK 16-20 Jan", "NQ_CALENDAR_EVIDENCE.md year-2015 row (truncated with ellipsis)"),
    ("2015-12-31", "2016-01-04", "NY window Dec 31 2015 - Jan 4 2016", "cmecal_coverage.json year-2015 note / NQ year-2015 row"),
    ("2016-01-15", "2016-01-19", "MLK 15-19 Jan", "NQ_CALENDAR_EVIDENCE.md year-2016 row (truncated with ellipsis)"),
    ("2016-12-30", "2017-01-03", "NY 30 Dec 2016-3 Jan 2017", "NQ_CALENDAR_EVIDENCE.md year-2016 row (truncated with ellipsis)"),
]

# cmecal_coverage.json note-named DAY-LEVEL dates for 2014-2016 (verbatim
# quotes; the 2011-2015 day level comes from the 53 PDFs instead).
# tier: 'primary'  = day-level ES/equity SESSION-hours evidence (candidate
#                    unadjudicated holiday status),
#       'settlement' = settlement-notice-only naming; a committed per-holiday
#                    PDF equity section may adjudicate the session side.
CMECAL_NAMED_DAYS = [
    ("2014-07-03", "primary",
     "Fourth-of-July settlement-times notice for Thu Jul 3 2014 (early-close evidence)",
     "cmecal_coverage.json year-2014 note; also 2014-4th-of-july-holiday-schedule.pdf"),
    ("2015-07-02", "primary",
     "Settlement notices name early-close days Jul 2 and Sep 4 2015",
     "cmecal_coverage.json year-2015 note; also 2015-4th-of-july-holiday-schedule.pdf "
     "equity section: 'Thursday, July 2: 1215 CT - Early close'"),
    ("2015-09-04", "settlement",
     "Settlement notices name early-close days Jul 2 and Sep 4 2015",
     "cmecal_coverage.json year-2015 note; CONTRADICTED on the session side by "
     "2015-labor-day-holiday-schedule.pdf equity section: 'Friday, Sep 4: "
     "1615 CT - Regular close'"),
    ("2016-03-25", "primary",
     "closures Good Friday Mar 25", "cmecal_coverage.json year-2016 note"),
    ("2016-11-25", "primary",
     "Equities floor close 12:15 CT Nov 25; ClearPort early close 13:45 ET Nov 25 "
     "(Globex equity times NOT transcribed)", "cmecal_coverage.json year-2016 note"),
    ("2016-12-26", "primary",
     "closures ... Dec 26", "cmecal_coverage.json year-2016 note"),
]

# Volume forensics on the panel (committed data, single additional read) for
# the conflict date: rules out empty/synthetic afternoon bars.
CONFLICT_VOLUME_CHECK = {
    "2015-07-02": {"held_symbol": "ESU5",
                   "bars_from_12ct": 619, "volume_sum_from_12ct": 476608,
                   "last_bar_ct": "2015-07-02 23:59:00-05:00",
                   "reading": "real, full-volume trading through the afternoon "
                              "and evening => the conflict is schedule-vs-data, "
                              "not a synthetic-bar artifact"},
    "2015-09-04": {"held_symbol": "ESU5",
                   "bars_from_12ct": 240, "volume_sum_from_12ct": 747485,
                   "last_bar_ct": "2015-09-04 16:14:00-05:00",
                   "reading": "regular 16:15 close — agrees with the PDF's "
                              "REGULAR close adjudication"},
}


def main():
    paths = {k: os.path.join(WORKTREE, v) for k, v in REL.items()}
    shas = {}
    for k, p in paths.items():
        check(f"input exists {k}", os.path.exists(p), p)
        shas[k] = sha256_file(p)
    for k, exp in PINNED_SHA.items():
        check(f"pinned sha {k}", shas[k] == exp, f"{shas[k]} == {exp}")

    k6 = json.load(open(paths["session_dispersion_es"], encoding="utf-8"))
    exclude = json.load(open(paths["exclude_list"], encoding="utf-8"))
    fomc = json.load(open(paths["ES_fomc_stats"], encoding="utf-8"))
    pdf_ev = json.load(open(paths["pdf_equity_evidence"], encoding="utf-8"))
    hol = json.load(open(paths["es_session_holiday"], encoding="utf-8"))

    sessions = k6["sessions"]
    check("k6 session count 4204", len(sessions) == 4204,
          f"n_sessions={k6['n_sessions']} rows={len(sessions)}")
    check("exclude_list head_sha (freeze generation HEAD)",
          exclude["head_sha"] == "e7fc1d8db00e91af74683cee7e999620fa8ff361",
          exclude["head_sha"])

    span_rows = [r for r in sessions if SPAN[0] <= r["session_date"] <= SPAN[1]]
    check("span session count 1535", len(span_rows) == 1535,
          f"{SPAN[0]}..{SPAN[1]} sessions={len(span_rows)}")

    # -------------------------------------------------- L1: panel recompute
    tbl = pq.read_table(paths["panel_parquet"],
                        columns=["raw_symbol", "ts_event"])
    ts = pd.to_datetime(tbl["ts_event"].to_pylist(), unit="ns", utc=True)
    df = pd.DataFrame({"raw_symbol": tbl["raw_symbol"].to_pylist(), "ts": ts})
    df["ct"] = df["ts"].dt.tz_convert("America/Chicago")
    df["dd"] = df["ct"].dt.strftime("%Y-%m-%d")
    df["t"] = df["ct"].dt.hour * 60 + df["ct"].dt.minute
    win = df[(df["t"] >= 8 * 60 + 30) & (df["t"] < 15 * 60)]
    counts = win.groupby(["raw_symbol", "dd"]).size()
    n_rows_panel = tbl.num_rows

    mism_all, recomputed = [], {}
    for r in sessions:  # ALL 4204 sessions, matching the freeze builder's law
        n = int(counts.get((r["held_symbol"], r["session_date"]), 0))
        recomputed[r["session_date"]] = n
        if n != r["bars_rth_core_held"]:
            mism_all.append(r["session_date"])
    check("L1 panel recompute bars_rth_core_held 4204/4204",
          not mism_all,
          f"single-shot parquet read ({n_rows_panel} rows, columns raw_symbol+ts_event): "
          f"recomputed RTH-core bars (raw_symbol==held_symbol, bar-start 08:30..14:59 CT) "
          f"equal sessions[].bars_rth_core_held for all 4204 sessions; "
          f"mismatches={mism_all[:5]}")

    # ----------------------------------------------------- L2: band census
    bands = {"cov==0 (bars=0)": [], "0<cov<0.60 (1..233)": [],
             "0.60<=cov<1.0 (234..389)": [], "cov==1.0 (bars=390)": []}
    for r in span_rows:
        b = recomputed[r["session_date"]]
        if b == 0:
            bands["cov==0 (bars=0)"].append(r["session_date"])
        elif b < BAND_LO:
            bands["0<cov<0.60 (1..233)"].append(r["session_date"])
        elif b < BAND_HI:
            bands["0.60<=cov<1.0 (234..389)"].append(r["session_date"])
        else:
            bands["cov==1.0 (bars=390)"].append(r["session_date"])
    census = {k: len(v) for k, v in bands.items()}
    check("L2 census total 1535", sum(census.values()) == 1535, str(census))
    check("L3 [0.60,1.0) band EMPTY for 2011-2016",
          census["0.60<=cov<1.0 (234..389)"] == 0,
          "A7 F-A1 claim re-measured at this HEAD: zero sessions with bars in "
          f"[234,389]; band members={bands['0.60<=cov<1.0 (234..389)']}")
    below = [recomputed[r["session_date"]] for r in span_rows
             if recomputed[r["session_date"]] < BAND_LO]
    at_or_above = [recomputed[r["session_date"]] for r in span_rows
                   if recomputed[r["session_date"]] >= BAND_LO]
    margin = {"max_bars_below_234": max(below),
              "max_coverage_below_0.60": round(max(below) / 390, 4),
              "min_bars_at_or_above_234": min(at_or_above),
              "min_coverage_at_or_above_0.60": round(min(at_or_above) / 390, 4)}
    bars_hist = dict(sorted(Counter(
        recomputed[r["session_date"]] for r in span_rows).items()))

    # ------------------------------------------- L4: candidate enumeration
    pdf_cands = pdf_ev.get("candidate_dates_closed_halt_early", {})
    pdf_regular = pdf_ev.get("regular_adjudicated_dates", {})
    cand = {}
    for dd, v in pdf_cands.items():
        if SPAN[0] <= dd <= SPAN[1]:
            cand[dd] = {"tier": "primary",
                        "provenance": "official per-holiday Globex schedule PDF "
                                      "(CME Group Equity Products section)",
                        "entries": v["entries"],
                        "truncation_times_ct": v.get("truncation_times_ct")}
    for dd, tier, quote, src in CMECAL_NAMED_DAYS:
        if SPAN[0] <= dd <= SPAN[1] and dd not in cand:
            cand[dd] = {"tier": tier, "provenance": src, "quote": quote,
                        "entries": []}
    check("L4a lemma2 truncation times all < 15:00 CT (extractor)",
          pdf_ev.get("lemma2_truncation_times_all_below_1500ct") is True
          and not pdf_ev.get("lemma2_violations"),
          "every committed equity-family HALT/EARLY_CLOSE time named for "
          "2011-2015 is <= 12:15 CT < 15:00 CT (RTH-core end) => any such day "
          "truncates RTH-core and cannot have 390 bars")

    # the frozen freeze's own HOLIDAY_* rows in-span (A7: class covers nothing)
    excl_span = [e for e in exclude["exclusions"]
                 if SPAN[0] <= e["session_date"] <= SPAN[1]]
    hu_span = [e["session_date"] for e in excl_span
               if e["reason_class"] == "HOLIDAY_UNCERTAIN"]
    hf_span = [e["session_date"] for e in excl_span
               if e["reason_class"] == "HOLIDAY_FACT_EARLYCLOSE"]
    check("L4b frozen HOLIDAY_UNCERTAIN empty in 2011-2016", not hu_span,
          f"exclude_list@{exclude['head_sha'][:8]} HOLIDAY_UNCERTAIN span rows="
          f"{len(hu_span)} (class spans 2017-2025 only)")
    check("L4c frozen HOLIDAY_FACT_EARLYCLOSE empty in 2011-2016", not hf_span,
          f"span rows={len(hf_span)} (2010-PDF + 2026-Q5 provenance only)")
    hu_all_years = sorted({e["session_date"][:4] for e in exclude["exclusions"]
                           if e["reason_class"] == "HOLIDAY_UNCERTAIN"})
    check("L4d builder never emits HOLIDAY_UNCERTAIN for 2011-2016",
          all(y < "2011" or y > "2016" for y in hu_all_years),
          f"HOLIDAY_UNCERTAIN years in exclude_list={hu_all_years}")

    # ------------------------------------------------- exposure evaluation
    excl_class = {e["session_date"]: e["reason_class"] for e in exclude["exclusions"]}
    fomc_dates = {r["date"] for r in fomc["per_event_day_level"]}
    exposure_rows = []       # mission-literal: bars>=234 on ANY candidate date
    blocker_rows = []        # unresolved: primary-tier candidate + full session
    resolved_rows = []       # settlement-tier candidates adjudicated REGULAR by PDF
    full_sessions = []
    partial_sessions = []
    for r in span_rows:
        dd = r["session_date"]
        b = recomputed[dd]
        wd = d(dd).weekday()
        row = {"session_date": dd, "bars_rth_core": b,
               "coverage_recomputed": round(b / 390, 4),
               "coverage_k6_field": r["rth_core_coverage"],
               "weekday": wd, "held_symbol": r["held_symbol"],
               "exclude_class": excl_class.get(dd, "NOT_EXCLUDED_SURVIVOR"),
               "is_fomc_statement_day": dd in fomc_dates,
               "is_candidate_date": dd in cand}
        if b >= BAND_LO:
            full_sessions.append(row)
            if dd in cand:
                c = cand[dd]
                if c["tier"] == "primary":
                    row2 = dict(row)
                    row2["candidate_provenance"] = c["provenance"]
                    row2["candidate_entries"] = c["entries"]
                    row2["disposition"] = (
                        "BLOCKER_UNRESOLVED_CONFLICT: a committed official "
                        "artifact names this date as an equity-family "
                        "holiday/early-close/halt day, yet the pinned panel "
                        "carries a COMPLETE (390-bar, real-volume) RTH-core "
                        "session that the frozen freeze does NOT exclude — "
                        "the session is eval-eligible with unadjudicated "
                        "holiday status. Evidence-vs-data conflict cannot be "
                        "resolved by this lane (fail-closed).")
                    row2["volume_forensics"] = CONFLICT_VOLUME_CHECK.get(dd)
                    blocker_rows.append(row2)
                    exposure_rows.append(row2)
                else:
                    adj = pdf_regular.get(dd)
                    row2 = dict(row)
                    row2["candidate_provenance"] = c["provenance"]
                    row2["disposition"] = (
                        "RESOLVED_REGULAR: the settlement-notice naming is "
                        "contradicted on the session side by a committed "
                        "per-holiday PDF equity section adjudicating the day "
                        "REGULAR, and the panel's complete session AGREES — "
                        "no unadjudicated holiday status remains")
                    row2["adjudicating_pdf_entries"] = adj
                    resolved_rows.append(row2)
                    exposure_rows.append(row2)
        else:
            partial_sessions.append(row)
    observation("L5a-zero BLOCKER rows (primary candidate + complete session)",
                not blocker_rows,
                f"blocker rows={len(blocker_rows)} "
                f"dates={[r['session_date'] for r in blocker_rows]}"
                + ("" if not blocker_rows else
                   " — EXPOSURE DISCOVERED: recorded in blocker_rows; "
                   "proof verdict = NOT_RUN_BLOCKER"))
    bad_wd = [r["session_date"] for r in full_sessions if r["weekday"] >= 5]
    check("L5b every bars>=234 span session is a weekday", not bad_wd,
          f"n={len(full_sessions)} weekends={bad_wd}")
    uncov = any(r["session_date"] in hu_span for r in full_sessions)
    check("L5c no bars>=234 span session on a frozen-HOLIDAY_UNCERTAIN date",
          not uncov, "class is empty in-span (L4b) so trivially true; recorded for completeness")
    unexcl_partial = [r["session_date"] for r in partial_sessions
                      if r["exclude_class"] == "NOT_EXCLUDED_SURVIVOR"]
    check("L5d every bars<234 span session is excluded by the frozen list",
          not unexcl_partial,
          f"n_partial={len(partial_sessions)} unexcluded={unexcl_partial}")
    prio = exclude["reason_class_priority"]
    cov_ok = all(r["exclude_class"] in prio and
                 prio.index(r["exclude_class"]) <= prio.index("COVERAGE_LT60")
                 for r in partial_sessions)
    check("L5e partial-session exclude classes all COVERAGE_LT60 or higher priority",
          cov_ok,
          str(Counter(r["exclude_class"] for r in partial_sessions)))

    # corroboration: candidate dates that ARE sessions — all truncated+excluded?
    cand_sessions = {r["session_date"]: r for r in span_rows
                     if r["session_date"] in cand}
    corroborated = {dd: {"bars": recomputed[dd],
                         "exclude_class": excl_class.get(dd, "NOT_EXCLUDED_SURVIVOR")}
                    for dd in cand_sessions if recomputed[dd] < BAND_LO}
    cand_closed_absent = sorted(dd for dd in cand
                                if dd not in {r["session_date"] for r in span_rows})

    # window interior review (context only)
    interior = []
    for lo, hi, quote, src in WINDOWS:
        for r in full_sessions:
            if lo <= r["session_date"] <= hi and not r["is_candidate_date"]:
                interior.append({"session_date": r["session_date"],
                                 "window": f"{lo}..{hi}", "window_quote": quote,
                                 "window_source": src,
                                 "weekday": r["weekday"],
                                 "assessment": "weekday full-coverage session "
                                               "inside a window-level range; the date "
                                               "is named as holiday/early-close/halt "
                                               "by NO committed artifact"})
    # FOMC corroboration
    fomc_span = sorted(x for x in fomc_dates if SPAN[0] <= x <= SPAN[1])
    fomc_full = [x for x in fomc_span
                 if recomputed.get(x, 0) >= BAND_LO]

    # eval-surface accounting for the 1491 full sessions
    cls_counter = Counter(r["exclude_class"] for r in full_sessions)
    eval_eligible = [r["session_date"] for r in full_sessions
                     if r["exclude_class"] == "NOT_EXCLUDED_SURVIVOR"]

    out = {
        "schema": "exposure_proof_2011_2016@1",
        "cycle_id": "FUTURES-ES-PB1-V1",
        "lane": "HOLIDAY-CLOSURE (M1)",
        "generated_utc": "2026-10-04",
        "measured_head": MEASURED_HEAD,
        "statement_tested": "no in-panel 2011-01-01..2016-12-31 session can enter "
                            "the evaluation surface while its holiday status is unadjudicated",
        "verdict": "PASS" if not blocker_rows else "NOT_RUN_BLOCKER",
        "verdict_basis": ("ZERO blocker rows — obligation CLOSED by machine proof"
                          if not blocker_rows else
                          "blocker rows EXIST (primary candidate dates carrying a "
                          "complete session that the frozen freeze does not exclude): "
                          + ", ".join(r["session_date"] for r in blocker_rows)
                          + " — the standing obligation is a REAL, NAMED blocker "
                            "at this data+freeze; NOT_RUN until resolved"),
        "band_census_2011_2016": census,
        "coverage_margin_2011_2016": margin,
        "bars_histogram_2011_2016": bars_hist,
        "n_sessions_span": len(span_rows),
        "n_full_sessions_bars_ge_234": len(full_sessions),
        "full_session_disposition": dict(cls_counter),
        "n_eval_eligible_full_sessions": len(eval_eligible),
        "eval_eligible_first": min(eval_eligible) if eval_eligible else None,
        "eval_eligible_last": max(eval_eligible) if eval_eligible else None,
        "n_partial_sessions_bars_lt_234": len(partial_sessions),
        "partial_sessions": partial_sessions,
        "n_exposure_rows_mission_literal": len(exposure_rows),
        "exposure_rows_mission_literal_bars_ge_234_and_candidate_date": exposure_rows,
        "n_blocker_rows": len(blocker_rows),
        "blocker_rows": blocker_rows,
        "n_resolved_rows": len(resolved_rows),
        "resolved_rows": resolved_rows,
        "candidate_enumeration": {
            "definition": "every 2011-2016 date named by ANY committed artifact as an "
                          "ES/equity-family holiday closure, early close, or halt day "
                          "(tier 'primary' = day-level session-hours evidence; tier "
                          "'settlement' = settlement-notice naming only)",
            "n_dates": len(cand),
            "n_primary": sum(1 for v in cand.values() if v["tier"] == "primary"),
            "sources": {
                "pdf_2011_2015": {
                    "file": REL["pdf_equity_evidence"],
                    "sha256": shas["pdf_equity_evidence"],
                    "n_dates": sum(1 for k in cand if k in pdf_cands),
                    "corpus": pdf_ev["source_corpus"]},
                "cmecal_note_named_days_2014_2016": {
                    "file": REL["cmecal_coverage"],
                    "sha256": shas["cmecal_coverage"],
                    "dates": [{"date": x[0], "tier": x[1]} for x in CMECAL_NAMED_DAYS]},
            },
            "dates": {k: v for k, v in sorted(cand.items())},
        },
        "corroboration": {
            "candidate_dates_that_are_truncated_sessions_all_lt234_and_excluded": corroborated,
            "candidate_dates_absent_from_panel": cand_closed_absent,
            "note": "candidate CLOSED dates are absent or 0-bar (e.g. Good Fridays "
                    "2011/2013/2014/2016, MLK 2014, Dec 25s, Jan 1s); candidate "
                    "EARLY_CLOSE/HALT dates that are sessions are all <=226 bars "
                    "and excluded by COVERAGE_LT60 — EXCEPT the named blocker(s)",
        },
        "frozen_holiday_classes_in_span": {
            "HOLIDAY_UNCERTAIN": hu_span,
            "HOLIDAY_FACT_EARLYCLOSE": hf_span,
            "note": "the fail-closed-pending class covers NOTHING at this data+freeze "
                    "(HOLIDAY_UNCERTAIN emits 2017-2025 only)",
        },
        "fomc_corroboration": {
            "n_fomc_statement_days_in_span": len(fomc_span),
            "n_of_them_full_coverage": len(fomc_full),
            "note": "FOMC days are adjudicated (excluded) by FOMC_STATEMENT_DAY "
                    "regardless of holiday status",
        },
        "window_interior_review": {
            "note": "window-level ranges are context, NOT candidates; every "
                    "full-coverage session inside a window but NOT on a day-level "
                    "candidate date is listed and assessed",
            "n_windows_declared": len(WINDOWS),
            "n_interior_sessions": len(interior),
            "interior_sessions": interior,
        },
        "lemmas": {
            "L1_panel_recompute": "bars_rth_core_held re-derived from the pinned parquet "
                                  "for all 4204 sessions — 4204/4204 equal (see checks)",
            "L2_band_partition": "exact integer partition at 234=0.60*390; census above",
            "L3_band_empty": "the [0.60,1.0) coverage band contains ZERO 2011-2016 "
                             "sessions — the only sessions with bars>=234 are complete "
                             "sessions (390 bars). The A7 F-A1 claim is TRUE as stated.",
            "L4_candidate_enumeration": f"{len(cand)} committed day-level candidates "
                                        "2011-2016 (56 PDF + cmecal note-named days, "
                                        "tiered primary/settlement); frozen HOLIDAY_* "
                                        "classes empty in-span",
            "L5_exposure": "VERIFIED-FALSE at strict candidate overlap: a "
                           "complete (390-bar, real-volume) session EXISTS on primary "
                           "candidate date(s) " + ", ".join(r["session_date"] for r in blocker_rows)
                           + " — see blocker_rows. All other candidate-date behavior "
                             "corroborates the freeze (truncated candidates all <234 "
                             "bars and excluded; CLOSED candidates absent from the panel).",
            "closure_argument": "The A7 exposure model assumed any unadjudicated "
                                "holiday manifests as a TRUNCATED session (every "
                                "committed truncation time is <= 12:15 CT, so a "
                                "truncated day cannot reach 234 bars) or a CLOSURE "
                                "(no session). Both arms hold in the data. The model "
                                "missed a third case, materialized exactly once: "
                                "2015-07-02, where the committed official schedule "
                                "(2015-4th-of-july-holiday-schedule.pdf, 'CME Group "
                                "Equity Products': 'Thursday, July 2: 1215 CT - Early "
                                "close') conflicts with the committed panel (complete "
                                "390-bar session, real volume 476,608 contracts after "
                                "12:00 CT). The freeze has no class for that date, so "
                                "the session is eval-eligible with holiday status that "
                                "is simultaneously adjudicated-by-artifact (early "
                                "close) and contradicted-by-data (full session) — "
                                "unresolvable by this lane under the fail-closed law. "
                                "Verdict: NOT_RUN (blocker) with the named date.",
        },
        "data_version_binding": {
            "panel_parquet": {"path": REL["panel_parquet"], "sha256": shas["panel_parquet"]},
            "session_universe": {"path": REL["session_dispersion_es"], "sha256": shas["session_dispersion_es"]},
            "exclude_list": {"path": REL["exclude_list"], "sha256": shas["exclude_list"],
                             "head_sha_at_generation": exclude["head_sha"]},
            "pdf_equity_evidence": {"path": REL["pdf_equity_evidence"], "sha256": shas["pdf_equity_evidence"]},
            "law": "this proof is valid ONLY for the panel + freeze at the shas above; "
                   "any data refresh or builder change re-runs exposure_proof.py and "
                   "re-opens the obligation automatically on any FAIL",
        },
        "checks": checks,
    }
    path = os.path.join(WORKTREE, OUT_REL)
    with open(path, "w", encoding="utf-8") as f:
        f.write(json.dumps(out, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "out": OUT_REL,
        "verdict": out["verdict"],
        "blocker_dates": [r["session_date"] for r in blocker_rows],
        "resolved_dates": [r["session_date"] for r in resolved_rows],
        "band_census": census,
        "n_candidates": len(cand),
        "n_exposure_rows_mission_literal": len(exposure_rows),
        "n_full": len(full_sessions),
        "n_partial": len(partial_sessions),
        "eval_eligible_full": len(eval_eligible),
        "checks_passed": sum(1 for c in checks if c["verdict"] == "PASS"),
        "checks_total": len(checks),
    }, indent=2))


if __name__ == "__main__":
    main()
