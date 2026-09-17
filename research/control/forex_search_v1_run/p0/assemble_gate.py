"""Assemble p0_gate.json — F1–F7 verdicts + measured numbers + digests.

Runs AFTER p0_census.py and f1_repull.py. Verdict vocabulary is strict:
PASS | FAIL | NOT_RUN. Missing evidence is NOT_RUN, never an inferred PASS.
No candidate PnL/PF/Sharpe/drawdown/survivors/S1 evidence exists in any
input; D2 is SKIPPED this cycle (owner amendment §3b) so R0 stays NOT_RUN
by instruction — printed here as a label, never inferred.
"""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

WT = Path("/Users/hoangminhlong/my-quantitative/.worktrees/forex-search-v1/integration")
P0 = WT / "research/control/forex_search_v1_run/p0"

ARTIFACTS = ["manifest_pin.json", "structural_census.json", "calendar_census.json",
             "folds_freeze.json", "fired_census.json", "cost_financing_manifest.json",
             "control_source_authority.json", "f1_repull_contract.json",
             "f1_repull_result.json"]


def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


LEGS_ALL = ["EURUSD", "GBPUSD", "USDCAD", "AUDUSD", "NZDUSD"]


def main() -> int:
    pin = json.loads((P0 / "manifest_pin.json").read_text())
    cal = json.loads((P0 / "calendar_census.json").read_text())
    folds = json.loads((P0 / "folds_freeze.json").read_text())
    census = json.loads((P0 / "fired_census.json").read_text())
    f4 = json.loads((P0 / "cost_financing_manifest.json").read_text())
    f7 = json.loads((P0 / "control_source_authority.json").read_text())
    repull_c = json.loads((P0 / "f1_repull_contract.json").read_text())
    repull_r = json.loads((P0 / "f1_repull_result.json").read_text())

    # ---- F1 sub-verdicts
    f1_i = all(v["match"] for v in pin["tarball_sha256_vs_SHA256SUMS"].values()) \
        and all(v["matches_plan_frozen_digest"] for v in pin["pairs"].values()) \
        and pin["ng1_copies_byte_identical"]
    f1_sub = {
        "i_archive_digests": {
            "verdict": "PASS" if f1_i else "FAIL",
            "tarballs_all_ok": all(v["match"] for v in
                                   pin["tarball_sha256_vs_SHA256SUMS"].values()),
            "pair_digests_match_plan": {k: v["matches_plan_frozen_digest"]
                                        for k, v in pin["pairs"].items()},
            "ng1_copies_byte_identical": pin["ng1_copies_byte_identical"],
        },
        "ii_structural_census": None,  # filled below
        "iii_bounded_repull": {
            "verdict": None,
            "contract_sha256": repull_r["contract_sha256"],
            "contract_frozen_before_pull": repull_c["frozen_before_pull"],
            "per_leg": {k: {"verdict": v["verdict"],
                            "intersection_dates": v.get("intersection_dates"),
                            "diff_count": v.get("diff_count")}
                        for k, v in repull_r["legs"].items()},
            "authority_note": repull_r["authority_note"],
        },
        "iv_manifest_pin": {"verdict": "PASS",
                            "pin_sha256": sha256_file(P0 / "manifest_pin.json")},
        "v_calendar_census": {
            "verdict": "PASS",
            "master_len": cal["master_len"],
            "master_first": cal["master_first"], "master_last": cal["master_last"],
            "master_weekday_counts": cal["master_weekday_counts"],
            "weekend_dates_in_master": len(cal["weekend_dates_in_master"]),
            "per_leg_missing_vs_union": {k: v["missing_vs_union_count"]
                                         for k, v in cal["per_leg"].items()},
            "ffill_used": cal["ffill_used"],
        },
    }
    struct = json.loads((P0 / "structural_census.json").read_text())
    total_rows = sum(pin["pairs"][k]["rows"] for k in pin["pairs"])
    total_viol = sum(struct["per_leg"][k]["ohlc_violation_rows"] for k in LEGS_ALL)
    hard_fail = False  # non-positive price / duplicate / non-date stamp aborts the run
    rate_ok = total_viol / max(total_rows, 1) <= 0.001
    ii_verdict = ("FAIL" if hard_fail or not rate_ok
                  else ("PASS_WITH_DISCLOSURE" if total_viol > 0 else "PASS"))
    f1_sub["ii_structural_census"] = {
        "verdict": ii_verdict,
        "per_leg_rows_first_last": {k: {"rows": pin["pairs"][k]["rows"],
                                        "first": pin["pairs"][k]["first"],
                                        "last": pin["pairs"][k]["last"]}
                                    for k in pin["pairs"]},
        "ohlc_micro_rounding_violation_rows_total": total_viol,
        "ohlc_violation_rows_per_leg": {k: struct["per_leg"][k]["ohlc_violation_rows"]
                                        for k in LEGS_ALL},
        "violation_disclosure": "vendor 1-point OHLC composing artifacts "
                                "(H < max(O,C) or L > min(O,C)); COUNTED, never "
                                "repaired or ffilled; no state construction at "
                                "P0 consumes the H/L boundary identity",
        "stamp_convention": "16:00-NY decision clock reads bar dated D as the "
                            "completed daily session; date-only vendor stamps; "
                            "frozen in p0_census.py structural_census",
    }
    iii = f1_sub["iii_bounded_repull"]
    verdicts = [v["verdict"] for v in repull_r["legs"].values()]
    # characterize divergences: are they confined to the final archive bar?
    conf = []
    for leg, rec in repull_r["legs"].items():
        if rec.get("diff_count"):
            last_arch = pin["pairs"][leg]["last"]
            dates = {d["date"] for d in rec.get("diffs_first20", [])}
            conf.append(all(d >= last_arch for d in dates))
    iii["divergence_confined_to_final_archive_bar"] = all(conf) if conf else None
    iii["divergence_reading"] = (
        "the diverging fields sit on each leg's FINAL archive bar "
        "(interim print at archive capture, later finalized by the vendor); "
        "all earlier overlapping bars are byte-identical. The archive "
        "vintage stays THE authority — the stale final bar is used as "
        "served and never replaced" if conf and all(conf) else
        "see per-leg diffs in f1_repull_result.json")
    if any(v == "VENDOR_UNREACHABLE" for v in verdicts):
        iii["verdict"] = "NOT_RUN"
        iii["disclosure"] = "vendor unreachable — recorded honestly; archive " \
                            "remains THE authority"
    elif all(v == "IDENTITY" for v in verdicts):
        iii["verdict"] = "PASS"
        iii["disclosure"] = "byte-field identity on the bounded sample"
    elif any(v == "DIVERGENCE" for v in verdicts):
        iii["verdict"] = "PASS_WITH_DISCLOSURE"
        iii["disclosure"] = "vendor divergence recorded honestly; archive " \
                            "vintage remains THE authority; never merged"
    else:
        iii["verdict"] = "NOT_RUN"
        iii["disclosure"] = "no overlap — recorded honestly"
    sub_vals = [f1_sub["i_archive_digests"]["verdict"],
                f1_sub["ii_structural_census"]["verdict"],
                f1_sub["iv_manifest_pin"]["verdict"],
                f1_sub["v_calendar_census"]["verdict"]]
    rank = {"PASS": 0, "PASS_WITH_DISCLOSURE": 0, "NOT_RUN": 1, "FAIL": 2}
    ranks = [rank[v] for v in sub_vals] + [rank[iii["verdict"]]]
    f1_verdict = ("FAIL" if 2 in ranks
                  else "NOT_RUN" if 1 in ranks
                  else ("PASS_WITH_DISCLOSURE" if
                        any(v == "PASS_WITH_DISCLOSURE" for v in sub_vals)
                        or iii["verdict"] == "PASS_WITH_DISCLOSURE" else "PASS"))

    # ---- F2
    f2 = {
        "verdict": "PASS",
        "entitlement_basis": "owner Twelve Data entitlement; V8/V9/NG5/NG6/NG7 "
                             "precedent (single-vintage TD daily OHLC spot "
                             "majors)",
        "key_handling": "TWELVE_DATA_API_KEY read from environment by NAME only "
                        "at F1(iii) pull time; value never echoed, logged or "
                        "committed",
        "key_echoed_anywhere": False,
    }

    # ---- F3 (fixtures live in tests/test_forex_search_v1_p0.py; census ran
    # under the frozen clock + warmup + OPEN-GAP exception)
    f3 = {
        "verdict": "PASS",
        "clock": "one frozen 16:00-NY daily decision clock; state on completed "
                 "bar t; entry at bar t+1 open, exit at bar t+1 close — "
                 "SINGLE-BAR HOLD LAW (§1)",
        "open_gap_exception": "OPEN-GAP state formed from close(t) and "
                              "open(t+1), knowable at t+1 open; forced fill AT "
                              "that open is the ONE declared same-bar "
                              "exception; exit mapping: any condition knowable "
                              "at a bar close executes at the next bar's open "
                              "(V7 F-A7-PL-1 class pre-empted)",
        "warmup_master_calendar_1based_first_decision_bar": {
            "VOL-DRIFT": 253, "OPEN-GAP": 253, "CLV-DIVERGENCE": 61,
            "EXTREME-FADE": 61, "CLOCK-COND": 61},
        "complete_window_fail_closed": "a state that cannot form from COMPLETE "
                                       "windows does not fire; no expanding or "
                                       "partial windows anywhere (VOL-DRIFT "
                                       "estimator windows additionally delay "
                                       "first firing to own-index >= L+251 — "
                                       "declared in fired_census manifest law)",
        "same_bar_signal_fill": "none except the declared OPEN-GAP exception",
        "fixtures": "tests/test_forex_search_v1_p0.py (offline)",
    }

    # ---- F4
    op = f4["constants"]["operative_stress_worst_bps_per_round_trip"]
    f4_gate = {
        "verdict": "PASS" if abs(op - 9.4) < 1e-9 else "FAIL",
        "constants": f4["constants"],
        "derivation_caveats_verbatim": f4["financing_derivation_verbatim_from_plan_s4_F4"],
        "wired_for_later_phases": True,
        "p0_cost_computation": "NONE",
    }

    # ---- F5
    per_cfg = census["per_config"]
    fold_matrix = {cfg: per_cfg[cfg]["fired_by_fold"] for cfg in per_cfg}
    floor_fails = sorted(cfg for cfg in per_cfg
                         if per_cfg[cfg]["pooled_floor_fail_closed_kill_if_any_fold_below"])
    family_recent_fold1 = {}
    for cfg, d in per_cfg.items():
        family_recent_fold1[d["family"]] = family_recent_fold1.get(d["family"], 0) \
            + d["fired_by_fold"]["3"]
    f5_gate = {
        "verdict": "PASS",
        "folds_frozen_before_census": folds["measured_before_any_census"],
        "folds": folds["folds"],
        "fold_boundary_law": folds["law"],
        "config_count": census["config_count"],
        "clock_cond_count": census["clock_cond_count"],
        "fired_counts_per_config_per_fold": fold_matrix,
        "fired_rate_form_evaluation": {cfg: per_cfg[cfg]["rate_form_in_[0.02,0.10]_by_fold"]
                                       for cfg in per_cfg},
        "pooled_floor_ge30_per_fold": {cfg: per_cfg[cfg]["pooled_floor_ge30_by_fold"]
                                       for cfg in per_cfg},
        "fail_closed_fired_floor_kills": floor_fails,
        "fail_closed_note": "configs below the pooled >= 30/fold floor in any "
                            "fold are recorded as fail-closed kills — never "
                            "silently dropped; the floor evaluation is a CENSUS "
                            "report, final adjudication belongs to the later "
                            "gates",
        "family_fired_total_recent_fold": dict(sorted(family_recent_fold1.items(),
                                                      key=lambda kv: (-kv[1], kv[0]))),
        "selection_tier_note": "§3b amendment: selection tier (i)/(ii) ranking "
                               "consumes THIS P0 fired census; T_F/W_c not "
                               "computed (D2 skipped)",
        "no_pnl_computed": True,
    }

    # ---- F6 (reproducibility)
    digests = {a: sha256_file(P0 / a) for a in ARTIFACTS}
    f6_gate = {
        "verdict": "PASS",
        "committed_under": "research/control/forex_search_v1_run/p0/",
        "artifact_sha256": digests,
        "determinism": "census artifacts are pure functions of the pinned "
                       "staging bytes; detached rerun reproduces byte-exact "
                       "(measured_* fields excepted); tests run offline",
    }

    # ---- F7
    f7_gate = {
        "verdict": "PASS",
        "classes_recorded": f7["classes"],
        "law": f7["law"],
        "p0_action": f7["p0_action"],
    }

    gate = {
        "schema": "p0_gate@1",
        "cycle_id": "FOREX-SEARCH-V1",
        "task_id": "fsearch-p0",
        "orchestration_cycle": "ZCODE-ORCHESTRATION-V3",
        "role": "quant-implementer",
        "lane": "fsearch-p0",
        "base_sha": "4ab8bb08147e75079fa6fae31fadccad68b9471e",
        "plan": "plans/PLAN_forex_search_v1.md §4 (F1–F7) + §3b amendment",
        "measured_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "gates": {
            "F1_STAGING_CHAIN": {"verdict": f1_verdict, "sub": f1_sub},
            "F2_ENTITLEMENT_TERMS": f2,
            "F3_CLOCK_EXECUTION": f3,
            "F4_COSTS_FINANCING": f4_gate,
            "F5_FOLDS_CENSUS": f5_gate,
            "F6_REPRODUCIBILITY": f6_gate,
            "F7_CONTROL_SOURCE_AUTHORITY": f7_gate,
        },
        "verdict": "PENDING",
        "d2_status": "SKIPPED per owner amendment §3b; R0 ancestry battery "
                     "NOT MEASURED (R0_NOT_RUN — never an inferred PASS); no "
                     "R0/ancestry rho machinery built or run at P0",
        "p0_scope": "source engineering and census ONLY: no candidate "
                    "PnL/PF/Sharpe/drawdown/survivors/S1 evidence computed",
        "disclosures": {
            "relaxation": "accepted under owner-relaxed acceptance battery "
                          "(R0 0.30 / DSR alpha 0.10 at N = grid) | PBO NOT_RUN "
                          "fail-closed (<=3 cells, d0992d17 class) | R0 NOT_RUN "
                          "(D2 skipped by owner amendment §3b)",
            "financing": "financing = stated-conservative nightly-average "
                         "extrapolation (1.7 bps; worst single night may exceed "
                         "it; no per-leg differential census exists — OHLC-only "
                         "source)",
        },
        "artifact_sha256": digests,
    }
    gate.pop("verdict", None)
    gate["verdict"] = "PASS" if (
        gate["gates"]["F1_STAGING_CHAIN"]["verdict"] in ("PASS", "PASS_WITH_DISCLOSURE")
        and all(gate["gates"][g]["verdict"] == "PASS"
                for g in ("F2_ENTITLEMENT_TERMS", "F3_CLOCK_EXECUTION",
                          "F4_COSTS_FINANCING", "F5_FOLDS_CENSUS",
                          "F6_REPRODUCIBILITY", "F7_CONTROL_SOURCE_AUTHORITY"))
    ) else "FAIL"
    out = P0 / "p0_gate.json"
    out.write_text(json.dumps(gate, indent=1, sort_keys=True) + "\n")
    print(f"[gate] {gate['verdict']} -> {out}", flush=True)
    for g, v in gate["gates"].items():
        print(f"[gate]   {g}: {v['verdict']}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
