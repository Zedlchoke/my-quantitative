#!/usr/bin/env python3
"""Assemble a9f_feasibility_v15.json from a9f_measurements_raw.json.

Adds verdicts, margins-to-fail, identity checks (from the proposal files),
fold calendar statement, NOT_RUN declarations and compute estimates.
No PnL / returns / expectancy anywhere.
"""
import datetime as dt
import json
from pathlib import Path

WT = Path("/Users/hoangminhlong/my-quantitative/.worktrees/crypto/v15/d2-a9f-feasibility")
RAW = json.loads((WT / "research/control/v15_run/d2/a9f/a9f_measurements_raw.json").read_text())

P1D = {}
for lane in ("a4", "a5", "a6"):
    for p in ("P1", "P2"):
        P1D[f"{lane.upper()}-V15-{p}" if lane != "a4" else f"A4-V15-{p}"] = None  # placeholder

PROP_PATHS = {
    "A4-P1": WT / "research/control/v15_run/d1/a4/proposal_P1.json",
    "A4-P2": WT / "research/control/v15_run/d1/a4/proposal_P2.json",
    "A5-P1": WT / "research/control/v15_run/d1/a5/proposal_P1.json",
    "A5-P2": WT / "research/control/v15_run/d1/a5/proposal_P2.json",
    "A6-P1": WT / "research/control/v15_run/d1/a6/proposal_P1.json",
    "A6-P2": WT / "research/control/v15_run/d1/a6/proposal_P2.json",
}


def arm_identity(pid):
    """Read arm names + weight-construction strings from the frozen proposal
    file and verify pairwise distinctness."""
    j = json.loads(PROP_PATHS[pid].read_text())
    if pid.startswith("A4"):
        names = [j["anchor_spec"]["name"], j["neighbour_spec"]["name"], j["causal_control_spec"]["name"]]
        cons = [j["anchor_spec"]["book"], j["neighbour_spec"]["book"], j["causal_control_spec"]["construction"]]
    elif pid.startswith("A5"):
        names = [j["anchor_spec"]["name"], j["neighbour_spec"]["name"], j["causal_control_spec"]["name"]]
        cons = [j["anchor_spec"]["construction"], j["neighbour_spec"]["variant"], j["causal_control_spec"]["construction"]]
    else:
        names = [j["anchor_spec"]["arm_id"], j["neighbour_spec"]["arm_id"], j["causal_control_spec"]["arm_id"]]
        cons = [j["anchor_spec"]["feature"], j["neighbour_spec"]["variant"], j["causal_control_spec"]["variant"]]
    distinct = len(set(names)) == 3 and len(set(cons)) == 3
    return {"arm_names": names, "constructions_distinct": bool(distinct),
            "record_ids_pairwise_distinct": bool(len(set(names)) == 3)}


def cost_line(arm_key):
    c = RAW[arm_key]["cost"]
    return {k: c[k]["mean_cost_bps_of_gross_per_decision"] for k in
            ("base_tick_low", "base_tick_high", "stress_tick_low", "stress_tick_high")}


def summarize_arm(key, decision_dates):
    a = RAW[key]
    st = a["stats"]
    return {
        "decision_dates_S0": decision_dates,
        "decisions_with_book": int(sum(1 for x in st if x["gross"] > 1e-9)),
        "fills_S0": int(sum(x["fills"] for x in st)),
        "one_side_turnover": {
            "mean_frac_of_gross_per_decision": round(sum(x["one_side_turnover"] for x in st) / len(st), 4),
            "sum_frac_of_gross_over_S0": round(sum(x["one_side_turnover"] for x in st), 2),
        },
        "mean_gross": round(sum(x["gross"] for x in st) / len(st), 4),
        "per_fold": a["folds"],
        "break_even_gross_edge_bps_of_gross_per_decision": cost_line(key),
    }


A9F_COST_CEILING_STRESS_BPS = 5.0  # A9F-declared sanity ceiling (NOT frozen); margins reported so any line can be applied

OUT = {
    "schema": "v15_run_artifact_v1",
    "artifact": "a9f_feasibility_v15",
    "cycle": "CRYPTO-V15",
    "generated_utc": dt.datetime.now(dt.UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
    "producer_role": "A9F",
    "worktree": str(WT),
    "head_verified": "d078252a7c0f42b5a848b8fd97447be1c479d707",
    "scope": "pre-selection feasibility ONLY: decision counts, warmup coverage, turnover/cost structures, fold population, hole-refusal census, control identifiability/runnability. NO PnL, NO returns, NO expectancy of positions computed anywhere.",
    "fold_calendar_used": {
        "S0": ["2025-08-22", "2026-08-21"],
        "F0": ["2025-08-22", "2025-12-20"], "purge_1": ["2025-12-21", "2025-12-21"],
        "F1": ["2025-12-22", "2026-04-20"], "purge_2": ["2026-04-21", "2026-04-21"],
        "F2": ["2026-04-22", "2026-08-21"],
        "scored_daily_decision_dates": 363,
        "a6_five_day_grid_dates": 76,
        "note": "proposers' unanimous working thirds with 1-day purge (V12/V14 fold contract); A4/A5 state these thirds verbatim, A6 defers to the runner's frozen calendar; daily arms force-flat on each fold's last scored day; A6 grid includes an explicit force-flat entry at each fold's last day",
    },
    "staged_cell_semantics": {
        "missing_metrics_day_cells": "the 130 staging-refused (symbol,day) cells of amendment-1; grid-violation days are fully absent from parquet, parse_error days retain partial rows but the CELL was refused by the frozen integrity gate, so refused cells never feed features",
        "usable_metrics_days_per_symbol": 424,
        "defect_cells_per_symbol": {"ONGUSDT": 43, "ACEUSDT": 14, "BOMEUSDT": 5, "each_other_symbol": 4},
        "hole_rule": "feature window >10% missing metrics-day cells => that symbol-date decision REFUSED (amendment-1)",
    },
    "not_run_declarations": [
        {"item": "per-symbol native tick sizes for slippage", "status": "NOT_RUN",
         "reason": "no staged instrument config exists for the V15 universe (legacy catalog holds BTCUSDT/ETHUSDT perpetual metadata only; v15_data carries no exchangeInfo)",
         "treatment": "fee component exact per proposal assumptions (5.0 bps base / 7.5 bps stress); tick-slippage priced under a declared FALLBACK band of 0.5-2.0 bps of price per fill (stress adds the specified +2 ticks); break-even edges reported across the band so any tick assumption can be substituted"},
        {"item": "funding-cost drag on break-even edge", "status": "NOT_MEASURED",
         "reason": "no PnL anywhere in A9F; funding is booked separately per the frozen cost-once convention",
         "treatment": "reported break-even edges cover fill costs only and are therefore LOWER bounds on the true break-even edge"},
    ],
    "cost_ceiling_applied_by_a9f": {
        "bound": "break-even gross edge per decision at the stress tier <= 5.0 bps of gross considered sane",
        "authority": "A9F-declared (the freeze pins no numeric turnover ceiling); margins reported so any other line can be applied",
    },
    "compute_runtime": {
        "measured_full_feasibility_run_all_18_arms_seconds": 62,
        "estimate_scored_run_per_arm_seconds": "<90 (panel build dominates; PnL adds kline fill lookups only)",
        "estimate_full_6_family_x_3_arm_budget": "<30 min serialized, well inside machine limits",
    },
}

# ------------------------------------------------------------------ A4-P1
a = RAW["A4-P1:ANCHOR-churn28"]; n = RAW["A4-P1:NEIGH-churn56"]; c = RAW["A4-P1:CTL-rangec28"]
st_t = [x["one_side_turnover"] for x in a["stats"]]
OUT["A4-P1_REGSTAB"] = {
    "hypothesis_id": "A4-V15-P1", "family": "REGSTAB register-stability premium",
    "arms": {
        "anchor_REGSTAB-ANCHOR-churn28": summarize_arm("A4-P1:ANCHOR-churn28", 363),
        "neighbour_REGSTAB-NEIGH-churn56": summarize_arm("A4-P1:NEIGH-churn56", 363),
        "control_REGSTAB-CTL-VOLCHURN-PLACEBO": summarize_arm("A4-P1:CTL-rangec28", 363),
    },
    "warmup": {
        "claim_checked": "first decision 2025-08-22 reading metrics <= 2025-08-19; churn28 needs 29 observations (28 changes), churn56 needs 57",
        "measured": {k: RAW["WARMUP_VERIFICATION"][k] for k in
                     ("A4-P1_anchor_churn28_needs_29_obs", "A4-P1_neighbour_churn56_needs_57_obs")},
        "claim_verdict": "correct for the anchor; the neighbour's 57-observation requirement is not stated in the proposal's warmup_spec but IS satisfied at the first decision",
    },
    "refusal_census": {**RAW["A4-P1:REFUSALS"],
                       "fold_population_impact": "no decision date lost in any fold; eligible names never drop below 18/20 on any decision date (3 fold-last force-flat days are contractual, not refusals)",
                       "denominator_note": "symbol_date_denominator uses the 20-symbol universe x 363 days"},
    "control_runnability": {
        "decision_count_vs_anchor": "363/363 = 100% (>= 60% required)",
        "panel": c["panel_diag"],
        "control_feature_vs_anchor_feature_pooled_spearman_rho": RAW["A4-P1:IDENTITY"]["control_vs_anchor_feature_spearman_rho"],
        "CONTROL_SELF_SUBSUMPTION_RISK": RAW["A4-P1:IDENTITY"]["flag"],
    },
    "identity_check": {**arm_identity("A4-P1"), "universe": "20 symbols, matches frozen universe"},
    "margins_to_fail": {
        "warmup_anchor_margin_usable_obs": 30,
        "warmup_neighbour_margin_usable_obs": 2,
        "warmup_neighbour_note": "THIN: 2 usable observations above the requirement at the first decision; any additional pre-S0 staging hole would break the neighbour's first-decision support",
        "cost_ceiling_stress_high_bps": {"measured": cost_line("A4-P1:ANCHOR-churn28")["stress_tick_high"],
                                          "ceiling": A9F_COST_CEILING_STRESS_BPS,
                                          "margin": round(A9F_COST_CEILING_STRESS_BPS - cost_line("A4-P1:ANCHOR-churn28")["stress_tick_high"], 2)},
        "control_rho_margin": {"measured": RAW["A4-P1:IDENTITY"]["control_vs_anchor_feature_spearman_rho"],
                                "bound": 0.95, "margin": round(0.95 - abs(RAW["A4-P1:IDENTITY"]["control_vs_anchor_feature_spearman_rho"]), 4)},
        "fold_decision_days": {"measured_min": 120, "bound": 20, "margin": 100},
    },
    "verdict": "RUNNABLE",
    "verdict_note": "all measured bounds sane; warmup margin thin only for the neighbour (2 usable obs); turnover low (mean one-side 6.7% of gross per decision); break-even edge 0.37-0.64 bps/decision across base-to-stress band",
}

# ------------------------------------------------------------------ A4-P2
am = RAW["A4-P2:ANCHOR-fadeP90-h5"]["event_meta"]
cm = RAW["A4-P2:CTL-priceshock"]["event_meta"]
OUT["A4-P2_REGSHOCK"] = {
    "hypothesis_id": "A4-V15-P2", "family": "REGSHOCK register-shock fade",
    "arms": {
        "anchor_REGSHOCK-ANCHOR-fadeP90-h5": {**summarize_arm("A4-P2:ANCHOR-fadeP90-h5", 363),
                                               "event_structure": am},
        "neighbour_REGSHOCK-NEIGH-fadeP90-h10": {**summarize_arm("A4-P2:NEIGH-fadeP90-h10", 363),
                                                  "event_structure": RAW["A4-P2:NEIGH-fadeP90-h10"]["event_meta"]},
        "control_REGSHOCK-CTL-PRICESHOCK-PLACEBO": {**summarize_arm("A4-P2:CTL-priceshock", 363),
                                                     "event_structure": cm},
    },
    "warmup": {"claim_checked": "42 changes + event day = 43 observations ending D-3; claimed first decision 2025-08-22",
                "measured": RAW["WARMUP_VERIFICATION"]["A4-P2_anchor_P90_43_obs"],
                "claim_verdict": "correct; proposal's own '~700+ symbol-events' estimate confirmed (782 measured)"},
    "refusal_census": {
        "events_fired": am["events_fired"], "events_refused_by_hole_rule": am["events_refused_by_hole_rule"],
        "refused_share": round(am["events_refused_by_hole_rule"] / am["events_fired"], 4),
        "cluster": "all refusals in the ONGUSDT 2026-03 and 2026-07/08 defect clusters",
        "fold_population_impact": "entries per fold 139/137/124 (anchor), all 20 symbols receive entries; drop-one symbol and fold both non-vacuous",
        "capacity_findings": "400 of 782 fired events become entries: 52 blocked by the 10-position concurrency cap, the rest by the one-position-per-symbol rule during 5-day holds; mean concurrent 5.39, max 10; the proposal's fold-population claim survives (400 entries >> fold needs)",
    },
    "control_runnability": {
        "control_entries_vs_anchor": f"{cm['entries']}/{am['entries']} = {round(cm['entries']/am['entries'],3)} (>= 0.60 required)",
        "control_feature": "price TR% shocks from staged klines (distinct field BY DESIGN - price-only placebo)",
        "CONTROL_SELF_SUBSUMPTION_RISK": "N/A - different information source by construction",
    },
    "identity_check": {**arm_identity("A4-P2"), "universe": "20 symbols, matches frozen universe"},
    "margins_to_fail": {
        "warmup_margin_usable_obs": 16,
        "cost_ceiling_stress_high_bps": {"measured": cost_line("A4-P2:ANCHOR-fadeP90-h5")["stress_tick_high"],
                                          "ceiling": A9F_COST_CEILING_STRESS_BPS,
                                          "margin": round(A9F_COST_CEILING_STRESS_BPS - cost_line("A4-P2:ANCHOR-fadeP90-h5")["stress_tick_high"], 2)},
        "entries_per_fold_min": {"measured": 124, "bound": 20, "margin": 104},
        "stress_delay_note": "the +1-day stress delay moves the effective event lag to 4 days; the book still runs mechanically at lag 4 (events still flag), so stress remains runnable as specified",
    },
    "verdict": "RUNNABLE",
    "verdict_note": "event rate, fold population, drop-one viability and control all measured sane; break-even edge 0.58-1.00 bps/decision; capacity constraint absorbs 49% of fired events but leaves 400 entries across all 20 symbols and all folds",
}

# ------------------------------------------------------------------ A5-P1
OUT["A5-P1_ELITE-SIZE-ASYM"] = {
    "hypothesis_id": "A5-V15-P1", "family": "ELITE-SIZE-ASYM",
    "arms": {
        "anchor_ELITE-SIZE-ASYM-ANCHOR": summarize_arm("A5-P1:ANCHOR", 363),
        "neighbour_ELITE-SIZE-ASYM-NB10Q": summarize_arm("A5-P1:NEIGH-Q5", 363),
        "control_CTL-ELITELEVEL": summarize_arm("A5-P1:CTL-ELITELEVEL", 363),
    },
    "warmup": {"claim_checked": "5 usable rows [D-7,D-3]; first decision needs metrics from 2025-08-15; neighbour 10 rows [D-12,D-3]",
                "measured": {k: RAW["WARMUP_VERIFICATION"][k] for k in ("A5-P1_anchor_5_rows", "A5-P1_neighbour_10_rows")},
                "claim_verdict": "correct"},
    "spec_ambiguity_flags": [
        {"flag": "AMBIGUITY_UNIVERSE_19_VS_20",
         "detail": "proposal lists 19 symbols (SOLUSDT absent) while its own entry rule says 'rank the 20 symbols' and its 7/6/7 tercile split requires 20 names; per the freeze ambiguity_rule this returns to A1 before implementation",
         "measured_impact": "decision counts identical either way; S0 one-side turnover identical to 4 decimals (14 held names in both readings); feasibility verdict invariant to the resolution"},
        {"flag": "MIN_TRADE_THRESHOLD_NON_BINDING",
         "detail": "the 0.05 min-trade threshold cannot ever suppress a trade: every possible per-name weight change is a multiple of the 0.0714 weight step (>= 0.05); the micro-turnover suppression it claims is decorative"},
        {"flag": "FAIL_CLOSED_VS_AMENDMENT_CONFLICT",
         "detail": "proposal's fail_closed says an under-window symbol is 'excluded from the cross-section, weights renormalized'; amendment-1 says >10% missing window cells REFUSE the symbol-date (no position, no fill). A9F applied the amendment (refusal) as the binding ex-ante semantics; on affected days the cross-section shrinks instead of renormalizing"},
    ],
    "refusal_census": {**RAW["A5-P1:REFUSALS"],
                       "fold_population_impact": "13 of 363 decision dates have an empty book: 10 from the global hole clusters (2025-08-29 -> 2025-09-01..05, 2026-08-12 -> 2026-08-15..19, where every symbol's 5-row window contains the refused cell) plus 3 partial-cluster days where eligible names fall below the 14 needed for the 7/7 sides; refusal clusters concentrate in ONGUSDT (92) and ACEUSDT (49)",
                       "denominator_note": "refusal_summary denominator uses 20x363; true listed universe is 19x363 (conservative)"},
    "control_runnability": {
        "decision_count_vs_anchor": "363/363 = 100% (>= 60% required)",
        "panel": RAW["A5-P1:CTL-ELITELEVEL"]["panel_diag"],
        "control_feature_vs_anchor_feature_pooled_spearman_rho": RAW["A5-P1:IDENTITY"]["control_vs_anchor_feature_spearman_rho"],
        "CONTROL_SELF_SUBSUMPTION_RISK": RAW["A5-P1:IDENTITY"]["flag"],
    },
    "identity_check": {**arm_identity("A5-P1"),
                       "universe": "19 symbols as listed (SOLUSDT absent) - see AMBIGUITY_UNIVERSE_19_VS_20"},
    "margins_to_fail": {
        "warmup_margin_usable_obs": 54,
        "cost_ceiling_stress_high_bps": {"measured": cost_line("A5-P1:ANCHOR")["stress_tick_high"],
                                          "ceiling": A9F_COST_CEILING_STRESS_BPS,
                                          "margin": round(A9F_COST_CEILING_STRESS_BPS - cost_line("A5-P1:ANCHOR")["stress_tick_high"], 2)},
        "control_rho_margin": {"measured": RAW["A5-P1:IDENTITY"]["control_vs_anchor_feature_spearman_rho"],
                                "bound": 0.95, "margin": round(0.95 - abs(RAW["A5-P1:IDENTITY"]["control_vs_anchor_feature_spearman_rho"]), 4)},
        "empty_book_days": {"measured": 13, "bound": "none frozen; fold scored-day bound 20 per fold", "margin_folds": "min fold scored days 120 vs bound 20 => margin 100"},
    },
    "verdict": "RUNNABLE",
    "verdict_note": "runnable after the universe ambiguity is resolved by A1; measured structure sane (turnover 8.0%/decision, break-even 0.44-0.76 bps/decision, control valid at rho -0.654)",
}

# ------------------------------------------------------------------ A5-P2
fm = RAW["A5-P2:ANCHOR"]["fire_meta"]
OUT["A5-P2_CROWD-LATE-CHURN"] = {
    "hypothesis_id": "A5-V15-P2", "family": "CROWD-LATE-CHURN",
    "arms": {
        "anchor_CROWD-LATE-CHURN-ANCHOR": {**summarize_arm("A5-P2:ANCHOR", 363), "fire_meta": fm},
        "neighbour_CROWD-LATE-CHURN-NB-POSVEL": {**summarize_arm("A5-P2:NEIGH-POSVEL", 363),
                                                  "fire_meta": RAW["A5-P2:NEIGH-POSVEL"]["fire_meta"]},
        "control_CTL-CROWDVEL-UNGATED": {**summarize_arm("A5-P2:CTL-UNGATED", 363),
                                          "fire_meta": RAW["A5-P2:CTL-UNGATED"]["fire_meta"]},
    },
    "warmup": {"claim_checked": "endpoints D-23 and D-3 usable; first decision needs metrics from 2025-07-30",
                "measured": RAW["WARMUP_VERIFICATION"]["A5-P2_anchor_2_endpoint_rows_span21"],
                "claim_verdict": "correct"},
    "decisive_measurement": {
        "bound": "the proposal's OWN falsification item 8 (drop-one fold non-vacuity): fired set empty on MORE THAN 50% of a fold's decision days = REJECTED ex ante",
        "measured_empty_fraction_by_fold": fm["empty_fraction_by_fold"],
        "anchor_days_fired_S0": fm["days_fired"], "of": 363,
        "mean_fired_names_when_fired": fm["mean_fired_names_when_fired"],
        "margin_to_fail_pp_by_fold": {f: round(100 * (fm["empty_fraction_by_fold"][f] - 0.5), 1) for f in ("F0", "F1", "F2")},
        "interpretation": "the elite non-confirmation gate (|v_top| < 0.5|v_glob|) almost never passes among the top-5 |v_glob| names: the anchor book is empty on 78.7-87.5% of every fold's decision days, breaching the 50% bound in ALL THREE folds. The rejection is structural (measured on features only, no PnL): scoring the cell would burn a budget slot to discover a guaranteed gate-8 kill",
        "name_day_concentration_when_fired": fm["name_day_concentration_top3"],
        "concentration_note": "gate-6 concentration is NOT the binding finding (top symbol 22.2% of fired name-days < 0.70); the non-vacuity breach is",
    },
    "refusal_census": {**RAW["A5-P2:REFUSALS"],
                       "fold_population_impact": "170 symbol-dates refused (2.3%); NOT the cause of the anchor's emptiness - the emptiness is the gate arithmetic itself",
                       "denominator_note": "refusal_summary denominator uses 20x363; true listed universe is 19x363 (conservative)"},
    "control_runnability": {
        "control_days_fired": 357, "of": 363, "mean_names_per_fire_day": RAW["A5-P2:CTL-UNGATED"]["fire_meta"]["mean_fired_names_when_fired"],
        "decision_count_vs_anchor": "357 fire-days vs anchor 61 => control runs at 585% of the anchor's fire count (>= 60% requirement met with huge margin)",
        "CONTROL_SELF_SUBSUMPTION_RISK": "OK (control is the ungated superset by design; it fires far more often than the anchor, which is the anchor's defect, not the control's)",
        "neighbour_contrast": "the NB-POSVEL neighbour (position-velocity gate) fires 347/363 days - the anchor's account-count gate is the sole binding constraint; the neighbour as a separate arm is runnable",
    },
    "identity_check": {**arm_identity("A5-P2"),
                       "universe": "19 symbols as listed (SOLUSDT absent) - same ambiguity flag as A5-P1"},
    "margins_to_fail": {
        "nonvacuity_margin_pp_by_fold": {f: round(100 * (fm["empty_fraction_by_fold"][f] - 0.5), 1) for f in ("F0", "F1", "F2")},
        "warmup_margin_usable_obs": 57,
        "fold_scored_days_margin": {"measured_min": 120, "bound": 20, "margin": 100},
    },
    "verdict": "INFEASIBLE_ANCHOR_FOLD_NONVACUITY",
    "verdict_note": "mechanically computable, but the anchor as specified is guaranteed rejected by the proposal's own preregistered falsification item 8 in all three folds (empty fired set on 78.7-87.5% of fold decision days vs the 50% bound; margins +28.7/+37.5/+33.5 pp). The control and neighbour arms run fine - the defect is the anchor's gate population",
}

# ------------------------------------------------------------------ A6-P1 / A6-P2
for pid, label, extra in [
    ("A6-P1", "taker-aggression saturation per unit of positioning churn",
     {"control_rho": RAW["A6-P1:IDENTITY"]["control_vs_anchor_feature_spearman_rho"],
      "self_subsumption_flag": RAW["A6-P1:IDENTITY"]["flag"],
      "stress_high_cost": cost_line("A6-P1:ANCHOR")["stress_tick_high"]}),
    ("A6-P2", "top-trader positioning change per unit of ambient taker aggression",
     {"control_rho": RAW["A6-P2:IDENTITY"]["control_vs_anchor_feature_spearman_rho"],
      "self_subsumption_flag": RAW["A6-P2:IDENTITY"]["flag"],
      "stress_high_cost": cost_line("A6-P2:ANCHOR")["stress_tick_high"]}),
]:
    anchor_key = f"{pid}:ANCHOR"
    a = RAW[anchor_key]
    OUT[f"{pid}_RATIO-OF-RATIO"] = {
        "hypothesis_id": pid.replace("A6-", "A6-V15-"), "family": label,
        "arms": {
            "anchor": summarize_arm(anchor_key, 76),
            "neighbour_W20": summarize_arm(f"{pid}:NEIGH-W20", 76),
            "control": summarize_arm(f"{pid}:CTL", 76),
        },
        "warmup": {"claim_checked": "anchor 10 daily aggregates [D-12,D-3]; neighbour 20 [D-23,D-3]; first F0 decision 2025-08-22",
                    "measured": {k: RAW["WARMUP_VERIFICATION"][k] for k in ("A6_anchor_W10", "A6_neighbour_W20")},
                    "claim_verdict": "correct"},
        "refusal_census": {"P1_anchor_W10": RAW["A6:REFUSALS"]["P1_anchor_W10"],
                            "P1_neigh_W20": RAW["A6:REFUSALS"]["P1_neigh_W20"],
                            "fold_population_impact": "4 forced-flat cycles measured (2025-09-01, 2025-09-06, 2026-08-15, 2026-08-20): any W10 window containing a global hole day has only 9 usable daily aggregates, so <10 eligible names triggers the proposal's own flat-cycle rule; all other 72 grid dates carry a full 10-vs-10 book",
                            "denominator": "76 decision dates x 20 symbols"},
        "control_runnability": {
            "decision_count_vs_anchor": "76/76 = 100% (>= 60% required)",
            "panel": a["panel_diag"],
            "control_feature_vs_anchor_feature_pooled_spearman_rho": extra["control_rho"],
            "n_symbol_dates_in_rho": RAW[f"{pid}:IDENTITY"]["n_symbol_dates"],
            "CONTROL_SELF_SUBSUMPTION_RISK": extra["self_subsumption_flag"],
        },
        "identity_check": arm_identity(pid) | {"universe": "20 symbols, matches frozen universe"},
        "margins_to_fail": {
            "warmup_margin_usable_obs": 49,
            "cost_ceiling_stress_high_bps": {"measured": extra["stress_high_cost"],
                                              "ceiling": A9F_COST_CEILING_STRESS_BPS,
                                              "margin": round(A9F_COST_CEILING_STRESS_BPS - extra["stress_high_cost"], 2)},
            "control_rho_margin": {"measured": extra["control_rho"], "bound": 0.95,
                                    "margin": round(0.95 - abs(extra["control_rho"]), 4)},
            "flat_cycles": {"measured": a["flat_cycles_lt10_eligible"], "bound": "none frozen (proposal's own <10-names flat rule)", "fold_scored_days_margin": "min fold grid dates 24 vs A5-style bound 20 => margin 4 (A6 grid is the thinnest fold population in the budget)"},
        },
    }

OUT["A6-P1_RATIO-OF-RATIO"]["verdict"] = "RUNNABLE"
OUT["A6-P1_RATIO-OF-RATIO"]["verdict_note"] = (
    "thin bounds named: (1) stress-tier break-even edge 4.36 bps/decision vs the A9F-declared 5.0 ceiling => margin +0.64 (fee-exact component; the tick band is a fallback, break-even at fee-only is 2.30 bps/decision); "
    "(2) control rho 0.8256 < 0.95 => margin +0.124, the highest control-anchor correlation among the valid controls, meaning the churn denominator reorders tails but not the body; "
    "(3) A6 grid dates 76 => thinnest decision population in the budget. All frozen bounds pass")

OUT["A6-P2_RATIO-OF-RATIO"]["verdict"] = "INFEASIBLE_CONTROL_SELF_SUBSUMPTION"
OUT["A6-P2_RATIO-OF-RATIO"]["verdict_note"] = (
    "measured pooled Spearman rho(anchor R = g/(A_abs+0.01), control raw g) = "
    f"{RAW['A6-P2:IDENTITY']['control_vs_anchor_feature_spearman_rho']} over "
    f"{RAW['A6-P2:IDENTITY']['n_symbol_dates']} symbol-dates, above the 0.95 flag line by "
    f"{round(RAW['A6-P2:IDENTITY']['control_vs_anchor_feature_spearman_rho'] - 0.95, 4)}. "
    "The aggression denominator is a positive scalar with insufficient cross-sectional dispersion to reorder the ranking: the control book is a near-clone of the anchor book. Under the preregistered non-reproduction rule EVERY outcome then kills the family: anchor expectancy > 0 => near-clone control also > 0 and >= 0.5 x anchor => FALSIFIED_BY_CONTROL; anchor expectancy <= 0 => MECHANISM_DEAD. The falsification apparatus cannot return 'survive'; void by measured construction. Independent second thinness: stress-tier break-even edge 5.95 bps/decision already exceeds the A9F-declared 5.0 ceiling (margin -0.95)")

OUT["verdict_summary"] = {
    "A4-P1_REGSTAB": "RUNNABLE",
    "A4-P2_REGSHOCK": "RUNNABLE",
    "A5-P1_ELITE-SIZE-ASYM": "RUNNABLE (with AMBIGUITY_UNIVERSE_19_VS_20 returning to A1)",
    "A5-P2_CROWD-LATE-CHURN": "INFEASIBLE_ANCHOR_FOLD_NONVACUITY",
    "A6-P1": "RUNNABLE (thin cost + control-rho margins named)",
    "A6-P2": "INFEASIBLE_CONTROL_SELF_SUBSUMPTION",
    "budget_implication": "4 proposals fully runnable; 2 infeasible on measured, pre-PnL, structural grounds; both infeasibilities are exactly the failure classes the D2 gates exist to catch before scoring",
}

# sanity assertions before writing
assert abs(sum(x["one_side_turnover"] for x in RAW["A4-P1:ANCHOR-churn28"]["stats"]) - 24.3) < 1.0
assert RAW["A5-P2:ANCHOR"]["fire_meta"]["days_fired"] == 61
assert RAW["A6-P2:IDENTITY"]["control_vs_anchor_feature_spearman_rho"] > 0.95

out_path = WT / "research/control/v15_run/d2/a9f/a9f_feasibility_v15.json"
out_path.write_text(json.dumps(OUT, indent=1, sort_keys=False) + "\n")
print(f"written {out_path} ({out_path.stat().st_size} bytes)")
for k, v in OUT["verdict_summary"].items():
    if k != "budget_implication":
        print(f"  {k}: {v}")
