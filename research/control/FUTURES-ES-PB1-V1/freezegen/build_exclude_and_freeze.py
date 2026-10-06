#!/usr/bin/env python
"""FUTURES-ES-PB1-V1 gate 2 — deterministic exclude list + selection freeze.

Pure function of committed artifacts at worktree HEAD
e7fc1d8db00e91af74683cee7e999620fa8ff361 (branch prep/futures-es-reg-20261004).
0-cost: no PnL, no signal computation, no network. Fail-closed: any input sha
mismatch or rule mismatch aborts without writing outputs.

Run:
  /Users/hoangminhlong/my-quantitative/.venv/bin/python \
    research/control/FUTURES-ES-PB1-V1/freezegen/build_exclude_and_freeze.py

Outputs (write boundary: this directory only):
  exclude_list.json
  selection_freeze.json
"""
import hashlib
import json
import os
import sys

import pandas as pd
import pyarrow.parquet as pq

WORKTREE = "/Users/hoangminhlong/my-quantitative/.worktrees/futures-es-reg/prep"
ROOT_REPO_PLANS = "/Users/hoangminhlong/my-quantitative/plans"
HEAD_SHA = "e7fc1d8db00e91af74683cee7e999620fa8ff361"
CYCLE_ID = "FUTURES-ES-PB1-V1"
GENERATED_UTC = "2026-10-04"
WARMUP_SESSIONS = 252
FOLD_WINDOWS = [
    ("F1", "2010-06-01", "2012-12-31"),
    ("F2", "2013-01-01", "2017-12-31"),
    ("F3", "2018-01-01", "2021-12-31"),
    ("F4", "2022-01-01", "2026-09-30"),
]
PRIORITY = [
    "FOMC_STATEMENT_DAY",
    "HOLIDAY_FACT_EARLYCLOSE",
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
                       None),
    "pit_exclude_set": ("research/control/FUTURES-ES-PB1-REGPREP-20261004/freeze/pit_exclude_set.json",
                        None),
    "D3_RECORDED": ("research/control/FUTURES-ES-PB1-REGPREP-20261004/auth/D3_RECORDED.json",
                    "f54610eb15e6cb41d32dec28616cdaaed6225fce0cfee9fe4cc3522b2fa1e355"),
    "ES_fomc_stats": ("research/control/FUTURES-DEEPRESEARCH-V2-20261003/analysis/ES_fomc_stats.json",
                      "228fe2d4efbde95984128b6b1f64a9162bb794ea406c488577036fa09518f213"),
    "r3_fomc": ("research/control/FUTURES-DEEPRESEARCH-V2-20261003/audit/a7_es/r3_fomc.json",
                "ba57bc3325559b7f57a3757c63c8b93e6a900d54592eebcd098d940acc4e34f3"),
    "session_dispersion_es": ("research/control/FUTURES-K6GATE-PREP-20261004/es/session_dispersion_es.json",
                              None),
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
                        None),
}

FREEZEGEN_DIR = "research/control/FUTURES-ES-PB1-V1/freezegen"

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

    record_test("identity count 24",
                len(identity["identities"]) == 24 and identity["reconciliation"]["count_match"] is True,
                f"identity_table_24: {len(identity['identities'])} identities, reconciliation.count_match="
                f"{identity['reconciliation']['count_match']}")
    record_test("pins manifest 34", pins["pin_count"] == 34,
                f"freeze_pins_v2.pin_count={pins['pin_count']}")

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
    record_test("2011-2016 no committed per-day holiday enumeration",
                all(str(y) not in {str(yy) for yy in uncertain_years} for y in range(2011, 2017)),
                "es_session_holiday.json holiday_deviation_windows start at 2017; "
                "cmecal_coverage.json 2011-2016 coverage lists are window-level category labels only "
                "(holidays/early_closes/expirations, no dated cells) => NOT_RUN fail-closed-pending "
                "for the 2011-2016 holiday-class enumeration (those days remain covered by the "
                "bar-measured COVERAGE_LT60 rule and by FOMC where applicable)")

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
    # Law dates outside the chain span (before panel start / after panel end).
    out_of_span = sorted(d for d in assign if d < span[0] or d > span[1])
    exclusions_in_span = [e for e in exclusions if e["session_date"] not in out_of_span]

    counts_in_span = {c: sum(1 for e in exclusions_in_span if e["reason_class"] == c) for c in PRIORITY}
    counts_in_panel = {c: sum(1 for e in in_panel_excl if e["session_date"] not in out_of_span
                              and e["reason_class"] == c) for c in PRIORITY}
    # Overlap matrix (how many sessions carried >1 candidate class before precedence).
    candidates = {d: [] for d in dates_sorted}
    cand_sets = {
        "FOMC_STATEMENT_DAY": set(fomc_dates),
        "HOLIDAY_FACT_EARLYCLOSE": {d for d, _, _ in holiday_fact_entries} & set(dates_sorted),
        "HOLIDAY_UNCERTAIN": {d for ds in uncertain_years.values() for d in ds} & set(dates_sorted),
        "COVERAGE_LT60": set(cov_rule),
    }
    for cls, s in cand_sets.items():
        for d in s:
            candidates[d].append(cls)
    multi = {d: v for d, v in candidates.items() if len(v) > 1}

    exclude_obj = {
        "schema": "exclude_list@1",
        "cycle_id": CYCLE_ID,
        "gate": "gate 2 of the two-key law (deterministic exclude list + selection freeze); 0-cost: no PnL, no signal computation",
        "generated_utc": GENERATED_UTC,
        "worktree": WORKTREE,
        "head_sha": HEAD_SHA,
        "determinism_law": "every element is a pure function of the committed artifacts cited in its "
                           "evidence block (file+field+sha256); no imputation; fail-closed",
        "reason_class_enum_note": "M1(d) adds WARMUP to the M1 reason_class enum (fold-head 252 "
                                  "sessions/fold, excluded from scoring). OTHER_NAMED_LAW is retained "
                                  "in the enum with count 0 (see law_notes for E2/E3/E4/E5 handling).",
        "reason_class_priority": PRIORITY,
        "priority_rule": "a session carrying multiple candidate classes is labelled by the first "
                         "class in reason_class_priority; the exclude SET is the union either way",
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
        ],
        "not_run_elements": [
            "Per-day holiday enumeration 2011-2016 — NOT_RUN: no committed machine-readable per-day "
            "list exists (es_session_holiday.json windows start 2017; cmecal_coverage.json 2011-2016 "
            "coverage lists are window-level category labels only). Class HOLIDAY_UNCERTAIN is "
            "therefore fail-closed-pending for 2011-2016: any 2011-2016 holiday/early-close day with "
            ">=60% RTH-core coverage and no other named-law exclusion is NOT provably excluded by "
            "this freeze. Never silently narrower: 2011-2016 early closes with <60% coverage remain "
            "excluded via COVERAGE_LT60, and FOMC days remain excluded via FOMC_STATEMENT_DAY.",
        ],
        "tests": tests,
    }

    os.makedirs(os.path.join(WORKTREE, FREEZEGEN_DIR), exist_ok=True)
    exclude_sha = write_json(f"{FREEZEGEN_DIR}/exclude_list.json", exclude_obj)

    # ------------------------------------------------------- selection freeze
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

    selection = {
        "schema": "selection_freeze@1",
        "cycle_id": CYCLE_ID,
        "gate": "gate 2 of the two-key law — deterministic exclude list + selection freeze (0-cost; no PnL; no signal computation)",
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
                              "zero-discrepancy",
            "embedded": identity,
        },
        "cost_contract": {
            "source_path": INPUTS["D3_RECORDED"][0],
            "source_sha256": shas["D3_RECORDED"]["sha256"],
            "source_pin_check": "measured sha equals freeze_pins_v2 sha256_v2 pin for D3_RECORDED "
                                "(f54610eb15e6cb41d32dec28616cdaaed6225fce0cfee9fe4cc3522b2fa1e355)",
            "source_field": "interpretation (decision_quote_verbatim + effective_cost_table_es + labels_binding + forbidden_values_law)",
            "cross_reference": "PLAN_futures_es_pb1_v1.md §2 (Variant A, owner D3 'tôi chọn 2.25$'); "
                               "COST_FREEZE_ERRATUM.md supersedes stale SPEC §5 prints",
            "embedded": {
                "decision_quote_verbatim": d3["decision_quote_verbatim"],
                "chosen_variant": d3["interpretation"]["chosen_variant"],
                "effective_cost_table_es": d3["interpretation"]["effective_cost_table_es"],
                "labels_binding": d3["interpretation"]["labels_binding"],
                "forbidden_values_law": d3["interpretation"]["forbidden_values_law"],
            },
        },
        "exclude_list": {
            "path": f"{FREEZEGEN_DIR}/exclude_list.json",
            "sha256": exclude_sha,
            "reason_class_priority": PRIORITY,
            "counts": exclude_obj["counts"],
            "law_notes_count": len(exclude_obj["law_notes"]),
        },
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
            "path": INPUTS["freeze_pins_v2"][0],
            "sha256_at_head": shas["freeze_pins_v2"]["sha256"],
            "manifest_id": pins["manifest_id"],
            "pin_count": pins["pin_count"],
            "note": "AUTHORITATIVE 34-pin manifest @ " + HEAD_SHA + "; self_reference_law: the manifest "
                    "hashes only the 34 freeze-set artifacts, not itself",
        },
        "laws": {
            "source_path": INPUTS["pit_exclude_set"][0],
            "source_sha256": shas["pit_exclude_set"]["sha256"],
            "embedding_note": "the 7 PIT/exclude components embedded verbatim (id + law_one_line + artifacts with shas)",
            "components": laws_embedded,
        },
        "not_run_register": {
            "carried_from_pit_exclude_set": pit["not_run_items_stay_not_run"],
            "added_by_this_gate": exclude_obj["not_run_elements"],
            "law": "NOT_RUN stays NOT_RUN (plan §3); a fail-closed-pending class is never silently narrowed",
        },
        "no_self_hash_law": "this file carries no hash of itself; the exclude_list sha above is the only "
                            "hash minted by gate 2",
    }

    selection_sha = write_json(f"{FREEZEGEN_DIR}/selection_freeze.json", selection)

    print(json.dumps({
        "exclude_list_sha256": exclude_sha,
        "selection_freeze_sha256": selection_sha,
        "counts_in_panel_sessions": counts_in_panel,
        "counts_entries_chain_span": counts_in_span,
        "law_dates_no_session": len([e for e in no_session_law_dates if e["session_date"] not in out_of_span]),
        "law_dates_out_of_span": len(out_of_span),
        "total_eval_sessions": total_eval,
        "tests_passed": sum(1 for t in tests if t["verdict"] == "PASS"),
    }, indent=2))


if __name__ == "__main__":
    main()
