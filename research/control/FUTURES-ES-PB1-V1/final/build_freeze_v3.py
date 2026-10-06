#!/usr/bin/env python
# FREEZE-V3-MACHINERY (lane M1) — build final/exclude_list_v3.json +
# final/selection_freeze_v3.json for cycle FUTURES-ES-PB1-V1.
#
# Merge law (deterministic, pure function of committed artifacts):
#   exclude_list_v3 = exclude_list_v2 (repair/, HISTORY, sha-pinned)
#                   + the 11 recorded additions of
#                     y2016/exclude_2016_failclosed.json
#                     (class HOLIDAY_2016_UNPROVEN_FAILCLOSED):
#                       - 4 new set members appended (2016-07-01, 2020-07-02,
#                         2021-07-02, 2021-12-31);
#                       - 7 relabels REPLACE the existing COVERAGE_LT60 entry
#                         for the same date (evidence label upgrade; the
#                         exclude SET is unchanged; the replaced candidate
#                         class is preserved in overlaps_before_precedence,
#                         mirroring the v2 treatment of the 2011 relabels).
#   reason_class_priority gains HOLIDAY_2016_UNPROVEN_FAILCLOSED at position 4
#   (after HOLIDAY_PDF_EQUITY_2011_2015, per the y2016 artifact's recorded
#   priority_position); priority_rank is renumbered for every entry as a pure
#   function of its class (rank never affects the exclude SET, which is the
#   union either way).
#
# Assertions executed here (M1 mission):
#   - v2 arithmetic reproduced EXACTLY first (eval 375/949/711/890 = 2,925);
#   - merged eval surface == 2,921 (F1 375 / F2 948 / F3 708 / F4 890) with
#     EVAL_V3-recorded bounds (F3 eval-last 2021-12-31 -> 2021-12-30);
#   - v3 date set is a SUPERSET of v2: +4 dates, -0 dates;
#   - exactly the 11 recorded additions (4 appended + 7 relabels), no other
#     entry touched except the priority_rank renumbering (class-pure);
#   - WARMUP positional law intact (first 252 sessions of each fold).
#
# QUARANTINE LAW: no ledger/counter/registry write; no PnL input; zero
# network; root read-only outside final/; NO GO exists or is implied.

import hashlib
import json
from collections import Counter, OrderedDict

WT = "/Users/hoangminhlong/my-quantitative/.worktrees/futures-es-reg/prep"
C = WT + "/research/control/FUTURES-ES-PB1-V1"
GEN_UTC = "2026-10-05"
HEAD = "a855dab809be73c4b6eef60ab8c41566532febcd"   # measured at lane start

P_V2EXCL = C + "/repair/exclude_list_v2.json"
P_V2FRZ = C + "/repair/selection_freeze_v2.json"
P_ADD = C + "/y2016/exclude_2016_failclosed.json"
P_EVALV3 = C + "/y2016/eval_v3.json"
P_EVALV3MD = C + "/y2016/EVAL_V3.md"
P_FAILREC = C + "/repair/FAIL_DONOR_VIOLATION.md"
P_CARRY = C + "/repair/DONOR_LAW_CARRYOVER.md"
P_SWEEP = C + "/y2016/sweep_candidates_v3.json"
P_SPEC = WT + "/research/control/FUTURES-ES-V1-PACKET/SPEC_PB1_ES.md"
P_SU = WT + "/research/control/FUTURES-K6GATE-PREP-20261004/es/session_dispersion_es.json"

OUT_EXCL = C + "/final/exclude_list_v3.json"
OUT_FRZ = C + "/final/selection_freeze_v3.json"

EXPECTED_EVAL = {"F1": (375, "2011-06-10", "2012-12-31"),
                 "F2": (948, "2014-01-17", "2017-12-29"),
                 "F3": (708, "2019-01-18", "2021-12-30"),
                 "F4": (890, "2023-01-18", "2026-09-30")}
EXPECTED_EVAL_V2 = {"F1": (375, "2011-06-10", "2012-12-31"),
                    "F2": (949, "2014-01-17", "2017-12-29"),
                    "F3": (711, "2019-01-18", "2021-12-31"),
                    "F4": (890, "2023-01-18", "2026-09-30")}


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


SHAS = {p.split("/")[-1]: sha256_file(p)
        for p in (P_V2EXCL, P_V2FRZ, P_ADD, P_EVALV3, P_EVALV3MD,
                  P_FAILREC, P_CARRY, P_SWEEP, P_SPEC, P_SU)}
for p, pin in ((P_SPEC, "445f749906481f33080185cab1628e6365ef2f6db3b9c4f9f0847646eb6b7073"),
               (P_SU, "e56c4a53841983e02f5e643e60693581e2c9e096488a1f7491659a71bb7c43a4")):
    assert SHAS[p.split("/")[-1]] == pin, f"pin mismatch: {p}"
assert SHAS["exclude_list_v2.json"] == json.load(open(P_V2FRZ))[
    "exclude_list"]["sha256"], "v2 freeze embeds a different exclude sha"

v2excl = json.load(open(P_V2EXCL))
v2frz = json.load(open(P_V2FRZ))
add = json.load(open(P_ADD))
evalv3 = json.load(open(P_EVALV3))
su = json.load(open(P_SU))

assert v2excl["schema"] == "exclude_list@2"
assert add["schema"] == "exclude_2016_failclosed@1"
assert len(su["sessions"]) == 4204

# ---------------------------------------------------------------- merge ----
CLASS_RANK_V3 = {"FOMC_STATEMENT_DAY": 0, "HOLIDAY_FACT_EARLYCLOSE": 1,
                 "HOLIDAY_PDF_EQUITY_2011_2015": 2,
                 "HOLIDAY_2016_UNPROVEN_FAILCLOSED": 3,
                 "HOLIDAY_UNCERTAIN": 4, "COVERAGE_LT60": 5, "WARMUP": 6}
PRIORITY_V3 = list(CLASS_RANK_V3)
RULE_LAW_V3 = add["new_rule_law"]["rule"]

entries = [dict(e) for e in v2excl["exclusions"]]
by_date = {}
for e in entries:
    assert e["session_date"] not in by_date, "v2 duplicate date"
    by_date[e["session_date"]] = e

appended, replaced = [], []
for a in add["exclusions"]:
    d = a["session_date"]
    assert a["in_panel"] is True
    assert a["reason_class"] == "HOLIDAY_2016_UNPROVEN_FAILCLOSED"
    ev = dict(a["evidence"])
    ev["bars_rth_core_held"] = a["bars_rth_core_held"]
    ev["held_symbol"] = a["held_symbol"]
    ev["new_set_member"] = a["new_set_member"]
    ev["prev_class"] = a["prev_class"]
    ev["law"] = RULE_LAW_V3
    ev["source_artifact"] = {
        "file": "research/control/FUTURES-ES-PB1-V1/y2016/exclude_2016_failclosed.json",
        "sha256": SHAS["exclude_2016_failclosed.json"]}
    ne = {"era": dict(a["era"]), "evidence": ev, "fold": a["fold"],
          "in_panel": True, "priority_rank": CLASS_RANK_V3[a["reason_class"]],
          "reason_class": a["reason_class"], "session_date": d}
    if a["new_set_member"]:
        assert d not in by_date, f"new member already present in v2: {d}"
        entries.append(ne)
        by_date[d] = ne
        appended.append(d)
    else:
        old = by_date[d]
        assert a["prev_class"] == "COVERAGE_LT60"
        assert old["reason_class"] == "COVERAGE_LT60", (
            f"relabel target class mismatch for {d}")
        entries[entries.index(old)] = ne
        by_date[d] = ne
        replaced.append(d)

assert len(appended) == 4 and len(replaced) == 7
assert set(appended) == {"2016-07-01", "2020-07-02", "2021-07-02", "2021-12-31"}
assert len(entries) == len(v2excl["exclusions"]) + 4

# class-pure priority_rank renumbering + drift audit
drift = []
for e in entries:
    new_rank = CLASS_RANK_V3[e["reason_class"]]
    if e.get("priority_rank") != new_rank:
        drift.append({"session_date": e["session_date"],
                      "reason_class": e["reason_class"],
                      "rank_old": e.get("priority_rank"), "rank_new": new_rank})
    e["priority_rank"] = new_rank

# set invariants
d2 = {e["session_date"] for e in v2excl["exclusions"]}
d3 = {e["session_date"] for e in entries}
assert d3 >= d2 and len(d3 - d2) == 4 and len(d2 - d3) == 0
assert d3 - d2 == set(appended)

# ------------------------------------------------- eval surface (both) ----
def eval_surface(exclusion_entries):
    """Eval surface per the frozen law: 4 sequential folds POST-EXCLUDE;
    warmup = first 252 sessions of the fold head counted AFTER the
    non-WARMUP exclusions (that is how the WARMUP class is cut — e.g. F1
    head runs to 2011-06-09, not the raw 252nd session 2011-05-26)."""
    cls = {}
    for e in exclusion_entries:
        if e.get("in_panel"):
            cls.setdefault(e["session_date"], set()).add(e["reason_class"])
    out, total = {}, 0
    for f in v2frz["fold_structure"]["folds"]:
        w = f["window"]
        in_win = [s["session_date"] for s in su["sessions"]
                  if w["from"] <= s["session_date"] <= w["to"]]
        base_excl = {d for d in in_win if cls.get(d, set()) - {"WARMUP"}}
        kept = [d for d in in_win if d not in base_excl]
        warm = set(kept[:252])
        warm_cls = {d for d in in_win if "WARMUP" in cls.get(d, set())}
        assert warm == warm_cls and len(warm) == 252, (
            f"WARMUP positional law broken in {f['fold']}")
        ev = kept[252:]
        out[f["fold"]] = {"n": len(ev),
                          "first": ev[0] if ev else None,
                          "last": ev[-1] if ev else None,
                          "base_excl": len(base_excl)}
        total += len(ev)
    return out, total


surf_v2, tot_v2 = eval_surface(v2excl["exclusions"])
assert tot_v2 == 2925, tot_v2
for k, (n, lo, hi) in EXPECTED_EVAL_V2.items():
    assert (surf_v2[k]["n"], surf_v2[k]["first"], surf_v2[k]["last"]) == (n, lo, hi), k
assert [surf_v2[k]["base_excl"] for k in ("F1", "F2", "F3", "F4")] == [38, 75, 72, 85]

surf_v3, tot_v3 = eval_surface(entries)
assert tot_v3 == 2921, tot_v3
for k, (n, lo, hi) in EXPECTED_EVAL.items():
    assert (surf_v3[k]["n"], surf_v3[k]["first"], surf_v3[k]["last"]) == (n, lo, hi), k
assert [surf_v3[k]["base_excl"] for k in ("F1", "F2", "F3", "F4")] == [38, 76, 75, 85]
# cross-check against the y2016 machine record
for k in ("F1", "F2", "F3", "F4"):
    rec = evalv3["folds"][k]
    assert surf_v3[k]["n"] == rec["eval_n_new"]
    assert surf_v3[k]["first"] == rec["eval_first"]
    last = rec.get("eval_last_new", rec.get("eval_last"))
    assert surf_v3[k]["last"] == last
assert evalv3["total"]["new"] == 2921

# ---------------------------------------------------------------- counts ---
in_panel = [e for e in entries if e["in_panel"]]
per_class_inpanel = Counter(e["reason_class"] for e in in_panel)
per_class_span = Counter(e["reason_class"] for e in entries)
counts_v3 = {
    "in_panel_session_exclusions": len({e["session_date"] for e in in_panel}),
    "law_dates_out_of_chain_span": v2excl["counts"]["law_dates_out_of_chain_span"],
    "law_dates_with_no_panel_session": v2excl["counts"]["law_dates_with_no_panel_session"],
    "per_reason_class_chain_span": {k: per_class_span[k] for k in PRIORITY_V3},
    "per_reason_class_in_panel_sessions": {k: per_class_inpanel[k]
                                           for k in PRIORITY_V3},
    "total_exclusion_entries": len(entries)
    + v2excl["counts"]["law_dates_out_of_chain_span"],
}
assert counts_v3["in_panel_session_exclusions"] == 1283
assert counts_v3["total_exclusion_entries"] == 1330
assert sum(counts_v3["per_reason_class_in_panel_sessions"].values()) == 1283
assert sum(counts_v3["per_reason_class_chain_span"].values()) == len(entries)

overlap = {
    "detail": dict(v2excl["overlaps_before_precedence"]["detail"]),
    "note": "v2 detail carried verbatim; the 7 v3 relabels are appended below "
            "(candidate classes in v3 priority order; the exclude SET is the "
            "union either way — only the label moved, COVERAGE_LT60 evidence "
            "is preserved in the replacement entry's prev_class).",
}
for d in replaced:
    overlap["detail"][d] = ["HOLIDAY_2016_UNPROVEN_FAILCLOSED", "COVERAGE_LT60"]

excl_v3 = {
    "schema": "exclude_list@3",
    "cycle_id": "FUTURES-ES-PB1-V1",
    "generated_utc": GEN_UTC,
    "head_sha": HEAD,
    "worktree": WT,
    "chain_span": v2excl["chain_span"],
    "session_universe": v2excl["session_universe"],
    "coverage_margin": v2excl["coverage_margin"],
    "determinism_law": v2excl["determinism_law"],
    "priority_rule": v2excl["priority_rule"],
    "reason_class_priority": PRIORITY_V3,
    "reason_class_enum_note":
        "v1 enum (FOMC_STATEMENT_DAY, HOLIDAY_FACT_EARLYCLOSE, "
        "HOLIDAY_UNCERTAIN, COVERAGE_LT60, WARMUP) preserved; REPAIR added "
        "HOLIDAY_PDF_EQUITY_2011_2015; the y2016 fail-closed audit adds "
        "HOLIDAY_2016_UNPROVEN_FAILCLOSED at priority position 4 (y2016/"
        "exclude_2016_failclosed.json). OTHER_NAMED_LAW retained with count 0 "
        "(law_notes E2-E5).",
    "gate":
        "gate 2 REPAIR v3 (append-only supersession of repair/"
        "exclude_list_v2.json, itself superseding freezegen/exclude_list.json; "
        "both HISTORY and unchanged). Merge = v2 set + the 11 recorded y2016 "
        "fail-closed additions (4 new members appended, 7 COVERAGE_LT60 "
        "evidence relabels); eval surface 2,925 -> 2,921; 0-cost: no PnL, no "
        "signal computation.",
    "supersedes": {
        "artifact": "research/control/FUTURES-ES-PB1-V1/repair/exclude_list_v2.json",
        "sha256": SHAS["exclude_list_v2.json"],
        "law": "append-only supersession; the v2 file is never modified"},
    "owner_authority": v2excl["owner_authority"],
    "owner_audit_basis_v3": add["owner_audit_basis"],
    "new_rule_law": v2excl["new_rule_law"],
    "new_rule_law_v3": {
        "class": add["new_rule_law"]["class"],
        "rule": add["new_rule_law"]["rule"],
        "priority_position": add["new_rule_law"]["priority_position"],
        "identity_invariance": add["new_rule_law"]["identity_invariance"],
        "source_artifact": {
            "file": "research/control/FUTURES-ES-PB1-V1/y2016/exclude_2016_failclosed.json",
            "sha256": SHAS["exclude_2016_failclosed.json"]},
        "donor_law_note": "the y2016 artifact's donor_law_note (DONOR_LAW_"
                          "CARRYOVER: 'the 4 new exclusions remain donor-"
                          "admitted') is SUPERSEDED by repair/"
                          "FAIL_DONOR_VIOLATION.md (D-V2-2): the SPEC §4 "
                          "flag-based donor law governs — donor-excluded = "
                          "every session flagged short OR bearing ANY "
                          "exclusion/flag class in the CURRENT freeze, "
                          "evaluated on the current freeze's flags. See "
                          "selection_freeze_v3.donor_law.",
    },
    "law_dates_out_of_chain_span": v2excl["law_dates_out_of_chain_span"],
    "law_notes": v2excl["law_notes"],
    "overlaps_before_precedence": overlap,
    "not_run_elements": v2excl["not_run_elements"] + [
        "2016 per-day holiday enumeration — NOT_RUN (UNCHANGED by this v3 "
        "merge; EVAL_V3 §4/§6): no committed 2016 day-level artifact exists; "
        "what the HOLIDAY_2016_UNPROVEN_FAILCLOSED class closes is the "
        "EXPOSURE via fail-closed exclusion, not the enumeration."],
    "exclusions": entries,
    "counts": counts_v3,
    "merge_provenance_v3": {
        "law": "deterministic merge: every v3 element is a pure function of "
               "repair/exclude_list_v2.json + y2016/exclude_2016_failclosed.json",
        "inputs": {"exclude_list_v2": {"sha256": SHAS["exclude_list_v2.json"]},
                   "exclude_2016_failclosed": {"sha256": SHAS["exclude_2016_failclosed.json"]},
                   "session_universe": {"sha256": SHAS["session_dispersion_es.json"]}},
        "n_entries_v2": len(v2excl["exclusions"]),
        "n_entries_v3": len(entries),
        "appended_new_members": appended,
        "relabels_replacing_prev_entry": replaced,
        "priority_rank_renumber_drift_rows": len(drift),
        "priority_rank_renumber_drift_classes": sorted(
            {d["reason_class"] for d in drift}),
        "eval_surface_reproduced": {"v2": {"total": tot_v2,
                                           "per_fold": {k: surf_v2[k]["n"] for k in surf_v2}},
                                    "v3": {"total": tot_v3,
                                           "per_fold": {k: surf_v3[k]["n"] for k in surf_v3}}},
        "set_delta": {"added_dates": appended, "removed_dates": []},
        "tests_v3_merge": [
            {"test": "v2 eval arithmetic reproduced exactly (375/949/711/890 = 2925)",
             "verdict": "PASS"},
            {"test": "v3 eval surface == 2921 (F1 375 / F2 948 / F3 708 / F4 890), "
                     "bounds == EVAL_V3 (F3 eval-last 2021-12-30)", "verdict": "PASS"},
            {"test": "v3 date set superset of v2: +4 / -0", "verdict": "PASS"},
            {"test": "exactly 4 appended + 7 relabels == the 11 recorded additions",
             "verdict": "PASS"},
            {"test": "WARMUP positional law: WARMUP class set == first 252 "
                     "post-EXCLUDE sessions of each fold head (4 folds)", "verdict": "PASS"},
            {"test": "no duplicate dates; one entry per session", "verdict": "PASS"},
        ],
    },
    "tests": v2excl["tests"],
}
# 'tests' above is the v2 gate-2 evidence block carried verbatim (history);
# this merge's own assertions are tests_v3_merge above.
excl_v3["tests_provenance_note"] = (
    "the 'tests' block is the v2 gate-2 evidence carried verbatim (history, "
    "cites v2 shas); this merge's assertions are merge_provenance_v3."
    "tests_v3_merge.")

with open(OUT_EXCL, "w") as f:
    json.dump(excl_v3, f, indent=1, sort_keys=True)
SHAS["exclude_list_v3.json"] = sha256_file(OUT_EXCL)

# ------------------------------------------------- selection_freeze_v3 ----
fold_structure = {
    "law": v2frz["fold_structure"]["law"],
    "tail_note": v2frz["fold_structure"]["tail_note"],
    "warmup_sessions_per_fold": 252,
    "total_eval_sessions": tot_v3,
    "folds": [],
}
for f in v2frz["fold_structure"]["folds"]:
    s = surf_v3[f["fold"]]
    nf = dict(f)
    nf["eval_sessions"] = {"first": s["first"], "last": s["last"], "n": s["n"]}
    if f["fold"] == "F3":
        nf["eval_sessions_v2_history"] = dict(f["eval_sessions"])
        nf["eval_last_change_law"] = ("2021-12-31 now carries "
                                      "HOLIDAY_2016_UNPROVEN_FAILCLOSED "
                                      "(y2016 fail-closed); eval-last moves to "
                                      "2021-12-30 (EVAL_V3 §2)")
    fold_structure["folds"].append(nf)

freeze_v3 = {
    "schema": "selection_freeze@3",
    "cycle_id": "FUTURES-ES-PB1-V1",
    "generated_utc": GEN_UTC,
    "head_sha": HEAD,
    "worktree": WT,
    "gate":
        "gate 2 REPAIR v3 — combined corrected final state: freeze v3 (v2 + "
        "the 11 y2016 fail-closed additions) + FLAG-BASED SPEC §4 donor law "
        "(repair/FAIL_DONOR_VIOLATION.md, D-V2-2) + gate-4 dry-run on this "
        "state. Append-only supersession of repair/selection_freeze_v2.json "
        "(HISTORY, unchanged). 0-cost: no PnL, no signal computation.",
    "supersedes": {
        "artifact": "research/control/FUTURES-ES-PB1-V1/repair/selection_freeze_v2.json",
        "sha256": SHAS["selection_freeze_v2.json"],
        "law": "append-only supersession; v1 gate-2 artifacts and the v2 "
               "repair are never modified"},
    "exclude_list": {
        "path": "research/control/FUTURES-ES-PB1-V1/final/exclude_list_v3.json",
        "sha256": SHAS["exclude_list_v3.json"],
        "schema": "exclude_list@3",
        "counts": counts_v3,
        "law_notes_count": len(v2excl["law_notes"]),
        "reason_class_priority": PRIORITY_V3,
        "supersedes": {
            "path": "research/control/FUTURES-ES-PB1-V1/repair/exclude_list_v2.json",
            "sha256": SHAS["exclude_list_v2.json"]}},
    "cost_contract": v2frz["cost_contract"],
    "identity_table": v2frz["identity_table"],
    "laws": v2frz["laws"],
    "fold_structure": fold_structure,
    "freeze_diff_v3": {
        "law": "pure merge of repair/exclude_list_v2.json + y2016/"
               "exclude_2016_failclosed.json; v2 eval arithmetic reproduced "
               "exactly (2,925) before the v3 change was applied",
        "inputs": {"exclude_list_v2": SHAS["exclude_list_v2.json"],
                   "exclude_2016_failclosed": SHAS["exclude_2016_failclosed.json"],
                   "eval_v3": SHAS["eval_v3.json"]},
        "eval_surface": {"old": 2925, "new": 2921, "delta": -4},
        "per_fold": {k: {"old": EXPECTED_EVAL_V2[k][0], "new": EXPECTED_EVAL[k][0]}
                     for k in ("F1", "F2", "F3", "F4")},
        "n_added_exclusions_in_panel": 4,
        "n_relabeled_entries": 7,
        "n_removed_exclusions": 0,
        "added_dates": appended,
        "relabel_dates": replaced,
    },
    "donor_law": {
        "law_spec_quote_verbatim":
            "[ERRATUM A7-SPEC-M5] SL = 1.0 × median của 20 range RTH session "
            "liền trước (strict past; close marks era-correct; loại session "
            "short/flagged)",
        "spec": {"path": "research/control/FUTURES-ES-V1-PACKET/SPEC_PB1_ES.md",
                 "sha256": SHAS["SPEC_PB1_ES.md"]},
        "correction_record": {
            "finding_id": "D-V2-2",
            "path": "research/control/FUTURES-ES-PB1-V1/repair/FAIL_DONOR_VIOLATION.md",
            "sha256": SHAS["FAIL_DONOR_VIOLATION.md"],
            "law": "donor-excluded = every session flagged short OR bearing "
                   "ANY exclusion/flag class in the CURRENT freeze, evaluated "
                   "on the current freeze's flags — flag-based, never a fixed "
                   "historical label list or a historical session set; the "
                   "expected count is machine-derived, never asserted",
            "machinery_of_record":
                "research/control/FUTURES-ES-PB1-V1/final/dryrun_builder_v3.py"},
        "supersedes": {
            "path": "research/control/FUTURES-ES-PB1-V1/repair/DONOR_LAW_CARRYOVER.md",
            "sha256": SHAS["DONOR_LAW_CARRYOVER.md"],
            "law": "the carryover law ('donor set == v1's 139, v1 labels') is "
                   "WITHDRAWN by D-V2-2: it kept 2015-07-02 donor-admitted "
                   "against its v2/v3 flag and is a conflation of the v1 "
                   "code's hardcoded class list (implementation) with the "
                   "SPEC's flag-based law (authority)"},
    },
    "y2016_evidence": {
        "eval_v3_report": {"path": "research/control/FUTURES-ES-PB1-V1/y2016/EVAL_V3.md",
                           "sha256": SHAS["EVAL_V3.md"]},
        "eval_v3_machine": {"path": "research/control/FUTURES-ES-PB1-V1/y2016/eval_v3.json",
                            "sha256": SHAS["eval_v3.json"]},
        "v3_addition": {"path": "research/control/FUTURES-ES-PB1-V1/y2016/exclude_2016_failclosed.json",
                        "sha256": SHAS["exclude_2016_failclosed.json"]},
        "candidate_sweep": {"path": "research/control/FUTURES-ES-PB1-V1/y2016/sweep_candidates_v3.json",
                            "sha256": SHAS["sweep_candidates_v3.json"]},
        "verdict_2016": "EXCLUDED_FAILCLOSED (exposure closed; the 2016 "
                        "day-level enumeration itself remains NOT_RUN — "
                        "EVAL_V3 §6)",
        "eval_surface": "2,925 -> 2,921 (F2 -1: 2016-07-01; F3 -3: 2020-07-02, "
                        "2021-07-02, 2021-12-31)",
        "identity_invariance": "identity table 24 and trial budget 24 "
                               "unchanged (EVAL_V3 §5)",
    },
    "not_run_register": dict(v2frz["not_run_register"],
                             v3_status={
                                 "2016_day_level_enumeration": "NOT_RUN "
                                 "(UNCHANGED) — the fail-closed class closes "
                                 "exposure, not the enumeration (EVAL_V3 §6; "
                                 "route: owner-authorized web.archive CDX "
                                 "retrieval of 2016 holiday-calendar vintages)",
                                 "added_by_this_gate": []}),
    "owner_authority": v2frz["owner_authority"],
    "owner_audit_basis_v3": add["owner_audit_basis"],
    "owner_ratified_pins_law": v2frz["owner_ratified_pins_law"],
    "pins_manifest": v2frz["pins_manifest"],
    "registered_plan": v2frz["registered_plan"],
    "no_self_hash_law":
        "this file carries no hash of itself; the exclude_list_v3 sha and the "
        "evidence-block shas above are the only hashes minted by this freeze",
}
with open(OUT_FRZ, "w") as f:
    json.dump(freeze_v3, f, indent=1, sort_keys=True)

print(json.dumps({
    "exclude_list_v3_sha256": SHAS["exclude_list_v3.json"],
    "selection_freeze_v3_path": OUT_FRZ,
    "entries_v2": len(v2excl["exclusions"]), "entries_v3": len(entries),
    "appended": appended, "relabels": replaced,
    "rank_renumber_rows": len(drift),
    "rank_renumber_classes": sorted({d["reason_class"] for d in drift}),
    "eval_v2": {k: surf_v2[k]["n"] for k in surf_v2}, "total_v2": tot_v2,
    "eval_v3": {k: surf_v3[k]["n"] for k in surf_v3}, "total_v3": tot_v3,
    "counts_v3": counts_v3,
    "verdict": "M1 MERGE ASSERTIONS ALL PASS",
}, indent=1))
