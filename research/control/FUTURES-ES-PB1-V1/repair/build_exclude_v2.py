#!/usr/bin/env python
"""FUTURES-ES-PB1-V1 gate 2 REPAIR — conservative exclude list v2 + diff + selection freeze v2.

Owner authority: auth/PREGO_REPAIR_RECORDED.json decision HOLIDAY-REPAIR-AUTH
("okay lên lệnh cho agent trong zcode đi", following the conservative holiday
repair proposal) + PINS-D-A1-A2-A3 ("Đồng ý cả ba cách trên").

STARTS from the exact frozen v1 logic (freezegen/build_exclude_and_freeze.py,
sha 9b94372d5bd297f5d50ac5107fcb1c34dcee9c090f4d10eaf38f97d387116e69) and adds
exactly ONE new rule class:

  HOLIDAY_PDF_EQUITY_2011_2015 — every in-panel session whose date is a
  primary-tier candidate (CLOSED / HALT / EARLY_CLOSE) of the committed
  53-PDF extraction holiday/pdf_equity_evidence_2011_2015.json AND is NOT
  PDF-adjudicated regular. Fail-closed: PDF-absent dates keep their current
  classes; PDF-adjudicated REGULAR dates (e.g. 2015-09-04) are never touched
  by this class; 2016 (no PDF set; evidence of absence recorded) is NOT
  covered and stays NOT_RUN — never silently resolved.

Everything else is preserved verbatim from v1: FOMC_STATEMENT_DAY,
HOLIDAY_FACT_EARLYCLOSE (2010+2026), HOLIDAY_UNCERTAIN (2017-2025),
COVERAGE_LT60 (rule + independent panel recompute), WARMUP (252/fold).

Evidence-driven, outcome-blind: no quarantined PnL read or used; raw panel
read-only (single-shot); the ORIGINAL gate-2 artifacts (freezegen/**) are
HISTORY and are never modified — the repaired freeze lives in repair/ as
append-only supersession (same pattern as freeze_pins v1->v2).

Run:
  /Users/hoangminhlong/my-quantitative/.venv/bin/python \
    research/control/FUTURES-ES-PB1-V1/repair/build_exclude_v2.py

Outputs (write boundary: this directory only):
  exclude_list_v2.json
  freeze_diff.json
  selection_freeze_v2.json
"""
import hashlib
import json
import os
import sys

import pandas as pd
import pyarrow.parquet as pq

WORKTREE = "/Users/hoangminhlong/my-quantitative/.worktrees/futures-es-reg/prep"
ROOT_REPO_PLANS = "/Users/hoangminhlong/my-quantitative/plans"
HEAD_SHA = "fc9c83621687bffafc8cc71039dee9e4c4c46dae"
CYCLE_ID = "FUTURES-ES-PB1-V1"
GENERATED_UTC = "2026-10-05"
WARMUP_SESSIONS = 252
FOLD_WINDOWS = [
    ("F1", "2010-06-01", "2012-12-31"),
    ("F2", "2013-01-01", "2017-12-31"),
    ("F3", "2018-01-01", "2021-12-31"),
    ("F4", "2022-01-01", "2026-09-30"),
]
# v1 priority preserved; the new PDF class slots between the FACT class and
# the UNCERTAIN (fail-closed-pending) class. The exclude SET is the union
# either way; the label follows first-in-priority.
PRIORITY = [
    "FOMC_STATEMENT_DAY",
    "HOLIDAY_FACT_EARLYCLOSE",
    "HOLIDAY_PDF_EQUITY_2011_2015",
    "HOLIDAY_UNCERTAIN",
    "COVERAGE_LT60",
    "WARMUP",
]

# (key, relative path, expected sha256 or None-to-record)
INPUTS = {
    "SPEC": ("research/control/FUTURES-ES-V1-PACKET/SPEC_PB1_ES.md",
             "445f749906481f33080185cab1628e6365ef2f6db3b9c4f9f0847646eb6b7073"),
    "PLAN_REGISTERED": ("/Users/hoangminhlong/my-quantitative/plans/PLAN_futures_es_pb1_v1.md",
                        None),  # ROOT repo, read-only authority side (absolute path)
    "identity_table_24": ("research/control/FUTURES-ES-PB1-REGPREP-20261004/freeze/identity_table_24.json",
                          "6e3919808ecea86d147ba67d8e5df4f4e83bed2414973f87de051054da6e471f"),
    "freeze_pins_v2": ("research/control/FUTURES-ES-PB1-REGPREP-20261004/freeze/freeze_pins_v2.json",
                       "f7e1b580071c09526f13915523a287094ed56a530d2196adc4de0c85907b469a"),
    "pit_exclude_set": ("research/control/FUTURES-ES-PB1-REGPREP-20261004/freeze/pit_exclude_set.json",
                        "f504c7319f235f75449e5b5707014c74a37ea9bf1e558e32be59c36fada8d2f6"),
    "D3_RECORDED": ("research/control/FUTURES-ES-PB1-REGPREP-20261004/auth/D3_RECORDED.json",
                    "f54610eb15e6cb41d32dec28616cdaaed6225fce0cfee9fe4cc3522b2fa1e355"),
    "ES_fomc_stats": ("research/control/FUTURES-DEEPRESEARCH-V2-20261003/analysis/ES_fomc_stats.json",
                      "228fe2d4efbde95984128b6b1f64a9162bb794ea406c488577036fa09518f213"),
    "r3_fomc": ("research/control/FUTURES-DEEPRESEARCH-V2-20261003/audit/a7_es/r3_fomc.json",
                "ba57bc3325559b7f57a3757c63c8b93e6a900d54592eebcd098d940acc4e34f3"),
    "session_dispersion_es": ("research/control/FUTURES-K6GATE-PREP-20261004/es/session_dispersion_es.json",
                              "e56c4a53841983e02f5e643e60693581e2c9e096488a1f7491659a71bb7c43a4"),
    "SYNTHESIS_K6": ("research/control/FUTURES-K6GATE-PREP-20261004/synth/SYNTHESIS_K6.md",
                     "03a8e77e2120f60c7a6d70802688c7f81dadf692e01e3c3d322575ff90de8237"),
    "es_session_holiday": ("research/control/FUTURES-SIX-READINESS-20261004/es/es_session_holiday.json",
                           "8885d5de4e7f4c5fbf06c194ea9a6b238e4a5450ac31e7d9807bc97d4ee71391"),
    "calendar_close_delta": ("research/control/FUTURES-SIX-SCORED-GATE-PREP-20261004/cal_close/calendar_close_delta.json",
                             "626deccc5debad9e8c24dce3a598c3371a937aeb5f792d0ce1f57314a09df8bb"),
    "es_o1m_roll_recheck": ("research/control/FUTURES-SIX-READINESS-20261004/es/es_o1m_roll_recheck.json",
                            "e7ab27ea2bfaab16009422bf7588d17e759f7e2652bf90f30c5ad4d9c5f1a66d"),
    "es_expiry_recheck": ("research/control/FUTURES-SIX-READINESS-20261004/es/es_expiry_recheck.json",
                          "2b065d5b94540e2740791ba33560d590be460b5866d9ede037a8a9db934fa94b"),
    "es_1m_outright_parquet": ("research/control/FUTURES-DEEPRESEARCH-V2-20261003/analysis/ES_cache/es_1m_outright.parquet",
                               "7ae6de2d5896d9e150f70209f2709ca70b625f0b06bbdbfed348b1b0e0227b95"),
    "cmecal_coverage": ("research/control/FUTURES-DATACONTRACT-QUAL-V1/analysis/d3_cmecalendar/cmecal_coverage.json",
                        "c82f50c4fa53cf93dfb0b652209007836e4d6ccfe29f3e4535a89f1f2086e157"),
    # ---- repair-wave inputs (new vs v1) ----
    "pdf_equity_evidence": ("research/control/FUTURES-ES-PB1-V1/holiday/pdf_equity_evidence_2011_2015.json",
                            "f3a8b4d43be720966ee8f2978de571e27c4e4ff5d2694dab4d1f4cd116c6bc53"),
    "PREGO_REPAIR_RECORDED": ("research/control/FUTURES-ES-PB1-V1/auth/PREGO_REPAIR_RECORDED.json",
                              "db0360faa1d2a70f9ace9e439082ebf94a058c05e0da53f7e5e10c0ba85d82bf"),
    "pin_decisions": ("research/control/FUTURES-ES-PB1-V1/pins/pin_decisions.json",
                      "ef267c3a9b91935c42ecbf30fabfbe19e0624a2acb1ec71a4402b559fee42c5a"),
    # v1 freeze artifacts = HISTORY baseline (read-only, never modified)
    "v1_exclude_list": ("research/control/FUTURES-ES-PB1-V1/freezegen/exclude_list.json",
                        "bc8a41b673eccb998017e704a9865d139e67438fe984906f7f522782f93b438a"),
    "v1_selection_freeze": ("research/control/FUTURES-ES-PB1-V1/freezegen/selection_freeze.json",
                            "e2b9934af01127ee698adda2fa0579d519f54881958e07463157728a8b96c1b7"),
}

FREEZEGEN_DIR = "research/control/FUTURES-ES-PB1-V1/freezegen"  # HISTORY, read-only
REPAIR_DIR = "research/control/FUTURES-ES-PB1-V1/repair"

tests = []


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def record_test(command, ok, detail):
    tests.append({"command": command, "exit_code": 0 if ok else 1,
                  "verdict": "PASS" if ok else "FAIL", "result": detail})
    if not ok:
        print("FATAL:", detail)
        sys.exit(1)


def canon(obj):
    return json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def write_json(relpath, obj):
    path = os.path.join(WORKTREE, relpath)
    with open(path, "w", encoding="utf-8") as f:
        f.write(canon(obj))
    return sha256_file(path)


def fold_of(date_str):
    for fid, lo, hi in FOLD_WINDOWS:
        if lo <= date_str <= hi:
            return fid
    return None


def main():
    shas = {}
    for key, (rel_or_abs, expected) in INPUTS.items():
        if rel_or_abs.startswith("/"):
            path = rel_or_abs
            rel = rel_or_abs
        else:
            path = os.path.join(WORKTREE, rel_or_abs)
            rel = rel_or_abs
        if not os.path.exists(path):
            record_test(f"sha256 {key}", False, f"input missing: {path}")
        h = sha256_file(path)
        if expected is not None:
            record_test(f"sha256 {key}", h == expected,
                        f"{key}: expected {expected} == measured {h}")
        shas[key] = {"path": rel, "sha256": h,
                     "pin_match": (None if expected is None else h == expected)}

    load = lambda key: json.load(open(os.path.join(WORKTREE, INPUTS[key][0]), encoding="utf-8"))
    spec_txt = open(os.path.join(WORKTREE, INPUTS["SPEC"][0]), encoding="utf-8").read()
    plan_txt = open(os.path.join(ROOT_REPO_PLANS, "PLAN_futures_es_pb1_v1.md"), encoding="utf-8").read()

    identity = load("identity_table_24")
    pins = load("freeze_pins_v2")
    pit = load("pit_exclude_set")
    d3 = load("D3_RECORDED")
    fomc = load("ES_fomc_stats")
    k6 = load("session_dispersion_es")
    hol = load("es_session_holiday")
    cald = load("calendar_close_delta")
    cmecal = load("cmecal_coverage")
    pdf_ev = load("pdf_equity_evidence")
    prego = load("PREGO_REPAIR_RECORDED")
    pin_dec = load("pin_decisions")
    v1_exclude = load("v1_exclude_list")
    v1_selection = load("v1_selection_freeze")

    record_test("identity count 24",
                len(identity["identities"]) == 24 and identity["reconciliation"]["count_match"] is True,
                f"identity_table_24: {len(identity['identities'])} identities, reconciliation.count_match="
                f"{identity['reconciliation']['count_match']}")
    record_test("pins manifest 34 (base manifest unchanged)", pins["pin_count"] == 34,
                f"freeze_pins_v2.pin_count={pins['pin_count']}")
    # owner repair authority
    repair_auth = next(d for d in prego["decisions"] if d["id"] == "HOLIDAY-REPAIR-AUTH")
    pins_auth = next(d for d in prego["decisions"] if d["id"] == "PINS-D-A1-A2-A3")
    record_test("PREGO repair authority present",
                repair_auth["decision_quote_verbatim"] == "okay lên lệnh cho agent trong zcode đi"
                and pins_auth["decision_quote_verbatim"] == "Đồng ý cả ba cách trên",
                "auth/PREGO_REPAIR_RECORDED.json carries HOLIDAY-REPAIR-AUTH ('okay lên lệnh cho agent "
                "trong zcode đi') + PINS-D-A1-A2-A3 ('Đồng ý cả ba cách trên'); not_a_go_law honored "
                "(no typed GO consumed)")

    # ---------------------------------------------------------------- sessions
    sessions = k6["sessions"]
    by_date = {r["session_date"]: r for r in sessions}
    dates_sorted = sorted(by_date)
    record_test("k6 session count 4204", len(sessions) == 4204,
                f"session_dispersion_es n_sessions={k6['n_sessions']}, rows={len(sessions)}")

    # COVERAGE_LT60: apply the SPEC §3 [M4] rule to committed per-session rows.
    cov_rule = sorted(r["session_date"] for r in sessions if r["rth_core_coverage"] < 0.6)
    cov_file = sorted(k6["excluded_dates"])
    record_test("coverage rule == excluded_dates", cov_rule == cov_file,
                f"rth_core_coverage<0.6 gives {len(cov_rule)} dates; excluded_dates has "
                f"{len(cov_file)}; equal={cov_rule == cov_file}")
    below = [r["rth_core_coverage"] for r in sessions if r["rth_core_coverage"] < 0.6]
    above = [r["rth_core_coverage"] for r in sessions if r["rth_core_coverage"] >= 0.6]
    margin = {"max_coverage_below_0.60": max(below), "min_coverage_at_or_above_0.60": min(above)}

    # Panel recompute (single-shot read): bars with raw_symbol==held_symbol and
    # bar-start 08:30..14:59 CT on the session date, per session_dispersion_es.json
    # rth_core_window_ct convention ("08:30-15:00 (bar starts 08:30..14:59)").
    panel_rel = INPUTS["es_1m_outright_parquet"][0]
    pq_meta = pq.ParquetFile(os.path.join(WORKTREE, panel_rel)).metadata
    tbl = pq.read_table(os.path.join(WORKTREE, panel_rel),
                        columns=["raw_symbol", "ts_event"])
    ts = pd.to_datetime(tbl["ts_event"].to_pylist(), unit="ns", utc=True)
    df = pd.DataFrame({"raw_symbol": tbl["raw_symbol"].to_pylist(), "ts": ts})
    df["ct"] = df["ts"].dt.tz_convert("America/Chicago")
    df["d"] = df["ct"].dt.strftime("%Y-%m-%d")
    df["t"] = df["ct"].dt.hour * 60 + df["ct"].dt.minute
    win = df[(df["t"] >= 8 * 60 + 30) & (df["t"] < 15 * 60)]
    counts = win.groupby(["raw_symbol", "d"]).size()
    mism, recomputed = [], {}
    for r in sessions:
        n = int(counts.get((r["held_symbol"], r["session_date"]), 0))
        recomputed[r["session_date"]] = n
        if n != r["bars_rth_core_held"]:
            mism.append((r["session_date"], r["held_symbol"], n, r["bars_rth_core_held"]))
    record_test("panel recompute bars_rth_core_held 4204/4204", not mism,
                f"single-shot parquet read ({pq_meta.num_rows} rows): recomputed RTH-core held bars "
                f"match session_dispersion_es.sessions[].bars_rth_core_held for all {len(sessions)} "
                f"sessions; mismatches={mism[:5]}")
    excl_by_cov = sorted(d for d in cov_rule if recomputed[d] / 390.0 < 0.6)
    record_test("panel-recomputed coverage == K6 flag", excl_by_cov == cov_rule,
                f"recomputed bars/390 < 0.6 reproduces the same {len(cov_rule)} dates")

    # ------------------------------------------------------------------ FOMC
    fomc_rows = fomc["per_event_day_level"]
    fomc_dates = [r["date"] for r in fomc_rows]
    record_test("FOMC 131 in-data day rows",
                len(fomc_dates) == 131 and fomc["n_in_data"] == 131 and fomc["n_statements_total"] == 132,
                f"n_statements_total={fomc['n_statements_total']}, n_in_data={fomc['n_in_data']}, "
                f"per_event_day_level rows={len(fomc_rows)}")
    fomc_missing_panel = [d for d in fomc_dates if d not in by_date]
    record_test("FOMC dates all panel sessions", not fomc_missing_panel,
                f"131/131 FOMC dates are panel sessions; not-in-panel={fomc_missing_panel}")
    record_test("132nd statement (Sunday) not a session",
                "2020-03-15" not in fomc_dates and "2020-03-15" not in by_date,
                "2020-03-15 (release_time_note irregular list, '17:00 Sun') is absent from "
                "per_event_day_level and from the panel session universe (Sunday; panel has 0 "
                "Saturday/Sunday RTH sessions per es_o1m_roll_recheck.json)")

    # --------------------------------------------------------------- holidays
    # FACT/Q5-verified (proven ES-specific status): 2010 PDF + 2026 Q5 grid.
    y2010 = hol["year_2010_product_level_reference"]["holiday_dates_for_legality"]
    span = (dates_sorted[0], dates_sorted[-1])
    fact_2026 = hol["holiday_deviation_windows_2017_2026"][-1]["holiday_dates_for_legality"]
    fact_windows = cald["cells_obtained"][1]["cell"]  # FACT upgrade x3 windows
    provenance_2026 = {
        "2026-01-19": "FACT_GRADE_CAL_CLOSE (MLK window)",
        "2026-04-03": "FACT_GRADE_CAL_CLOSE (Good Friday window)",
        "2026-07-03": "FACT_GRADE_CAL_CLOSE (July-4 window)",
    }
    holiday_fact_entries = []
    for d in y2010:
        holiday_fact_entries.append((d, "2010",
            "2010 official 38-page Globex holiday calendar PDF (E1-(ii) per-day/per-time proof source); "
            "verbatim detail in es_session_holiday.json year_2010_product_level_reference"))
    for d in fact_2026:
        prov = provenance_2026.get(d, "Q5_VERIFIED_OBTAINED (2026 weekly template + 11 deviation "
                                        "windows, 23 dated cells, independently verified Q5 chain)")
        holiday_fact_entries.append((d, "2026",
            f"{prov}; cell family: {fact_windows}"))
    # HOLIDAY_UNCERTAIN (window-level only; ES-specific times NOT_TRANSCRIBED): 2017-2025.
    uncertain_years = {}
    for w in hol["holiday_deviation_windows_2017_2026"]:
        y = w["year"]
        if y == 2026:
            continue
        assert "NOT_TRANSCRIBED" in w["es_product_globex_times"], y
        uncertain_years[y] = w["holiday_dates_for_legality"]
    record_test("HOLIDAY_UNCERTAIN emits 2017-2025 only (unchanged from v1)",
                all(str(y) not in {str(yy) for yy in uncertain_years} for y in range(2011, 2017)),
                "es_session_holiday.json holiday_deviation_windows start at 2017; the "
                "fail-closed-pending class is unchanged and still emits 2017-2025 only. "
                "2011-2015 day-level candidates are now carried by the NEW class "
                "HOLIDAY_PDF_EQUITY_2011_2015 (53-PDF extraction); 2016 stays NOT_RUN "
                "(no per-day PDF set exists — evidence of absence recorded in "
                "holiday/HOLIDAY_CLOSURE.md M2); 2016 is NOT silently resolved by this repair.")

    # ------------------------------------------------- NEW RULE: PDF evidence
    pdf_cands = pdf_ev["candidate_dates_closed_halt_early"]
    pdf_regular = pdf_ev["regular_adjudicated_dates"]
    record_test("PDF evidence schema + corpus",
                pdf_ev["schema"] == "pdf_equity_evidence_2011_2015@1"
                and pdf_ev["n_files"] == 53 and len(pdf_ev["files"]) == 53,
                f"53 committed per-holiday CME Globex schedule PDFs 2011-2015; "
                f"equity sections found {pdf_ev['n_equity_sections_found']}/53; "
                f"lemma2 truncation times all < 15:00 CT = "
                f"{pdf_ev['lemma2_truncation_times_all_below_1500ct']}")
    # candidates and regular-adjudicated sets must be disjoint
    regular_nonempty = {k for k, v in pdf_regular.items() if v}
    overlap_cand_reg = sorted(set(pdf_cands) & regular_nonempty)
    record_test("PDF candidate set disjoint from PDF regular-adjudicated set",
                not overlap_cand_reg,
                f"{len(pdf_cands)} CLOSED/HALT/EARLY_CLOSE candidates vs {len(regular_nonempty)} "
                f"adjudicated-regular dates; overlap={overlap_cand_reg}")
    # 2015-09-04: adjudicated REGULAR by PDF; never a candidate; stays INCLUDED.
    r904 = pdf_regular.get("2015-09-04")
    record_test("2015-09-04 PDF-adjudicated REGULAR_CLOSE and not a candidate -> stays INCLUDED",
                r904 is not None and r904[0]["classification"] == "REGULAR_CLOSE"
                and "2015-09-04" not in pdf_cands,
                "2015-labor-day-holiday-schedule.pdf equity section: 'Friday, Sep 4' "
                "1615 CT - Regular close (sha " + r904[0]["sha256"] + "); the settlement-notice "
                "naming (cmecal_coverage year-2015 note) is contradicted on the session side; "
                "the HOLIDAY_PDF_EQUITY_2011_2015 rule never touches PDF-adjudicated regular dates")
    # 2016 evidence of absence honored: the PDF set carries no 2016 dates.
    pdf_years = sorted({d[:4] for d in list(pdf_cands) + list(regular_nonempty)})
    record_test("PDF set is 2011-2015 only; 2016 has no day-level PDF set (NOT resolved)",
                pdf_years == ["2010", "2011", "2012", "2013", "2014", "2015"]
                and not any(k.startswith("2016") for k in pdf_cands),
                f"candidate+regular date years={pdf_years}; 2016 absence evidence: "
                "HOLIDAY_CLOSURE.md M2 (globex-holiday-calendar.pdf naming family ends 2010; "
                "eq-gapfill 2011 404 probe + CDX inventory captures/cdx_holiday_files.txt); "
                "2016 fail-closed basis is re-proven separately by repair/exposure_proof_v2.json (M2)")
    # verbatim quote lookup from the extractor's per-file statements
    stmt_by_date = {}
    for f in pdf_ev["files"]:
        for s in f.get("statements", []):
            stmt_by_date.setdefault(s["date"], []).append(
                {"file": f["file"], "sha256": f["sha256"],
                 "classification": s["classification"], "time_ct": s.get("time_ct"),
                 "verbatim": s["verbatim"]})

    # ------------------------------------------------------------- exclusions
    def base_evidence(key):
        return {"file": INPUTS[key][0], "sha256": shas[key]["sha256"]}

    prio_idx = {c: i for i, c in enumerate(PRIORITY)}
    assign = {}  # date -> (class, evidence)

    for d in fomc_dates:
        row = next(r for r in fomc_rows if r["date"] == d)
        assign[d] = ("FOMC_STATEMENT_DAY", {
            **base_evidence("ES_fomc_stats"),
            "field": "per_event_day_level[].date",
            "law": "SPEC_PB1_ES §3 [ERRATUM A7-SPEC-M3]: every FOMC statement day is base-EXCLUDED "
                   "at day level (132 statements 2011-2026; day-level public dates, time-safe)",
            "statement_timed": bool(row["timed"])})
    for d, yr, prov in holiday_fact_entries:
        ev = {**base_evidence("es_session_holiday"),
              "field": f"holiday_dates_for_legality[{yr}]",
              "provenance_class": prov}
        if yr == "2026" and prov.startswith("FACT_GRADE"):
            ev["corroborating_file"] = INPUTS["calendar_close_delta"][0]
            ev["corroborating_sha256"] = shas["calendar_close_delta"]["sha256"]
        assign.setdefault(d, ("HOLIDAY_FACT_EARLYCLOSE", ev))
    # NEW (PREGO HOLIDAY-REPAIR-AUTH): primary-tier PDF candidates 2011-2015.
    # Assigned for EVERY candidate date in the chain span (session or not), so the
    # law-date register records the full PDF-named set; only in-panel sessions can
    # change the eval surface. PDF-adjudicated REGULAR dates are never assigned.
    pdf_rule_dates = sorted(d for d in pdf_cands if span[0] <= d <= span[1])
    for d in pdf_rule_dates:
        ev = {**base_evidence("pdf_equity_evidence"),
              "field": f"candidate_dates_closed_halt_early[{d}]",
              "provenance_class": "OFFICIAL_PER_HOLIDAY_GLOBEX_PDF_EQUITY_SECTION (equity-family "
                                  "authority; ES-specific transcription remains NOT_RUN per the "
                                  "evidence json family_authority_note)",
              "classification": pdf_cands[d]["entries"],
              "truncation_times_ct": pdf_cands[d].get("truncation_times_ct"),
              "pdf_statements_verbatim": stmt_by_date.get(d, []),
              "not_pdf_adjudicated_regular": d not in regular_nonempty,
              "law": "PREGO-REPAIR HOLIDAY-REPAIR-AUTH (owner 2026-10-04): every in-panel session "
                     "on a committed 53-PDF primary-tier candidate date (CLOSED/HALT/EARLY_CLOSE) "
                     "not PDF-adjudicated regular is EXCLUDED, conservative direction only "
                     "(SPEC_PB1_ES §2-E1 fail-closed; closes exposure finding F-A1 blocker "
                     "2015-07-02 named by holiday/exposure_proof_2011_2016.json)"}
        assign.setdefault(d, ("HOLIDAY_PDF_EQUITY_2011_2015", ev))
    for yr, ds in sorted(uncertain_years.items()):
        for d in ds:
            assign.setdefault(d, ("HOLIDAY_UNCERTAIN", {
                **base_evidence("es_session_holiday"),
                "field": f"holiday_deviation_windows_2017_2026[year={yr}].holiday_dates_for_legality",
                "provenance_class": "WINDOW_LEVEL_ARCHIVED_OFFICIAL; ES-specific Globex early-close "
                                    "times NOT_TRANSCRIBED (not_obtained_register)",
                "law": "SPEC_PB1_ES §2-E1 fail-closed: session-day excluded unless ES-specific "
                       "holiday/early-close status is proven per-day"}))
    for d in cov_rule:
        r = by_date[d]
        assign.setdefault(d, ("COVERAGE_LT60", {
            **base_evidence("session_dispersion_es"),
            "field": "sessions[].rth_core_coverage < 0.6 (== excluded_dates)",
            "law": "SPEC_PB1_ES §3 [ERRATUM A7-SPEC-M4]: RTH-core coverage (minutes 08:30-15:00 CT "
                   "having a bar, era-correct) < 60% => EXCLUDE; never imputed",
            "rth_core_coverage": r["rth_core_coverage"],
            "bars_rth_core_held": r["bars_rth_core_held"],
            "held_symbol": r["held_symbol"],
            "panel_recomputed_bars_rth_core_held": recomputed[d]}))

    # WARMUP: first 252 surviving sessions per fold (post base excludes), by law.
    warmup_dates = {}
    survivors = [d for d in dates_sorted if d not in assign and fold_of(d) is not None]
    for fid, lo, hi in FOLD_WINDOWS:
        in_fold = [d for d in survivors if lo <= d <= hi]
        take = in_fold[:WARMUP_SESSIONS]
        record_test(f"{fid} has >= {WARMUP_SESSIONS} surviving sessions",
                    len(in_fold) >= WARMUP_SESSIONS,
                    f"{fid}: {len(in_fold)} survivors, warmup takes first {len(take)}")
        warmup_dates[fid] = take
        for d in take:
            assign[d] = ("WARMUP", {
                "file": "plans/PLAN_futures_es_pb1_v1.md §3 + research/control/FUTURES-ES-V1-PACKET/SPEC_PB1_ES.md §3/§7",
                "sha256": shas["PLAN_REGISTERED"]["sha256"],
                "law": "warmup 252 sessions per fold head — excluded from scoring (signal q80 needs "
                       "trailing-252d strict past; folds multiply evaluation views, never identities)",
                "fold": fid, "position_in_fold": in_fold.index(d) + 1})

    # ---- v2 rule assertions (fail-closed on the NEW class) ----
    pdf_in_panel = [d for d in pdf_rule_dates if d in by_date]
    pdf_not_excluded = [d for d in pdf_in_panel if assign.get(d, (None,))[0] != "HOLIDAY_PDF_EQUITY_2011_2015"]
    record_test("every in-panel PDF candidate session carries HOLIDAY_PDF_EQUITY_2011_2015",
                not pdf_not_excluded,
                f"{len(pdf_rule_dates)} candidate dates in chain span; {len(pdf_in_panel)} are "
                f"in-panel sessions; unlabelled={pdf_not_excluded}")
    fomc_pdf_overlap = sorted(set(fomc_dates) & set(pdf_rule_dates))
    record_test("FOMC/PDF-candidate overlap recorded (FOMC keeps the label; set is the union)",
                True,
                f"overlap={fomc_pdf_overlap} (empty => no precedence interaction; any overlap would "
                f"still be excluded either way)")
    # conservative direction: v2 exclude SET must be a SUPERSET of the v1 set.
    # BOTH maps must span in-span entries AND out-of-span law dates, else the
    # 2010/2026 HOLIDAY_FACT law dates (identical in v1 and v2) would leak in
    # as false "added" rows.
    v1_cls = {e["session_date"]: e["reason_class"] for e in v1_exclude["exclusions"]}
    v1_cls_full = dict(v1_cls)
    v1_cls_full.update({e["session_date"]: e["reason_class"]
                        for e in v1_exclude["law_dates_out_of_chain_span"]})
    v2_cls = {d: assign[d][0] for d in assign}  # full map: in-span + out-of-span
    removed = sorted(set(v1_cls_full) - set(v2_cls))
    record_test("conservative direction: zero sessions REMOVED from exclusion (superset law)",
                not removed,
                f"v1 excludes {len(v1_cls_full)} law dates (in-span {len(v1_cls)} + out-of-span "
                f"{len(v1_cls_full) - len(v1_cls)}), v2 excludes {len(v2_cls)}; removed={removed}"
                + ("  *** CRITICAL: removal detected — repair must not narrow the freeze ***"
                   if removed else ""))
    added = sorted(set(v2_cls) - set(v1_cls_full))
    added_sessions = [d for d in added if d in by_date]
    added_law_dates = [d for d in added if d not in by_date]
    record_test("added exclusion sessions == exactly {2015-07-02}",
                added_sessions == ["2015-07-02"],
                f"added law dates total {len(added)} ({len(added_sessions)} in-panel sessions + "
                f"{len(added_law_dates)} non-session law dates); added in-panel sessions="
                f"{added_sessions}; the pre-existing 35 candidate sessions keep their exclusion "
                f"(label moves COVERAGE_LT60 -> HOLIDAY_PDF_EQUITY_2011_2015)")

    exclusions = []
    for d in sorted(assign):
        cls, ev = assign[d]
        r = by_date.get(d)
        fid = fold_of(d)
        exclusions.append({
            "session_date": d,
            "reason_class": cls,
            "priority_rank": prio_idx[cls],
            "evidence": ev,
            "era": None if r is None else {"quality_era": r["quality_era"],
                                           "close_era": r["close_era"],
                                           "tri_era": r["tri_era"]},
            "fold": fid,
            "in_panel": r is not None,
        })

    in_panel_excl = [e for e in exclusions if e["in_panel"]]
    no_session_law_dates = [e for e in exclusions if not e["in_panel"]]
    out_of_span = sorted(d for d in assign if d < span[0] or d > span[1])
    exclusions_in_span = [e for e in exclusions if e["session_date"] not in out_of_span]

    counts_in_span = {c: sum(1 for e in exclusions_in_span if e["reason_class"] == c) for c in PRIORITY}
    counts_in_panel = {c: sum(1 for e in in_panel_excl if e["session_date"] not in out_of_span
                              and e["reason_class"] == c) for c in PRIORITY}
    candidates_multi = {d: [] for d in dates_sorted}
    cand_sets = {
        "FOMC_STATEMENT_DAY": set(fomc_dates),
        "HOLIDAY_FACT_EARLYCLOSE": {d for d, _, _ in holiday_fact_entries} & set(dates_sorted),
        "HOLIDAY_PDF_EQUITY_2011_2015": set(pdf_rule_dates) & set(dates_sorted),
        "HOLIDAY_UNCERTAIN": {d for ds in uncertain_years.values() for d in ds} & set(dates_sorted),
        "COVERAGE_LT60": set(cov_rule),
    }
    for cls, s in cand_sets.items():
        for d in s:
            candidates_multi[d].append(cls)
    multi = {d: v for d, v in candidates_multi.items() if len(v) > 1}

    exclude_obj = {
        "schema": "exclude_list@2",
        "cycle_id": CYCLE_ID,
        "gate": "gate 2 REPAIR (append-only supersession of freezegen/exclude_list.json, which is "
                "HISTORY and unchanged); 0-cost: no PnL, no signal computation",
        "supersedes": {
            "artifact": f"{FREEZEGEN_DIR}/exclude_list.json",
            "sha256": INPUTS["v1_exclude_list"][1],
            "generation_head": v1_exclude["head_sha"],
            "law": "append-only supersession; the v1 file is never modified",
        },
        "owner_authority": {
            "record": INPUTS["PREGO_REPAIR_RECORDED"][0],
            "sha256": INPUTS["PREGO_REPAIR_RECORDED"][1],
            "decision_id": "HOLIDAY-REPAIR-AUTH",
            "decision_quote_verbatim": repair_auth["decision_quote_verbatim"],
            "decision_basis_law": repair_auth["decision_basis_law"],
            "not_a_go_law": prego["not_a_go_law"],
        },
        "generated_utc": GENERATED_UTC,
        "worktree": WORKTREE,
        "head_sha": HEAD_SHA,
        "determinism_law": "every element is a pure function of the committed artifacts cited in its "
                           "evidence block (file+field+sha256); no imputation; fail-closed",
        "reason_class_enum_note": "v1 enum (FOMC_STATEMENT_DAY, HOLIDAY_FACT_EARLYCLOSE, "
                                  "HOLIDAY_UNCERTAIN, COVERAGE_LT60, WARMUP) preserved; REPAIR adds "
                                  "HOLIDAY_PDF_EQUITY_2011_2015 (PREGO HOLIDAY-REPAIR-AUTH). OTHER_"
                                  "NAMED_LAW is retained in the enum with count 0 (law_notes E2-E5).",
        "reason_class_priority": PRIORITY,
        "priority_rule": "a session carrying multiple candidate classes is labelled by the first "
                         "class in reason_class_priority; the exclude SET is the union either way",
        "new_rule_law": {
            "class": "HOLIDAY_PDF_EQUITY_2011_2015",
            "rule": "exclude every in-panel session whose date is a committed 53-PDF primary-tier "
                    "candidate (CLOSED/HALT/EARLY_CLOSE) AND is not PDF-adjudicated regular",
            "artifact": {"file": INPUTS["pdf_equity_evidence"][0],
                         "sha256": INPUTS["pdf_equity_evidence"][1]},
            "n_candidate_dates_in_chain_span": len(pdf_rule_dates),
            "n_candidate_dates_in_panel": len(pdf_in_panel),
            "n_candidate_dates_absent_from_panel": len(pdf_rule_dates) - len(pdf_in_panel),
            "kept_included_by_adjudication": {
                "2015-09-04": "PDF REGULAR_CLOSE (2015-labor-day-holiday-schedule.pdf '1615 CT - "
                              "Regular close'); stays in its data-measured class (survivor)",
            },
            "fail_closed_law": "PDF-absent dates keep their current classes; 2016 (no PDF set, "
                               "evidence of absence) is NOT covered and stays NOT_RUN — re-proven "
                               "separately by repair/exposure_proof_v2.json",
        },
        "session_universe": {
            "source_file": INPUTS["session_dispersion_es"][0],
            "source_sha256": shas["session_dispersion_es"]["sha256"],
            "field": "sessions[] (n=4204, session_date ascending)",
            "n_sessions": len(sessions),
            "first_session": dates_sorted[0],
            "last_session": dates_sorted[-1],
            "note": "session 2026-10-01 is the panel-trim tail stub (129 bars, RTH-core coverage 0.0); "
                    "it is inside COVERAGE_LT60 and outside every fold window (fold=null)",
        },
        "chain_span": {"first_session": span[0], "last_session": span[1]},
        "counts": {
            "per_reason_class_chain_span": counts_in_span,
            "per_reason_class_in_panel_sessions": counts_in_panel,
            "total_exclusion_entries": len(exclusions),
            "in_panel_session_exclusions": sum(counts_in_panel.values()),
            "law_dates_with_no_panel_session": len([e for e in no_session_law_dates
                                                    if e["session_date"] not in out_of_span]),
            "law_dates_out_of_chain_span": len(out_of_span),
        },
        "coverage_margin": margin,
        "overlaps_before_precedence": {
            "sessions_with_multiple_candidate_classes": len(multi),
            "detail": {d: v for d, v in sorted(multi.items())},
        },
        "exclusions": exclusions_in_span,
        "law_dates_out_of_chain_span": [
            {"session_date": d, "reason_class": assign[d][0], "note": "outside the chain span "
             f"({span[0]}..{span[1]}); listed for fail-closed completeness, not a chain session"}
            for d in out_of_span],
        "law_notes": [
            "FOMC 132nd statement = 2020-03-15 (Sunday, 17:00; ES_fomc_stats.json release_time_note "
            "irregular list) — no session exists to exclude (panel has zero weekend RTH sessions); "
            "the dated day-exclude basis is the 131 in-data rows of per_event_day_level.",
            "E2 (whole-quarter exclude on any expiry-source mismatch): 0 quarters excluded — "
            "es_expiry_recheck.json: 68/68 expiry union re-derived, 66/66 data-side match "
            "(sha " + shas["es_expiry_recheck"]["sha256"] + ").",
            "E3 (2026 bounds), E4 (uncertain prev-session => signal-day exclude), E5 "
            "(strays/dash/break-bars per DATACONTRACT §1.6) are signal-time laws carried into "
            "scoring; they are not enumerable at this 0-cost freeze without signal computation and "
            "are NOT silently assumed empty here.",
            "WARMUP entries extend the base enum per mission M1(d); warmup sessions are excluded "
            "from scoring, not from the data chain.",
            "REPAIR: HOLIDAY_PDF_EQUITY_2011_2015 consumes holiday/pdf_equity_evidence_2011_2015.json "
            "(53 committed per-holiday CME Globex schedule PDFs 2011-2015, 'CME Group Equity Products' "
            "sections; 56 primary-tier candidates, 106 PDF-adjudicated regular dates, lemma2 "
            "truncation times all < 15:00 CT). The equity-family authority basis and the residual "
            "ES-specific-transcription NOT_RUN are documented in that artifact's "
            "family_authority_note. The v1 blocker 2015-07-02 (exposure_proof_2011_2016.json "
            "NOT_RUN_BLOCKER) is now excluded by this class.",
        ],
        "not_run_elements": [
            "Per-day holiday enumeration 2016 — NOT_RUN (UNCHANGED by this repair): no committed "
            "machine-readable per-day list exists for 2016 (es_session_holiday.json windows start "
            "2017; cmecal_coverage.json year-2016 note is a window/note-level naming; the committed "
            "per-holiday PDF set covers 2011-2015 only — evidence of absence recorded in "
            "holiday/HOLIDAY_CLOSURE.md M2). The 2016 sessions' fail-closed basis is re-proven "
            "separately by repair/exposure_proof_v2.json (M2): the class HOLIDAY_PDF_EQUITY_2011_2015 "
            "deliberately does NOT cover 2016, and 2016 is NOT silently treated as resolved. "
            "2011-2016 early closes with <60% coverage remain excluded via COVERAGE_LT60, and FOMC "
            "days remain excluded via FOMC_STATEMENT_DAY.",
            "ES-specific per-day/per-time transcription 2011-2015 — NOT_RUN (carried): the PDF rule "
            "consumes equity-FAMILY day-level candidates; per-product ES Globex times remain "
            "untranscribed (not_obtained_register). Conservative direction: candidates are "
            "EXCLUDED, never upgraded on transcription gaps.",
        ],
        "tests": tests,
    }

    os.makedirs(os.path.join(WORKTREE, REPAIR_DIR), exist_ok=True)
    exclude_sha = write_json(f"{REPAIR_DIR}/exclude_list_v2.json", exclude_obj)

    # ------------------------------------------------------- M3: freeze diff
    def eval_surface_from(cls_map, warmup_map):
        folds_out = []
        for fid, lo, hi in FOLD_WINDOWS:
            in_fold_all = [d for d in dates_sorted if lo <= d <= hi]
            excl_in_fold = [d for d in in_fold_all
                            if cls_map.get(d) is not None and cls_map[d] != "WARMUP"]
            surv = [d for d in in_fold_all if d not in excl_in_fold]
            wu = warmup_map[fid]
            ev = [d for d in surv if d not in set(wu)]
            folds_out.append({"fold": fid, "n_sessions_in_window": len(in_fold_all),
                              "n_base_excluded": len(excl_in_fold), "n_surviving": len(surv),
                              "warmup_first": wu[0] if wu else None,
                              "warmup_last": wu[-1] if wu else None,
                              "eval_n": len(ev), "eval_first": ev[0] if ev else None,
                              "eval_last": ev[-1] if ev else None})
        return folds_out

    v2_folds = eval_surface_from(v2_cls, warmup_dates)
    # v1 warmup sets: reconstruct from v1 exclude list WARMUP rows
    v1_warmup_dates = {}
    for e in v1_exclude["exclusions"]:
        if e["reason_class"] == "WARMUP" and e["fold"]:
            v1_warmup_dates.setdefault(e["fold"], []).append(e["session_date"])
    v1_folds = eval_surface_from(v1_cls, v1_warmup_dates)
    # cross-check v1 reconstruction against the frozen v1 selection_freeze
    for a, b in zip(v1_folds, v1_selection["fold_structure"]["folds"]):
        record_test(f"v1 fold {a['fold']} reconstruction matches frozen selection_freeze",
                    a["eval_n"] == b["eval_sessions"]["n"]
                    and a["eval_first"] == b["eval_sessions"]["first"]
                    and a["eval_last"] == b["eval_sessions"]["last"]
                    and a["n_base_excluded"] == b["n_base_excluded"],
                    f"reconstructed {a['eval_n']} eval ({a['eval_first']}..{a['eval_last']}), "
                    f"{a['n_base_excluded']} base-excluded == frozen "
                    f"{b['eval_sessions']['n']} ({b['eval_sessions']['first']}.."
                    f"{b['eval_sessions']['last']}), {b['n_base_excluded']}")
    v1_warmup_flat = sorted(d for ds in v1_warmup_dates.values() for d in ds)
    v2_warmup_flat = sorted(d for ds in warmup_dates.values() for d in ds)
    record_test("WARMUP sets identical v1 -> v2",
                v1_warmup_flat == v2_warmup_flat,
                f"{len(v1_warmup_flat)} warmup sessions (4x252); the single added exclusion "
                f"(2015-07-02, 2015) sits AFTER every v1 fold-head warmup window end "
                f"(max warmup end in F2 = 2014-01-16), so no warmup boundary moves")

    relabels = []
    for d in sorted(set(v1_cls) & set(v2_cls)):
        if v1_cls[d] != v2_cls[d]:
            relabels.append({"session_date": d, "v1_class": v1_cls[d], "v2_class": v2_cls[d],
                             "in_panel": d in by_date,
                             "pdf_evidence": ({"file": stmt_by_date[d][0]["file"],
                                               "sha256": stmt_by_date[d][0]["sha256"],
                                               "classification": stmt_by_date[d][0]["classification"],
                                               "time_ct": stmt_by_date[d][0]["time_ct"],
                                               "verbatim": stmt_by_date[d][0]["verbatim"]}
                                              if d in stmt_by_date else None)})
    added_rows = []
    for d in added_sessions:
        st = stmt_by_date.get(d, [{}])[0]
        added_rows.append({
            "session_date": d, "v1_class": None, "v2_class": v2_cls[d],
            "fold": fold_of(d), "in_eval_surface_v1": d not in v1_cls,
            "panel": {k: by_date[d][k] for k in
                      ("held_symbol", "bars_rth_core_held", "rth_core_coverage", "quality_era",
                       "close_era", "tri_era") if k in by_date[d]},
            "pdf_evidence": {"file": st.get("file"), "sha256": st.get("sha256"),
                             "classification": st.get("classification"),
                             "time_ct": st.get("time_ct"), "verbatim": st.get("verbatim")},
            "why": "PREGO HOLIDAY-REPAIR-AUTH: committed official schedule names this date an "
                   "equity-family early close; the exposure proof named it NOT_RUN_BLOCKER "
                   "(eval-eligible with unadjudicated holiday status); conservative repair "
                   "EXCLUDES it (evidence-vs-data conflict resolved in the conservative direction)",
        })
    diff_obj = {
        "schema": "freeze_diff@1",
        "cycle_id": CYCLE_ID,
        "generated_utc": GENERATED_UTC,
        "worktree": WORKTREE,
        "head_sha": HEAD_SHA,
        "owner_authority": {"record": INPUTS["PREGO_REPAIR_RECORDED"][0],
                            "sha256": INPUTS["PREGO_REPAIR_RECORDED"][1],
                            "decision_id": "HOLIDAY-REPAIR-AUTH"},
        "old_artifact": {"path": INPUTS["v1_exclude_list"][0],
                         "sha256": INPUTS["v1_exclude_list"][1],
                         "head_sha_at_generation": v1_exclude["head_sha"]},
        "new_artifact": {"path": f"{REPAIR_DIR}/exclude_list_v2.json", "sha256": exclude_sha},
        "direction_law": "conservative only: the v2 exclude set must be a strict SUPERSET of v1 "
                         "modulo class labels; any removal is a CRITICAL finding",
        "added_exclusions": added_rows,
        "n_added_exclusions_in_panel": len(added_rows),
        "added_law_dates_no_panel_session": [{"session_date": d, "v2_class": v2_cls[d]}
                                             for d in added_law_dates],
        "removed_exclusions": [{"session_date": d, "v1_class": v1_cls[d]} for d in removed],
        "n_removed_exclusions": len(removed),
        "critical_finding": bool(removed),
        "class_relabels_same_set": relabels,
        "n_class_relabels": len(relabels),
        "warmup_change": {"v1_n": len(v1_warmup_flat), "v2_n": len(v2_warmup_flat),
                          "identical": v1_warmup_flat == v2_warmup_flat},
        "eval_surface": {
            "total_old": sum(f["eval_n"] for f in v1_folds),
            "total_new": sum(f["eval_n"] for f in v2_folds),
            "per_fold": [
                {"fold": a["fold"],
                 "n_sessions_in_window": a["n_sessions_in_window"],
                 "n_base_excluded": {"old": a["n_base_excluded"], "new": b["n_base_excluded"]},
                 "n_surviving": {"old": a["n_surviving"], "new": b["n_surviving"]},
                 "warmup": {"old": [a["warmup_first"], a["warmup_last"]],
                            "new": [b["warmup_first"], b["warmup_last"]]},
                 "eval_n": {"old": a["eval_n"], "new": b["eval_n"]},
                 "eval_first": {"old": a["eval_first"], "new": b["eval_first"]},
                 "eval_last": {"old": a["eval_last"], "new": b["eval_last"]}}
                for a, b in zip(v1_folds, v2_folds)],
        },
        "counts_old_vs_new": {
            "per_reason_class_in_panel_sessions": {
                c: {"old": sum(1 for e in v1_exclude["exclusions"]
                               if e["reason_class"] == c and e["in_panel"]),
                    "new": counts_in_panel[c]}
                for c in sorted(set(v1_exclude["counts"]["per_reason_class_in_panel_sessions"])
                                | set(counts_in_panel))},
            "per_reason_class_chain_span": {
                c: {"old": v1_exclude["counts"]["per_reason_class_chain_span"].get(c, 0),
                    "new": counts_in_span[c]}
                for c in sorted(set(v1_exclude["counts"]["per_reason_class_chain_span"])
                                | set(counts_in_span))},
            "total_exclusion_entries": {"old": v1_exclude["counts"]["total_exclusion_entries"],
                                        "new": exclude_obj["counts"]["total_exclusion_entries"]},
            "in_panel_session_exclusions": {"old": v1_exclude["counts"]["in_panel_session_exclusions"],
                                            "new": exclude_obj["counts"]["in_panel_session_exclusions"]},
            "law_dates_with_no_panel_session": {
                "old": v1_exclude["counts"]["law_dates_with_no_panel_session"],
                "new": exclude_obj["counts"]["law_dates_with_no_panel_session"]},
        },
        "invariants": {
            "identity_table": {"n": len(identity["identities"]), "unchanged": True,
                               "sha256": INPUTS["identity_table_24"][1],
                               "law": "24 trial identities (P-A 8 + P-B 8 + FOMC 4 + C1-C4 4); the "
                                      "repair touches only session membership, never identities"},
            "budgets": {"trial_budget": 24, "unchanged": True,
                        "law": "identity/cell budget frozen at 24 (ES cap 24 FROZEN, "
                               "identity_table_24 reconciliation); cost contract untouched "
                               "(D3_RECORDED sha " + INPUTS["D3_RECORDED"][1] + ")"},
        },
        "changed_number_explanations": [
            "in_panel COVERAGE_LT60 69 -> 34: the 35 in-panel COVERAGE sessions that are also PDF "
            "primary-tier candidates are relabelled HOLIDAY_PDF_EQUITY_2011_2015 (priority rank 2 "
            "beats rank 4); the exclude SET is unchanged for them (union law).",
            "in_panel HOLIDAY_PDF_EQUITY_2011_2015 0 -> 36: those 35 relabelled sessions + "
            "2015-07-02 (the single NEW exclusion; previously an eval-eligible survivor).",
            "chain-span HOLIDAY_PDF_EQUITY_2011_2015 0 -> 56: the 36 in-panel + 20 candidate dates "
            "with no panel session (CLOSED/full-halt days), recorded as law dates with in_panel=false "
            "exactly as v1 recorded non-session HOLIDAY_* law dates.",
            "total_exclusion_entries 1305 -> 1326 (+21): +1 in-panel session (2015-07-02) + "
            "20 non-session law dates.",
            "law_dates_with_no_panel_session 19 -> 39 (+20): the non-session PDF candidate dates.",
            "eval surface 2926 -> 2925 (-1): F2 loses exactly 2015-07-02 from its eval surface; "
            "warmup windows are untouched (added exclusion post-dates every warmup window end).",
        ],
        "tests": [],
    }

    diff_sha = write_json(f"{REPAIR_DIR}/freeze_diff.json", diff_obj)

    # ------------------------------------------------- selection freeze v2
    folds = []
    for fid, lo, hi in FOLD_WINDOWS:
        in_fold_all = [d for d in dates_sorted if lo <= d <= hi]
        excl_in_fold = [d for d in in_fold_all if d in assign and assign[d][0] != "WARMUP"]
        surv = [d for d in in_fold_all if d not in excl_in_fold]
        wu = warmup_dates[fid]
        ev = [d for d in surv if d not in set(wu)]
        folds.append({
            "fold": fid,
            "window": {"from": lo, "to": hi},
            "n_sessions_in_window": len(in_fold_all),
            "n_base_excluded": len(excl_in_fold),
            "n_surviving": len(surv),
            "warmup_carve_out": {"n": len(wu), "first": wu[0] if wu else None,
                                 "last": wu[-1] if wu else None,
                                 "law": "SPEC_PB1_ES §3/§7: warmup 252 sessions per fold head"},
            "eval_sessions": {"n": len(ev), "first": ev[0] if ev else None,
                              "last": ev[-1] if ev else None},
        })
    total_eval = sum(f["eval_sessions"]["n"] for f in folds)

    laws_embedded = []
    for comp in pit["components"]:
        laws_embedded.append({
            "id": comp["id"],
            "law_one_line": comp["law_one_line"],
            "artifacts": comp["artifacts"],
        })
    # NEW law component: the PDF-evidence rule (PREGO repair)
    pdf_sha_list = [{"file": f["file"], "sha256": f["sha256"]} for f in pdf_ev["files"]]
    laws_embedded.append({
        "id": "REPAIR-1 HOLIDAY_PDF_EQUITY_2011_2015 (PREGO HOLIDAY-REPAIR-AUTH)",
        "law_one_line": "Owner-authorized conservative revision (2026-10-04): every in-panel session "
                        "on a committed 53-PDF primary-tier candidate date (CLOSED/HALT/EARLY_CLOSE, "
                        "2011-2015) not PDF-adjudicated regular is base-EXCLUDED; PDF-adjudicated "
                        "regular days (e.g. 2015-09-04) stay in their data-measured classes; 2016 "
                        "(no PDF set; evidence of absence) stays NOT_RUN and is re-proven "
                        "fail-closed by repair/exposure_proof_v2.json.",
        "artifacts": [
            {"path": INPUTS["pdf_equity_evidence"][0],
             "sha256": INPUTS["pdf_equity_evidence"][1],
             "what": "53-PDF extraction roll-up (schema pdf_equity_evidence_2011_2015@1): 56 "
                     "candidate dates CLOSED/HALT/EARLY_CLOSE, 106 regular-adjudicated dates, "
                     "lemma2 truncation times all < 15:00 CT, 5 documented anomalies"},
            {"path": pdf_ev["source_corpus"]["dir"],
             "sha256": None,
             "what": "the 53 committed per-holiday PDF captures; per-file sha256 list embedded "
                     "below (pdf_files_sha256) and verbatim equity sections at "
                     "files[].equity_section_verbatim of the evidence json",
             "catalog": pdf_ev["source_corpus"]["catalog"]},
            {"path": INPUTS["PREGO_REPAIR_RECORDED"][0],
             "sha256": INPUTS["PREGO_REPAIR_RECORDED"][1],
             "what": "owner decision record HOLIDAY-REPAIR-AUTH ('okay lên lệnh cho agent trong "
                     "zcode đi') authorizing this conservative revision; not a typed GO"},
        ],
        "pdf_files_sha256": pdf_sha_list,
    })

    # PINS now LAW: owner-ratified pin definitions embedded verbatim
    rat_pin_defs = []
    for p in pin_dec["pins"]:
        rat_pin_defs.append({
            "pin_id": p["pin_id"],
            "question_verbatim": p["question"],
            "ratified_option": p["dryrun_recorded_default"],
            "owner_effect_verbatim": pins_auth["effect"][p["pin_id"]],
        })
    selection = {
        "schema": "selection_freeze@2",
        "cycle_id": CYCLE_ID,
        "gate": "gate 2 REPAIR — deterministic exclude list v2 + selection freeze v2 "
                "(append-only supersession of freezegen/selection_freeze.json, which is HISTORY "
                "and unchanged; 0-cost; no PnL; no signal computation)",
        "supersedes": {
            "artifact": f"{FREEZEGEN_DIR}/selection_freeze.json",
            "sha256": INPUTS["v1_selection_freeze"][1],
            "law": "append-only supersession; v1 gate-2 artifacts are never modified",
        },
        "owner_authority": {
            "record": INPUTS["PREGO_REPAIR_RECORDED"][0],
            "sha256": INPUTS["PREGO_REPAIR_RECORDED"][1],
            "decisions": [
                {"id": "HOLIDAY-REPAIR-AUTH",
                 "decision_quote_verbatim": repair_auth["decision_quote_verbatim"],
                 "context_quote_from_owner_message": repair_auth["context_quote_from_owner_message"],
                 "decision_basis_law": repair_auth["decision_basis_law"]},
                {"id": "PINS-D-A1-A2-A3",
                 "decision_quote_verbatim": pins_auth["decision_quote_verbatim"],
                 "context_quote_from_owner_message": pins_auth["context_quote_from_owner_message"]},
            ],
            "not_a_go_law": prego["not_a_go_law"],
        },
        "generated_utc": GENERATED_UTC,
        "worktree": WORKTREE,
        "head_sha": HEAD_SHA,
        "registered_plan": {
            "path": "plans/PLAN_futures_es_pb1_v1.md (ROOT repo — read-only authority side)",
            "sha256": shas["PLAN_REGISTERED"]["sha256"],
            "law_quoted": "Folds: 4-fold shape F1 2010-06..2012-12 · F2 2013-01..2017-12 · "
                          "F3 2018-01..2021-12 · F4 2022-01..2026-09, warmup 252 sessions/fold head "
                          "(plan §3); gates: 2 = deterministic exclude list + selection freeze (plan §4).",
        },
        "identity_table": {
            "source_path": INPUTS["identity_table_24"][0],
            "source_sha256": shas["identity_table_24"]["sha256"],
            "embedding_note": "imported verbatim (parsed, not retyped) from freeze/identity_table_24.json; "
                              "SPEC §6 A-r4 table, P-A 8 + P-B 8 + FOMC 4 + C1-C4 4 = 24, reconciliation "
                              "zero-discrepancy; UNCHANGED by the repair",
            "embedded": identity,
        },
        "cost_contract": {
            "source_path": INPUTS["D3_RECORDED"][0],
            "source_sha256": shas["D3_RECORDED"]["sha256"],
            "source_pin_check": "measured sha equals freeze_pins_v2 sha256_v2 pin for D3_RECORDED "
                                "(f54610eb15e6cb41d32dec28616cdaaed6225fce0cfee9fe4cc3522b2fa1e355)",
            "source_field": "interpretation (decision_quote_verbatim + effective_cost_table_es + labels_binding + forbidden_values_law)",
            "cross_reference": "PLAN_futures_es_pb1_v1.md §2 (Variant A, owner D3 'tôi chọn 2.25$'); "
                               "COST_FREEZE_ERRATUM.md supersedes stale SPEC §5 prints; UNCHANGED by "
                               "the repair",
            "embedded": {
                "decision_quote_verbatim": d3["decision_quote_verbatim"],
                "chosen_variant": d3["interpretation"]["chosen_variant"],
                "effective_cost_table_es": d3["interpretation"]["effective_cost_table_es"],
                "labels_binding": d3["interpretation"]["labels_binding"],
                "forbidden_values_law": d3["interpretation"]["forbidden_values_law"],
            },
        },
        "exclude_list": {
            "path": f"{REPAIR_DIR}/exclude_list_v2.json",
            "sha256": exclude_sha,
            "reason_class_priority": PRIORITY,
            "counts": exclude_obj["counts"],
            "law_notes_count": len(exclude_obj["law_notes"]),
            "supersedes": {"path": INPUTS["v1_exclude_list"][0],
                           "sha256": INPUTS["v1_exclude_list"][1]},
        },
        "freeze_diff": {"path": f"{REPAIR_DIR}/freeze_diff.json", "sha256": diff_sha,
                        "n_added_exclusions_in_panel": len(added_rows),
                        "n_removed_exclusions": len(removed),
                        "eval_surface": {"old": sum(f["eval_n"] for f in v1_folds),
                                         "new": total_eval}},
        "fold_structure": {
            "law": "PLAN §3 / SPEC §7: 4 sequential folds post-EXCLUDE; warmup 252 sessions/fold head; "
                   "folds multiply evaluation views, never identities",
            "warmup_sessions_per_fold": WARMUP_SESSIONS,
            "folds": folds,
            "total_eval_sessions": total_eval,
            "tail_note": "session 2026-10-01 (panel-trim stub) lies outside all fold windows; it is "
                         "already excluded by COVERAGE_LT60 and carries fold=null in the exclude list",
        },
        "pins_manifest": {
            "base_manifest": {
                "path": INPUTS["freeze_pins_v2"][0],
                "sha256_at_head": shas["freeze_pins_v2"]["sha256"],
                "manifest_id": pins["manifest_id"],
                "pin_count": pins["pin_count"],
                "note": "AUTHORITATIVE 34-pin manifest @ " + HEAD_SHA + " for every artifact "
                        "unchanged by the repair — NOT re-pinned here; reference only "
                        "(self_reference_law: the base manifest hashes only the 34 freeze-set "
                        "artifacts, not itself)",
            },
            "v2_delta_pins": {
                "note": "the v2 freeze pins ADD exactly these three artifacts (append-only delta on "
                        "top of freeze_pins_v2); unchanged artifacts are covered by the base "
                        "manifest reference above; this file carries no hash of itself",
                "added_pins": [
                    {"artifact": f"{REPAIR_DIR}/exclude_list_v2.json", "sha256": exclude_sha},
                    {"artifact": INPUTS["PREGO_REPAIR_RECORDED"][0],
                     "sha256": INPUTS["PREGO_REPAIR_RECORDED"][1]},
                    {"artifact": INPUTS["pdf_equity_evidence"][0],
                     "sha256": INPUTS["pdf_equity_evidence"][1]},
                ],
            },
        },
        "owner_ratified_pins_law": {
            "source_decisions": INPUTS["pin_decisions"][0],
            "source_decisions_sha256": INPUTS["pin_decisions"][1],
            "record": INPUTS["PREGO_REPAIR_RECORDED"][0],
            "record_sha256": INPUTS["PREGO_REPAIR_RECORDED"][1],
            "decision_quote_verbatim": pins_auth["decision_quote_verbatim"],
            "context_quote_from_owner_message": pins_auth["context_quote_from_owner_message"],
            "decision_basis_law": pins_auth["decision_basis_law"],
            "identity_invariance": pins_auth["identity_invariance"],
            "pins_embedded_verbatim": rat_pin_defs,
            "law": "the three rehearsal-machinery pins are now LAW by owner ratification; the "
                   "definitions above are verbatim from pins/pin_decisions.json (question + "
                   "ratified option) and auth/PREGO_REPAIR_RECORDED.json (owner effect)",
        },
        "laws": {
            "source_path": INPUTS["pit_exclude_set"][0],
            "source_sha256": shas["pit_exclude_set"]["sha256"],
            "embedding_note": "the 7 PIT/exclude components embedded verbatim (id + law_one_line + "
                              "artifacts with shas) + the REPAIR-1 PDF-evidence component",
            "components": laws_embedded,
        },
        "not_run_register": {
            "carried_from_pit_exclude_set": pit["not_run_items_stay_not_run"],
            "added_by_this_gate": exclude_obj["not_run_elements"],
            "resolved_by_this_repair": [
                "Per-day holiday enumeration 2011-2015 (primary-tier candidates) — was NOT_RUN in "
                "v1 (X-A5 / A7 F-A1); now consumed by HOLIDAY_PDF_EQUITY_2011_2015: every in-panel "
                "candidate session is excluded (36) and the named blocker 2015-07-02 is out of the "
                "eval surface. ES-specific per-day transcription remains NOT_RUN (carried above).",
            ],
            "law": "NOT_RUN stays NOT_RUN (plan §3); a fail-closed-pending class is never silently "
                   "narrowed — 2016 enumeration explicitly remains NOT_RUN",
        },
        "no_self_hash_law": "this file carries no hash of itself; the exclude_list_v2 and "
                            "freeze_diff shas above are the only hashes minted by this repair",
    }

    selection_sha = write_json(f"{REPAIR_DIR}/selection_freeze_v2.json", selection)

    print(json.dumps({
        "exclude_list_v2_sha256": exclude_sha,
        "freeze_diff_sha256": diff_sha,
        "selection_freeze_v2_sha256": selection_sha,
        "counts_in_panel_sessions": counts_in_panel,
        "counts_entries_chain_span": counts_in_span,
        "added_in_panel": added_sessions,
        "added_law_dates_no_session": len(added_law_dates),
        "removed": removed,
        "relabels": len(relabels),
        "total_eval_sessions": {"old": sum(f["eval_n"] for f in v1_folds), "new": total_eval},
        "tests_passed": sum(1 for t in tests if t["verdict"] == "PASS"),
    }, indent=2))


if __name__ == "__main__":
    main()
