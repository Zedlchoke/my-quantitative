#!/usr/bin/env python
"""FUTURES-ES-PB1-V1 / lane BUILDER-REPAIR — M2 exposure proof re-run at the v2 freeze.

Adapts holiday/exposure_proof.py (v1, sha
6f401d1c4540a54c7fcfcdcf1f3d8c5a3febdb6aab516f7b0287476af1a6319a; v1 output
verdict NOT_RUN_BLOCKER on 2015-07-02) to the REPAIRED exclude list
repair/exclude_list_v2.json. Per owner law (PREGO HOLIDAY-REPAIR-AUTH): the
verdict comes from the machine rows, never from expectations.

Proves, per sub-epoch:
  (a) 2011-2015: zero sessions with unadjudicated holiday status inside the
      evaluation surface — every in-panel session on a 53-PDF primary-tier
      candidate date (CLOSED/HALT/EARLY_CLOSE, not PDF-adjudicated regular)
      is EXCLUDED by the v2 freeze; the 2015-07-02 blocker row is GONE.
  (b) 2016: enumerate the 2016 in-panel sessions and prove the fail-closed
      basis from committed 2016 evidence (cmecal year-2016 note-named days;
      readiness holiday json — no 2016 windows exist; cal_close FACT cells —
      2026-only): every candidate-named 2016 session is truncated+COVERAGE-
      excluded or absent; any COMPLETE session on a candidate-named 2016 date
      would be an ambiguity row and the class STAYS NOT_RUN with that named
      blocker. 2016 is NOT silently treated as resolved by the PDF class.

Zero network. No PnL/signal computation (bar counting only). Single-shot
panel read.

Run:
  /Users/hoangminhlong/my-quantitative/.venv/bin/python \
    research/control/FUTURES-ES-PB1-V1/repair/exposure_proof_v2.py

Output (write boundary: this directory only):
  exposure_proof_v2.json
"""
import hashlib
import json
import os
import sys
from collections import Counter
from datetime import datetime

import pandas as pd
import pyarrow.parquet as pq

WORKTREE = "/Users/hoangminhlong/my-quantitative/.worktrees/futures-es-reg/prep"
MEASURED_HEAD = "fc9c83621687bffafc8cc71039dee9e4c4c46dae"  # single rev-parse at lane start

REL = {
    "session_dispersion_es": "research/control/FUTURES-K6GATE-PREP-20261004/es/session_dispersion_es.json",
    "panel_parquet": "research/control/FUTURES-DEEPRESEARCH-V2-20261003/analysis/ES_cache/es_1m_outright.parquet",
    "exclude_list_v2": "research/control/FUTURES-ES-PB1-V1/repair/exclude_list_v2.json",
    "v1_exposure_proof": "research/control/FUTURES-ES-PB1-V1/holiday/exposure_proof_2011_2016.json",
    "ES_fomc_stats": "research/control/FUTURES-DEEPRESEARCH-V2-20261003/analysis/ES_fomc_stats.json",
    "es_session_holiday": "research/control/FUTURES-SIX-READINESS-20261004/es/es_session_holiday.json",
    "calendar_close_delta": "research/control/FUTURES-SIX-SCORED-GATE-PREP-20261004/cal_close/calendar_close_delta.json",
    "cmecal_coverage": "research/control/FUTURES-DATACONTRACT-QUAL-V1/analysis/d3_cmecalendar/cmecal_coverage.json",
    "pdf_equity_evidence": "research/control/FUTURES-ES-PB1-V1/holiday/pdf_equity_evidence_2011_2015.json",
}
PINNED_SHA = {
    "session_dispersion_es": "e56c4a53841983e02f5e643e60693581e2c9e096488a1f7491659a71bb7c43a4",
    "panel_parquet": "7ae6de2d5896d9e150f70209f2709ca70b625f0b06bbdbfed348b1b0e0227b95",
    "exclude_list_v2": "67060c8ce5bf2402672c847b20e22842c3f2c14a5951b703ff19061b88ffcbcd",
    "v1_exposure_proof": "8ffc0fa2799e6e516b2cdc44ba08d1cb36dcdd5fbae61e493f0c9a302c42e519",
    "ES_fomc_stats": "228fe2d4efbde95984128b6b1f64a9162bb794ea406c488577036fa09518f213",
    "es_session_holiday": "8885d5de4e7f4c5fbf06c194ea9a6b238e4a5450ac31e7d9807bc97d4ee71391",
    "calendar_close_delta": "626deccc5debad9e8c24dce3a598c3371a937aeb5f792d0ce1f57314a09df8bb",
    "cmecal_coverage": "c82f50c4fa53cf93dfb0b652209007836e4d6ccfe29f3e4535a89f1f2086e157",
    "pdf_equity_evidence": "f3a8b4d43be720966ee8f2978de571e27c4e4ff5d2694dab4d1f4cd116c6bc53",
}
OUT_REL = "research/control/FUTURES-ES-PB1-V1/repair/exposure_proof_v2.json"
SPAN = ("2011-01-01", "2016-12-31")
BAND_LO = 234  # bars >= 234 <=> coverage >= 0.60 exactly (0.6*390=234)
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


# cmecal_coverage.json note-named DAY-LEVEL dates (verbatim quotes; the
# 2011-2015 day level comes from the 53 PDFs instead). Identical to v1.
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

# Volume forensics carried from the v1 proof (committed data, unchanged panel).
CONFLICT_VOLUME_CHECK = {
    "2015-07-02": {"held_symbol": "ESU5",
                   "bars_from_12ct": 619, "volume_sum_from_12ct": 476608,
                   "last_bar_ct": "2015-07-02 23:59:00-05:00",
                   "reading": "real, full-volume trading through the afternoon "
                              "and evening => the v1 conflict was schedule-vs-data, "
                              "not a synthetic-bar artifact; RESOLVED by the repair "
                              "in the conservative direction (session excluded)"},
    "2015-09-04": {"held_symbol": "ESU5",
                   "bars_from_12ct": 240, "volume_sum_from_12ct": 747485,
                   "last_bar_ct": "2015-09-04 16:14:00-05:00",
                   "reading": "regular 16:15 close — agrees with the PDF's "
                              "REGULAR close adjudication; stays INCLUDED"},
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
    exclude = json.load(open(paths["exclude_list_v2"], encoding="utf-8"))
    v1proof = json.load(open(paths["v1_exposure_proof"], encoding="utf-8"))
    fomc = json.load(open(paths["ES_fomc_stats"], encoding="utf-8"))
    pdf_ev = json.load(open(paths["pdf_equity_evidence"], encoding="utf-8"))
    hol = json.load(open(paths["es_session_holiday"], encoding="utf-8"))
    cald = json.load(open(paths["calendar_close_delta"], encoding="utf-8"))

    sessions = k6["sessions"]
    check("k6 session count 4204", len(sessions) == 4204,
          f"n_sessions={k6['n_sessions']} rows={len(sessions)}")
    check("exclude_list_v2 is the repaired freeze at this lane's HEAD",
          exclude["head_sha"] == MEASURED_HEAD
          and exclude["schema"] == "exclude_list@2"
          and exclude["supersedes"]["sha256"] == "bc8a41b673eccb998017e704a9865d139e67438fe984906f7f522782f93b438a",
          f"schema={exclude['schema']} head_sha={exclude['head_sha']} supersedes "
          f"v1 {exclude['supersedes']['sha256'][:8]} (v1 file unmodified)")
    check("v1 proof was the NOT_RUN_BLOCKER record this repair resolves",
          v1proof["verdict"] == "NOT_RUN_BLOCKER"
          and [r["session_date"] for r in v1proof["blocker_rows"]] == ["2015-07-02"],
          f"v1 verdict={v1proof['verdict']}, blocker dates="
          f"{[r['session_date'] for r in v1proof['blocker_rows']]}")

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
    for r in sessions:  # ALL 4204 sessions, matching the freeze builders' law
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
    check("L3 [0.60,1.0) band EMPTY for 2011-2016 (unchanged data)",
          census["0.60<=cov<1.0 (234..389)"] == 0,
          "A7 F-A1 claim re-measured at this HEAD: zero sessions with bars in "
          f"[234,389]; band members={bands['0.60<=cov<1.0 (234..389)']}")

    # ------------------------------------------- L4: candidate enumeration
    pdf_cands = pdf_ev.get("candidate_dates_closed_halt_early", {})
    pdf_regular = pdf_ev.get("regular_adjudicated_dates", {})
    pdf_rule_dates = sorted(d for d in pdf_cands if SPAN[0] <= d <= SPAN[1])
    cand = {}
    for dd in pdf_rule_dates:
        cand[dd] = {"tier": "primary",
                    "rule": "HOLIDAY_PDF_EQUITY_2011_2015 (consumed by the v2 freeze)",
                    "provenance": "official per-holiday Globex schedule PDF "
                                  "(CME Group Equity Products section)",
                    "entries": pdf_cands[dd]["entries"],
                    "truncation_times_ct": pdf_cands[dd].get("truncation_times_ct")}
    for dd, tier, quote, src in CMECAL_NAMED_DAYS:
        if SPAN[0] <= dd <= SPAN[1] and dd not in cand:
            cand[dd] = {"tier": tier, "rule": None, "provenance": src,
                        "quote": quote, "entries": []}
    check("L4a lemma2 truncation times all < 15:00 CT (extractor)",
          pdf_ev.get("lemma2_truncation_times_all_below_1500ct") is True
          and not pdf_ev.get("lemma2_violations"),
          "every committed equity-family HALT/EARLY_CLOSE time named for "
          "2011-2015 is <= 12:15 CT < 15:00 CT (RTH-core end) => any such day "
          "truncates RTH-core and cannot have 390 bars")

    # v2 freeze holiday classes in-span
    excl_span = [e for e in exclude["exclusions"]
                 if SPAN[0] <= e["session_date"] <= SPAN[1]]
    hu_span = [e["session_date"] for e in excl_span if e["reason_class"] == "HOLIDAY_UNCERTAIN"]
    hf_span = [e["session_date"] for e in excl_span if e["reason_class"] == "HOLIDAY_FACT_EARLYCLOSE"]
    hp_span = [e["session_date"] for e in excl_span if e["reason_class"] == "HOLIDAY_PDF_EQUITY_2011_2015"]
    check("L4b v2 HOLIDAY_UNCERTAIN empty in 2011-2016 (unchanged)", not hu_span,
          f"span rows={len(hu_span)} (class spans 2017-2025 only)")
    check("L4c v2 HOLIDAY_FACT_EARLYCLOSE empty in 2011-2016 (unchanged)", not hf_span,
          f"span rows={len(hf_span)} (2010-PDF + 2026-Q5 provenance only)")
    check("L4d v2 HOLIDAY_PDF_EQUITY_2011_2015 covers exactly the 56 in-span PDF candidates",
          sorted(hp_span) == pdf_rule_dates,
          f"class rows in span={len(hp_span)}; PDF candidates in span={len(pdf_rule_dates)}")
    check("L4e the PDF class deliberately covers NO 2016 date (evidence of absence honored)",
          not any(dd.startswith("2016") for dd in hp_span),
          "2016 has no per-holiday PDF set (HOLIDAY_CLOSURE.md M2 evidence of absence); the "
          "2016 fail-closed basis is proven separately by this proof's 2016 sub-epoch section")
    # 2016 committed-evidence boundary assertions
    readiness_years = sorted({w["year"] for w in hol["holiday_deviation_windows_2017_2026"]})
    check("L4f readiness holiday json has NO 2016 window",
          all(y >= 2017 for y in readiness_years),
          f"es_session_holiday.json holiday_deviation_windows years={readiness_years}")
    fact_events = cald["cells_obtained"][1]["values_verbatim_ES_id133_events"]
    fact_dates = sorted({k.split("_")[1][:4] for k in fact_events}
                        | {d[4:8] for v in fact_events.values() for d in v})
    check("L4g cal_close FACT cells are 2026-only",
          all(y == "2026" for y in fact_dates),
          f"calendar_close_delta FACT cell event-date years={sorted(set(fact_dates))} "
          "(no 2016 FACT cell exists)")

    # ------------------------------------------------- exposure evaluation
    excl_class = {e["session_date"]: e["reason_class"] for e in exclude["exclusions"]}
    prio = exclude["reason_class_priority"]
    fomc_dates = {r["date"] for r in fomc["per_event_day_level"]}
    exposure_rows = []
    blocker_rows = []
    resolved_rows = []
    pdf_rule_excluded_rows = []
    full_sessions = []
    partial_sessions = []
    for r in span_rows:
        dd = r["session_date"]
        b = recomputed[dd]
        wd = datetime.strptime(dd, "%Y-%m-%d").date().weekday()
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
                    cls = excl_class.get(dd)
                    if cls is not None and prio.index(cls) <= prio.index("COVERAGE_LT60"):
                        row2["disposition"] = (
                            "EXCLUDED_ADJUDICATED: the v2 freeze excludes this session by "
                            f"{cls}; a primary candidate date may no longer carry an "
                            "eval-eligible session, so no unadjudicated holiday status "
                            "remains (conservative repair law)")
                        row2["volume_forensics"] = CONFLICT_VOLUME_CHECK.get(dd)
                        if cls == "HOLIDAY_PDF_EQUITY_2011_2015":
                            pdf_rule_excluded_rows.append(row2)
                        exposure_rows.append(row2)
                    else:
                        row2["disposition"] = (
                            "BLOCKER_UNRESOLVED_CONFLICT: a committed official "
                            "artifact names this date as an equity-family "
                            "holiday/early-close/halt day, yet the pinned panel "
                            "carries a COMPLETE RTH-core session that the v2 freeze "
                            "does NOT exclude — eval-eligible with unadjudicated "
                            "holiday status. The class STAYS NOT_RUN on this row "
                            "(fail-closed; named blocker).")
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
                        "no unadjudicated holiday status remains; stays INCLUDED")
                    row2["adjudicating_pdf_entries"] = adj
                    resolved_rows.append(row2)
                    exposure_rows.append(row2)
        else:
            partial_sessions.append(row)

    # ============================ (a) 2011-2015 sub-epoch =================
    rows_11_15 = [r for r in span_rows if r["session_date"] <= "2015-12-31"]
    full_11_15 = [r for r in rows_11_15 if recomputed[r["session_date"]] >= BAND_LO]
    blockers_11_15 = [r for r in blocker_rows if r["session_date"] <= "2015-12-31"]
    eval_11_15 = [r["session_date"] for r in full_11_15
                  if r["session_date"] not in excl_class]
    # machine-row verdict: zero 2011-2015 sessions with unadjudicated holiday
    # status inside the evaluation surface = no full session on ANY
    # candidate-named date that is not excluded and not PDF-adjudicated regular.
    unadj_11_15 = blockers_11_15  # primary candidates, complete session, not excluded
    epoch_2011_2015_verdict = "PASS" if not unadj_11_15 else "NOT_RUN_BLOCKER"
    observation("EPOCH 2011-2015 zero unadjudicated-holiday sessions in the eval surface",
                not unadj_11_15,
                f"blocker rows={len(unadj_11_15)} "
                f"dates={[r['session_date'] for r in unadj_11_15]}"
                + ("" if not unadj_11_15 else
                   " — EXPOSURE DISCOVERED: recorded below; verdict = NOT_RUN_BLOCKER"))
    b702 = next((r for r in pdf_rule_excluded_rows if r["session_date"] == "2015-07-02"), None)
    b702_cls = b702["exclude_class"] if b702 is not None else "NOT FOUND in pdf_rule_excluded_rows"
    observation("EPOCH 2011-2015 the 2015-07-02 v1 blocker row is GONE (now excluded)",
                b702 is not None and b702["exclude_class"] == "HOLIDAY_PDF_EQUITY_2011_2015",
                f"2015-07-02 v2 class={b702_cls} (v1: eval-eligible NOT_RUN_BLOCKER); panel "
                f"unchanged (390 bars, coverage 1.0, held ESU5) — evidence-vs-data conflict "
                f"resolved in the conservative direction by owner HOLIDAY-REPAIR-AUTH")

    # ============================ (b) 2016 sub-epoch ======================
    rows_2016 = [r for r in span_rows if r["session_date"].startswith("2016")]
    cand_2016 = sorted(dd for dd in cand if dd.startswith("2016"))
    full_2016 = [r for r in rows_2016 if recomputed[r["session_date"]] >= BAND_LO]
    partial_2016 = [r for r in rows_2016 if recomputed[r["session_date"]] < BAND_LO]
    absent_2016 = [dd for dd in cand_2016
                   if dd not in {r["session_date"] for r in rows_2016}]
    # machine-row ambiguity test: a COMPLETE session on ANY candidate-named 2016
    # date that the v2 freeze does not exclude would be ambiguous => class stays
    # NOT_RUN with that named blocker. No 2016 date may be silently resolved.
    ambiguous_2016 = []
    rows_2016_detail = []
    for r in rows_2016:
        dd = r["session_date"]
        b = recomputed[dd]
        cls = excl_class.get(dd, "NOT_EXCLUDED_SURVIVOR")
        is_cand = dd in cand_2016
        rows_2016_detail.append({
            "session_date": dd, "bars_rth_core": b,
            "coverage_recomputed": round(b / 390, 4),
            "exclude_class": cls, "is_candidate_date": is_cand,
            "candidate_provenance": cand.get(dd, {}).get("provenance") if is_cand else None,
            "candidate_tier": cand.get(dd, {}).get("tier") if is_cand else None})
        if is_cand and b >= BAND_LO and cls == "NOT_EXCLUDED_SURVIVOR":
            ambiguous_2016.append(rows_2016_detail[-1])
    epoch_2016_verdict = ("FAIL_CLOSED_BASIS_PROVEN" if not ambiguous_2016
                          else "NOT_RUN_BLOCKER")
    observation("EPOCH 2016 zero ambiguous sessions (fail-closed basis PROVEN from machine rows)"
                if not ambiguous_2016 else
                "EPOCH 2016 ambiguous sessions EXIST — class stays NOT_RUN (named blocker)",
                not ambiguous_2016,
                f"2016 in-panel sessions={len(rows_2016)} "
                f"(full {len(full_2016)} / partial {len(partial_2016)}); "
                f"candidate-named 2016 dates={cand_2016}; "
                f"candidate dates absent from panel={absent_2016}; "
                f"candidate-named sessions all truncated(<234)+COVERAGE-excluded or absent; "
                f"ambiguous rows={len(ambiguous_2016)} "
                f"dates={[r['session_date'] for r in ambiguous_2016]}"
                + ("" if not ambiguous_2016 else
                   " — the HOLIDAY_PDF_EQUITY_2011_2015 class does NOT cover 2016 and the "
                   "2016 enumeration STAYS NOT_RUN with this named blocker"))
    # every full 2016 session sits on a date named as holiday by NO committed artifact
    unnamed_full_2016 = [r["session_date"] for r in full_2016
                         if r["session_date"] not in cand_2016]

    # ---- overall verdict FROM THE MACHINE ROWS (never from expectations) ----
    overall_blockers = blocker_rows  # both epochs
    verdict = "PASS" if not overall_blockers else "NOT_RUN_BLOCKER"

    cls_counter = Counter(r["exclude_class"] for r in full_sessions)
    eval_eligible = [r["session_date"] for r in full_sessions
                     if r["exclude_class"] == "NOT_EXCLUDED_SURVIVOR"]
    prio_all_ok = all(r["exclude_class"] in prio and
                      prio.index(r["exclude_class"]) <= prio.index("COVERAGE_LT60")
                      for r in partial_sessions)
    check("L5 partial-session exclude classes all COVERAGE_LT60 or higher priority (v2 enum)",
          prio_all_ok,
          str(Counter(r["exclude_class"] for r in partial_sessions)))

    out = {
        "schema": "exposure_proof_v2@1",
        "cycle_id": "FUTURES-ES-PB1-V1",
        "lane": "BUILDER-REPAIR (M2)",
        "generated_utc": "2026-10-05",
        "measured_head": MEASURED_HEAD,
        "supersedes": {"artifact": "research/control/FUTURES-ES-PB1-V1/holiday/exposure_proof_2011_2016.json",
                       "sha256": PINNED_SHA["v1_exposure_proof"],
                       "v1_verdict": v1proof["verdict"],
                       "v1_blocker_dates": [r["session_date"] for r in v1proof["blocker_rows"]]},
        "owner_authority": {"record": "research/control/FUTURES-ES-PB1-V1/auth/PREGO_REPAIR_RECORDED.json",
                            "decision_id": "HOLIDAY-REPAIR-AUTH",
                            "law": "the verdict below comes from the machine rows; expected "
                                   "outcomes were never used as evidence"},
        "statement_tested": "no in-panel 2011-01-01..2016-12-31 session can enter "
                            "the evaluation surface while its holiday status is unadjudicated",
        "verdict": verdict,
        "verdict_basis": ("ZERO blocker rows across both sub-epochs at the v2 freeze — "
                          "obligation CLOSED by machine proof"
                          if not overall_blockers else
                          "blocker rows EXIST at the v2 freeze: "
                          + ", ".join(r["session_date"] for r in overall_blockers)
                          + " — NOT_RUN until resolved"),
        "epoch_2011_2015": {
            "verdict": epoch_2011_2015_verdict,
            "basis": ("zero sessions with unadjudicated holiday status inside the evaluation "
                      "surface: every in-panel session on a 53-PDF primary-tier candidate date "
                      "is EXCLUDED by HOLIDAY_PDF_EQUITY_2011_2015 (or a higher-priority class); "
                      "the v1 blocker 2015-07-02 row is GONE; 2015-09-04 stays INCLUDED "
                      "(PDF-adjudicated REGULAR_CLOSE, panel agrees)"
                      if epoch_2011_2015_verdict == "PASS" else
                      "unadjudicated rows exist: " + ", ".join(r["session_date"] for r in unadj_11_15)),
            "n_sessions": len(rows_11_15),
            "n_full_sessions_bars_ge_234": len(full_11_15),
            "n_eval_eligible_full_sessions": len(eval_11_15),
            "eval_eligible_first": min(eval_11_15) if eval_11_15 else None,
            "eval_eligible_last": max(eval_11_15) if eval_11_15 else None,
            "n_blocker_rows": len(unadj_11_15),
            "blocker_dates": [r["session_date"] for r in unadj_11_15],
            "n_pdf_rule_excluded_candidate_sessions": len(pdf_rule_excluded_rows),
            "pdf_rule_excluded_candidate_dates": [r["session_date"] for r in pdf_rule_excluded_rows],
            "resolved_regular_dates": [r["session_date"] for r in resolved_rows],
        },
        "epoch_2016": {
            "verdict": epoch_2016_verdict,
            "basis": ("zero ambiguous 2016 sessions EXIST (machine rows): every candidate-named "
                      "2016 session is truncated (<234 bars) and COVERAGE_LT60-excluded or absent "
                      "from the panel; every complete 2016 session sits on a date named as "
                      "holiday/early-close by NO committed 2016 artifact; the enumeration "
                      "REMAINS NOT_RUN (no per-day 2016 list is claimed) and the "
                      "HOLIDAY_PDF_EQUITY_2011_2015 class deliberately does NOT cover 2016"
                      if epoch_2016_verdict == "FAIL_CLOSED_BASIS_PROVEN" else
                      "ambiguous 2016 rows exist — class stays NOT_RUN with named blocker(s): "
                      + ", ".join(r["session_date"] for r in ambiguous_2016)),
            "enumeration_status": "NOT_RUN (unchanged; evidence of absence for any 2016 per-day "
                                  "PDF set recorded in holiday/HOLIDAY_CLOSURE.md M2)",
            "n_sessions": len(rows_2016),
            "n_full_sessions_bars_ge_234": len(full_2016),
            "n_partial_sessions_bars_lt_234": len(partial_2016),
            "candidate_named_dates_committed_2016_evidence": cand_2016,
            "candidate_dates_absent_from_panel": absent_2016,
            "candidate_named_dates_absent_named_by_no_artifact_full_sessions": unnamed_full_2016,
            "n_ambiguous_rows": len(ambiguous_2016),
            "ambiguous_rows": ambiguous_2016,
            "named_blocker_if_any": [r["session_date"] for r in ambiguous_2016],
            "sessions": rows_2016_detail,
            "committed_2016_evidence_sources": {
                "cmecal_year_2016_note": {
                    "file": REL["cmecal_coverage"], "sha256": shas["cmecal_coverage"],
                    "dates": [{"date": dd, "tier": t, "quote": q, "source": s}
                              for dd, t, q, s in CMECAL_NAMED_DAYS if dd.startswith("2016")]},
                "readiness_holiday_json": {
                    "file": REL["es_session_holiday"], "sha256": shas["es_session_holiday"],
                    "fact": "holiday_deviation_windows years " + str(readiness_years)
                            + " — NO 2016 window exists"},
                "cal_close_fact_cells": {
                    "file": REL["calendar_close_delta"], "sha256": shas["calendar_close_delta"],
                    "fact": "FACT-grade cells are 2026-only (MLK/GoodFriday/July-4 2026); "
                            "no 2016 FACT cell exists"},
            },
        },
        "band_census_2011_2016": census,
        "n_sessions_span": len(span_rows),
        "n_full_sessions_bars_ge_234": len(full_sessions),
        "full_session_disposition": dict(cls_counter),
        "n_eval_eligible_full_sessions": len(eval_eligible),
        "n_partial_sessions_bars_lt_234": len(partial_sessions),
        "n_exposure_rows_mission_literal": len(exposure_rows),
        "exposure_rows": exposure_rows,
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
            "n_pdf_rule_dates_in_span": len(pdf_rule_dates),
            "sources": {
                "pdf_2011_2015": {
                    "file": REL["pdf_equity_evidence"], "sha256": shas["pdf_equity_evidence"],
                    "n_dates": len(pdf_rule_dates),
                    "consumed_by": "HOLIDAY_PDF_EQUITY_2011_2015 in repair/exclude_list_v2.json"},
                "cmecal_note_named_days_2014_2016": {
                    "file": REL["cmecal_coverage"], "sha256": shas["cmecal_coverage"],
                    "dates": [{"date": x[0], "tier": x[1]} for x in CMECAL_NAMED_DAYS]},
            },
        },
        "v1_to_v2_blocker_resolution": {
            "v1": {"verdict": v1proof["verdict"],
                   "blocker": "2015-07-02 (390-bar real-volume session, eval-eligible, "
                              "official schedule names 12:15 CT early close)"},
            "v2": {"disposition": b702["disposition"] if b702 else None,
                   "exclude_class": b702["exclude_class"] if b702 else None,
                   "law": "owner HOLIDAY-REPAIR-AUTH: conservative direction — exclude the "
                          "session, never upgrade it on an evidence-vs-data conflict"},
        },
        "data_version_binding": {
            "panel_parquet": {"path": REL["panel_parquet"], "sha256": shas["panel_parquet"]},
            "session_universe": {"path": REL["session_dispersion_es"], "sha256": shas["session_dispersion_es"]},
            "exclude_list_v2": {"path": REL["exclude_list_v2"], "sha256": shas["exclude_list_v2"],
                                "head_sha_at_generation": exclude["head_sha"]},
            "pdf_equity_evidence": {"path": REL["pdf_equity_evidence"], "sha256": shas["pdf_equity_evidence"]},
            "law": "this proof is valid ONLY for the panel + v2 freeze at the shas above; "
                   "any data refresh or builder change re-runs this proof and re-opens the "
                   "obligation automatically on any FAIL",
        },
        "checks": checks,
    }
    path = os.path.join(WORKTREE, OUT_REL)
    with open(path, "w", encoding="utf-8") as f:
        f.write(json.dumps(out, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "out": OUT_REL,
        "verdict": out["verdict"],
        "epoch_2011_2015": epoch_2011_2015_verdict,
        "epoch_2016": epoch_2016_verdict,
        "blocker_dates": [r["session_date"] for r in blocker_rows],
        "ambiguous_2016_dates": [r["session_date"] for r in ambiguous_2016],
        "pdf_rule_excluded_dates_n": len(pdf_rule_excluded_rows),
        "resolved_regular_dates": [r["session_date"] for r in resolved_rows],
        "band_census": census,
        "n_candidates": len(cand),
        "n_full": len(full_sessions),
        "n_partial": len(partial_sessions),
        "eval_eligible_full": len(eval_eligible),
        "checks_passed": sum(1 for c in checks if c["verdict"] == "PASS"),
        "checks_total": len(checks),
    }, indent=2))


if __name__ == "__main__":
    main()
