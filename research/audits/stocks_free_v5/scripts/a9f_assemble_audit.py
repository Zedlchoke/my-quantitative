"""Assemble the A9-F feasibility audit artifact (schema stocks_free_v5_run/a9_f_feasibility_audit@1).

Merges the schedule, SEC feature/coverage, and price-arm measurements into the
final audit JSON. No PnL anywhere.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

HERE = "."
sched = json.load(open("schedule_out.json"))
sec = json.load(open("sec_features_out.json"))
price = json.load(open("price_arms_out.json"))

NOW = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

# ---- shared schedule facts ---------------------------------------------------
fold_block = {
    "s0_sessions_measured": sched["s0"]["n_sessions"],
    "s0_window": "2018-04-04..2025-07-31 (matches all proposals' declared 1842)",
    "folds": {
        fid: {
            "declared": next(f"{a}..{b}" for f, a, b in [(
                "S0_FOLD_1", "2018-04-04", "2020-09-01")] if f == fid) if fid == "S0_FOLD_1"
            else ("2020-09-10..2023-02-09" if fid == "S0_FOLD_2" else "2023-02-17..2025-07-24"),
            "n_sessions_measured": v["n_sessions"],
            "first": v["first"],
            "last": v["last"],
        }
        for fid, v in sched["folds"].items()
    },
    "fold_gap_sessions_inside_s0": sched["fold_gaps"],
    "quarterly_63_clock": {
        "used_by": ["a4_h1", "a4_h2", "a5_h1", "a5_h2"],
        "ticks_per_fold": {k: v["n_ticks"] for k, v in sched["quarterly_clock_63"]["per_fold"].items()},
        "total_ticks": sched["quarterly_clock_63"]["total_ticks"],
        "every_tick_inside_exactly_one_fold": sched["quarterly_clock_63"]["every_tick_inside_exactly_one_fold"],
        "fold_offsets": "0,63,...,567 (10/fold; each fold 609 sessions >= 568 required)",
        "final_tick_truncated_hold": True,
        "meets_min_30_total": True,
        "meets_min_5_per_fold": True,
    },
    "global_42_clock": {
        "used_by": ["a6_h1", "a6_h2"],
        "n_slots": sched["global_clock_42"]["n_slots"],
        "per_fold_scored": sched["global_clock_42"]["per_fold_scored"],
        "slots_outside_all_folds": sched["global_clock_42"]["slots_outside_all_folds"],
        "all_slots_inside_exactly_one_fold": sched["global_clock_42"]["all_slots_inside_exactly_one_fold"],
        "meets_min_30_total": sched["global_clock_42"]["meets_30_total"],
        "meets_min_5_per_fold": sched["global_clock_42"]["meets_5_per_fold"],
    },
    "etf_leg_history_facts": {
        "XLC_inception": "2018-06-19",
        "XLC_21_sessions": sched["xlc_eligibility"]["21_sessions"],
        "XLC_63_sessions": sched["xlc_eligibility"]["63_sessions"],
        "XLC_252_sessions": sched["xlc_eligibility"]["252_sessions"],
        "XLRE_first_session": sched["etf_history"]["XLRE"]["first"],
        "XLRE_252_sessions_from": sched["xlre_252_eligible_from"],
        "note": "XLRE has >= 252 sessions of adjusted history from 2016-10-07, i.e. BEFORE S0 start; only XLC is history-delayed inside S0",
    },
    "benchmark": {
        "instrument": "SPY _all adjusted path",
        "coverage": "2010-01-04..2026-08-27",
        "covers_all_quarterly_ticks": sched["benchmark_spy_all"]["covers_all_quarterly_ticks"],
        "covers_all_42grid_slots": sched["benchmark_spy_all"]["covers_all_42grid_slots"],
        "pre_s0_252_runway_starts": sched["benchmark_spy_all"]["covers_pre_s0_252_runway_start"],
    },
}

# ---- per-proposal entries ----------------------------------------------------

def elig_vector(arm):
    return [x["n_eligible"] for x in arm["per_tick"]]

a4h1, a4h2, a5h1, a6h1 = sec["a4_h1"], sec["a4_h2"], sec["a5_h1"], sec["a6_h1"]
a5h2, a6h2 = price["a5_h2"], price["a6_h2"]

def count_ge(vec, k):
    return sum(1 for n in vec if n >= k)

v_a4h1 = elig_vector(a4h1)
v_a4h2 = elig_vector(a4h2)
v_a5h1 = elig_vector(a5h1)
v_a6h1 = elig_vector(a6h1)

RISKS_COMMON_SEC = "single-vintage newest-effective-date coverage: the sector observation is pinned to the newest fiscal period end present in the panel, which is usually an off-cycle filer's period end with a 1-5 filer cohort; coverage at that vintage is structurally low regardless of panel-wide data availability (census pre-S0 fractions are about ANY record, not about the newest-vintage cohort)"

proposals = {}

proposals["a4_h1"] = {
    "hypothesis_id": "SFV5-A4-H1-BSHEXPANSION",
    "verdict": "INFEASIBLE",
    "verdict_basis": "feature build-through impossible under the proposal's own declared gates: 0 rank-eligible sectors at EVERY one of the 30 decision ticks (declared: '>= 9 sectors eligible at every tick'); the declared 'zero-margin honesty' rule (10 scored ticks per fold, any lost tick kills the floor) is therefore triggered at maximum severity",
    "schedule": {"feasible": True, "detail": "30 ticks (10/fold), all inside exactly one fold; t-252s reference sessions exist on the frozen calendar (first tick 2018-04-04 -> 2017-04-03 pre-S0; proposal said '~2017-04-05')"},
    "warmup": {
        "history_before_first_slot": True,
        "detail": "census-certified pre-S0 availability recomputed and CONFIRMED (us-gaap:Assets pre-S0 fractions 0.80-1.00 per sector, matching packet census exactly); history exists, but the first slot's DECLARED gates still empty the rank set (see feature_build_through)",
    },
    "feature_build_through": {
        "canonical_bridge_used": "research/assets/stocks/pit_conditioning.py conditioning_panel/aggregate_sector_asof, field us-gaap:Assets, max_filing_gap_days=400, 410-filer frozen panel",
        "store_sha256_verified": sec["store_sha_match"],
        "declared_gates": a4h1["declared_gates"],
        "measured_eligible_sectors_per_tick": v_a4h1,
        "min_eligible": a4h1["min_elig"],
        "ticks_with_ge_9_eligible": count_ge(v_a4h1, 9),
        "ticks_with_ge_6_eligible": count_ge(v_a4h1, 6),
        "root_causes_measured": {
            "coverage_gate_b": "newest-single-vintage coverage < 0.60 at 60.0% of sector-ticks (t side) and more at the t-252s reference side; median newest-vintage cohort = 15 of 40 filers",
            "coherence_gate_c": "endpoint effective-date coherence (<= 100 calendar days between t and t-252s vintages) fails at nearly every sector-tick: the single-vintage effective date advances by ~91-366 days across a 252-session differencing lag, so the 100-day cap is structurally unsatisfiable for an annual/quarterly-vintage aggregate",
        },
        "coverage_table_t_side": price["cov_a4h1_tick"],
        "coverage_table_ref252_side": price["cov_a4h1_ref252"],
        "per_sector_floor_breaches": "every one of the 11 sectors drops below the 0.60 floor at 2-30 of 30 ticks (t side)",
    },
    "identifiability": {
        "status": "NOT_EVALUABLE",
        "detail": "declared kill thresholds (mean |Spearman| <= 0.40 AND max |rho| <= 0.60; CAN-FIRE with >= 5 control-book membership changes; >= 9 eligible at every tick) cannot be applied because the anchor and control rank vectors never contain >= 3 sectors at any tick",
        "measured_mean_abs_rho": None,
        "measured_max_abs_rho": None,
        "eligible_set_never_reaches_declared_9": True,
    },
    "turnover": {
        "estimable": False,
        "detail": "no book can form at any tick, so measured churn is undefined; the design-level upper bound (full 3+3 reconstitution every tick) is ~8.7/yr two-way vs the 6.0 ceiling, and the declared expected 1.1-2.4/yr is unattainable because the rank set is empty",
    },
    "breadth_cap_gross_net": {
        "legs_per_decision": "0 measured (declared 6; K=min(3,floor(N/3)) degenerate)",
        "gross_cap": "1.0 declared, well-formed",
        "dollar_neutral": "3v3 at +/-1/6 nets to 0 as declared (arithmetic identity), but unattainable with an empty rank set",
    },
    "implementation_risks_top3": [
        "FATAL (measured): declared eligibility gates (b) coverage>=0.60 at both endpoints and (c) 100-day endpoint-vintage coherence are jointly unsatisfiable on the real panel; the family cannot form a book at any of the 30 declared ticks",
        RISKS_COMMON_SEC,
        "panel-composition drift and XLC leg delay are secondary and immaterial given the fatal gate infeasibility",
    ],
    "notes": [
        "The census ('fundable = pre-S0 availability fraction >= 0.80') certifies data EXISTENCE, not single-vintage coverage at the newest effective date; the proposal's claim 'exactly what the coverage census certifies' conflates the two.",
        "No reparameterisation may be proposed post hoc (proposal's own rule); the family dies in feasibility as specified.",
    ],
}

proposals["a4_h2"] = {
    "hypothesis_id": "SFV5-A4-H2-CASHINTENSITY",
    "verdict": "INFEASIBLE",
    "verdict_basis": "declared non-emptiness gate fails by measurement: eligible sectors >= 9 at 0 of 30 ticks (max 7, min 0); 3+3 baskets can form at only 4 of 30 ticks -> scored decisions far below the frozen floor of 30 (and the proposal's own zero-margin rule)",
    "schedule": {"feasible": True, "detail": "same 30-tick quarterly clock; all ticks inside exactly one fold"},
    "warmup": {
        "history_before_first_slot": True,
        "detail": "cash and assets pre-S0 availability recomputed (0.70-1.00) and matching the packet census; XLF's declared cash failure (0.70 < 0.80) confirmed",
    },
    "feature_build_through": {
        "canonical_bridge_used": "conditioning_panel for us-gaap:CashAndCashEquivalentsAtCarryingValue and us-gaap:Assets, gap 400, ratio-of-means key CI=M_cash/M_assets",
        "store_sha256_verified": sec["store_sha_match"],
        "declared_gates": a4h2["declared_gates"],
        "measured_eligible_sectors_per_tick": v_a4h2,
        "min_eligible": a4h2["min_elig"],
        "ticks_with_ge_9_eligible": count_ge(v_a4h2, 9),
        "ticks_with_ge_6_eligible": count_ge(v_a4h2, 6),
        "coverage_table": price["cov_a4h2"],
        "per_sector_floor_breaches": "every sector drops below the 0.60 both-fields floor at 2-30 of 30 ticks; XLF is ex-ante census-excluded as declared",
    },
    "identifiability": {
        "status": "NOT_IDENTIFIABLE_AS_DECLARED",
        "declared": "mean |rho| <= 0.40 AND max |rho| <= 0.60; CAN-FIRE; >= 9 eligible anchor+control every tick, >= 8 neighbour",
        "measured_mean_abs_rho": a4h2["rho_mean_abs"],
        "measured_max_abs_rho": a4h2["rho_max_abs"],
        "measured_on": "degenerate eligible sets of 3-7 sectors only (sets of 9-10 never occur); numbers are reported for completeness, the eligibility failure is primary",
        "neighbour_min_eligible": a4h2["neighbour_min_eligible"],
        "gate_neighbour_ge_8": a4h2["gate_neighbour_ge_8"],
        "control_membership_changes_total": a4h2["control_book_membership_changes_total"],
        "detail": "where measurable, mean |rho| 0.5328 > 0.40 and max |rho| 0.80 > 0.60 caps are exceeded; the >= 9-eligible precondition itself never holds",
    },
    "turnover": {
        "estimable": False,
        "detail": "books form at only 4/30 ticks; design upper bound ~8.7/yr two-way (full reconstitution) vs 6.0 ceiling; declared 0.9-2.0/yr unattainable",
    },
    "breadth_cap_gross_net": {
        "legs_per_decision": "3+3 declared at +/-1/6 (net 0) but forms at only 4/30 ticks; K degenerates to 1 at N in {3,4,5}",
        "gross_cap": "1.0 declared, well-formed",
    },
    "implementation_risks_top3": [
        "FATAL (measured): the same single-vintage coverage + effective-date-coherence gates as A4-H1 (here coherence between the cash and assets vintages) empty the rank set; >= 9 eligible never occurs",
        RISKS_COMMON_SEC,
        "two-field vintage skew makes the 100-day coherence gate even harder than A4-H1's single-field endpoint gate (cash and assets effective dates differ per filer reporting habit)",
    ],
    "notes": [
        "XLF census exclusion (cash 0.70) and XLC leg delay measured and confirmed as declared; immaterial given the fatal coverage infeasibility.",
    ],
}

proposals["a5_h1"] = {
    "hypothesis_id": "SFV5-A5-H1",
    "verdict": "INFEASIBLE",
    "verdict_basis": "3v3 book can form at ZERO of 30 decision ticks (max eligible 5, min 0; 3v3 needs >= 6): the dei:EntityPublicFloat panel's newest single vintage is an off-cycle filer's fiscal year-end with 1-5 filers, so the declared 0.60 coverage floor fails almost everywhere; scored-decision floor unreachable",
    "schedule": {"feasible": True, "detail": "30-tick quarterly clock OK; 21-session leg rule puts XLC in from 2018-07-19 (tick 3 onward) as declared ('~2018-07')"},
    "warmup": {
        "history_before_first_slot": True,
        "detail": "float and LSE pre-S0 availability recomputed (0.80-1.00 and 0.80-1.00) and matching the packet census (the packet census core list contains LiabilitiesAndStockholdersEquity even though the d1 packet's core_fields excerpt does not; the p2 audit A7_warmup_coverage numbers confirm >= 0.80 for all 11 sectors exactly as the proposal cites); history exists but per-tick vintage coverage fails",
    },
    "feature_build_through": {
        "canonical_bridge_used": "conditioning_panel for dei:EntityPublicFloat and us-gaap:LiabilitiesAndStockholdersEquity, gap 550, ratio-of-aggregates key R = mean_float/mean_lse",
        "store_sha256_verified": sec["store_sha_match"],
        "declared_gates": a5h1["declared_gates"],
        "measured_eligible_sectors_per_tick": v_a5h1,
        "min_eligible": a5h1["min_elig"],
        "ticks_with_ge_6_eligible": count_ge(v_a5h1, 6),
        "coverage_table": price["cov_a5h1"],
        "per_sector_floor_breaches": "every sector below the 0.60 floor at 16-30 of 30 ticks; the float (annual 10-K cover-page fact) is the binding side: its newest effective date is a single filer's FY-end, so coverage is 0.025-0.1 at most ticks",
    },
    "identifiability": {
        "status": "NOT_EVALUABLE",
        "declared": "Spearman(anchor, control) <= 0.90 at decision slots AND >= 25% of slots with >= 1 differing long/short membership leg",
        "measured_mean_abs_rho": a5h1["rho_mean_abs"],
        "measured_max_abs_rho": a5h1["rho_max_abs"],
        "measured_divergence_fraction": a5h1["divergence_fraction"],
        "detail": "measurable at only 9/30 ticks and on 2-5 sector sets (mean |rho| 0.6444, max 1.0, divergence 16.67% < 25%); all numbers are degenerate-set artifacts - the primary failure is that the books never form",
    },
    "turnover": {
        "estimable": False,
        "detail": "no 3v3 book forms at any tick; declared ~3.8/yr base estimate unattainable; design upper bound ~8.7/yr",
    },
    "breadth_cap_gross_net": {
        "legs_per_decision": "declared exactly 6 non-CASH legs; measured 0 at every tick (max eligible 5 < 6)",
        "gross_cap": "1.0 declared, well-formed; net 0 by arithmetic",
    },
    "implementation_risks_top3": [
        "FATAL (measured): EntityPublicFloat is an annual cover-page fact; the canonical single-vintage bridge pins the sector observation to the newest FY-end present (one off-cycle filer), so the 0.60 floor fails at ~all sector-ticks",
        RISKS_COMMON_SEC,
        "the LSE denominator side alone would often pass (coverage 0.75-0.95 at many ticks), which shows the failure is field-specific vintage pinning, not store-wide absence - relevant only for any future re-design, not for rescuing this proposal",
    ],
    "notes": [
        "The proposal's preregistered non-emptiness assumption ('Both fields are census-fundable (>= 0.80) in all 11 sectors pre-S0, so floor breaches are not expected') is falsified by measurement: fundability and per-tick vintage coverage are different objects.",
    ],
}

proposals["a6_h1"] = {
    "hypothesis_id": "SFV5-A6-H1",
    "verdict": "INFEASIBLE",
    "verdict_basis": "declared skip rule ('fewer than 6 eligible sectors -> decision skipped and not scored') fires at 42 of 44 grid slots: max eligible 7, min 0, eligible >= 6 at only 2 slots -> ~2 scored decisions vs the >= 30 floor; the proposal's own prose acknowledges A9-F must verify this arithmetic and the verification fails",
    "schedule": {"feasible": True, "detail": "44-slot 42-session grid; every slot inside exactly one fold (15/15/14 per fold); no slot falls in the fold gaps"},
    "warmup": {
        "history_before_first_slot": True,
        "detail": "AssetsCurrent and Assets pre-S0 availability recomputed (0.20-1.00; XLF 0.25 and XLRE 0.20 fail as declared) and matching the packet census; 252-session beta runway available pre-S0; but per-tick vintage coverage fails the 0.40 per-leg floor",
    },
    "feature_build_through": {
        "canonical_bridge_used": "conditioning_panel for us-gaap:AssetsCurrent and us-gaap:Assets, gap 200, ratio key WCINT = mean(AssetsCurrent)/mean(Assets), per-leg floor 0.40, census-9 sector set",
        "store_sha256_verified": sec["store_sha_match"],
        "declared_gates": a6h1["declared_gates"],
        "measured_eligible_sectors_per_tick": v_a6h1,
        "min_eligible": a6h1["min_elig"],
        "ticks_with_ge_6_eligible": count_ge(v_a6h1, 6),
        "coverage_table": price["cov_a6h1"],
        "per_sector_floor_breaches": "even at the relaxed 0.40 per-leg floor: XLB below floor at 29/44 slots, XLI 40/44, XLK 43/44, XLP 44/44, XLV 40/44, XLY 42/44; only XLE (8) and XLU (9) ever pass reliably",
        "gap_200_side_effect": "the declared 200-day filing clock additionally prunes annual-only AssetsCurrent filers between 10-K stamps, compounding the vintage pinning",
    },
    "identifiability": {
        "status": "NOT_EVALUABLE_AS_DECLARED",
        "declared": "kill if mean |rho| >= 0.60 across decision sessions OR >= 2 of 3 legs share the same side in >= 70% of sessions",
        "measured_mean_abs_rho": a6h1["rho_mean_abs"],
        "measured_max_abs_rho": a6h1["rho_max_abs"],
        "long_overlap_ge2_fraction": a6h1["long_overlap_ge2_fraction"],
        "short_overlap_ge2_fraction": a6h1["short_overlap_ge2_fraction"],
        "detail": "measured on 2-7 sector sets (mean |rho| 0.5543 < 0.60 and side-sharing 0.75/0.75 would nominally exceed 0.70, but 2-of-3-of-3 legs is ill-defined on sets smaller than 3); numbers are degenerate-set artifacts, not a clean pass or kill",
    },
    "turnover": {
        "estimable": False,
        "detail": "books form at 2/44 slots; declared 0.8-2.2/yr unattainable; design upper bound ~13.3/yr (full reconstitution at ~6.0 ticks/yr + hedge bound 0.25/rebalance + boundaries) vs 6.0 ceiling",
    },
    "breadth_cap_gross_net": {
        "legs_per_decision": "declared 6 sector legs + 1 SPY hedge + CASH; measured eligible set >= 6 at only 2/44 slots",
        "gross_cap": "declared 1.25 = 1.0 legs + |hedge| <= 0.25; arithmetic well-formed (equality only at the hedge truncation bound)",
        "cash_reconciliation": "cash = 1 - net with net = w_SPY in [-0.25, 0.25]: identity well-defined as declared",
    },
    "implementation_risks_top3": [
        "FATAL (measured): 0.40 per-leg coverage floor fails at nearly every slot for most sectors under the declared gap 200; the skip rule then destroys the scored-sample floor",
        RISKS_COMMON_SEC,
        "declared prose/rule mismatch on the early rank set: prose says 7 sectors {no XLC, no XLV}, but the written rule (census-9 AND >= 252-session history) yields 8 early because XLV has full price history from 2010-01-04; the rule text governs, the prose is wrong (immaterial given the fatal coverage failure)",
    ],
    "notes": [
        "A6-H1's drop-one claim ('7 eligible early -> drop leaves exactly 6') inherits the same prose error; under the written rule it would be 8 -> 7.",
    ],
}

proposals["a5_h2"] = {
    "hypothesis_id": "SFV5-A5-H2",
    "verdict": "FEASIBLE_WITH_NOTES",
    "verdict_basis": "schedule, warmup, feature computation, overlay computability, stale-control constructibility, benchmark coverage and floors all verified on the real snapshot; the preregistered control-identifiability check PASSES on the divergence leg (90% >= 25%) and on the mean reading of rho (0.759 <= 0.90) but FAILS on a strict per-slot-max reading (max 0.9545 > 0.90 at 6/30 slots) - the declared threshold text does not specify mean vs max, so identifiability is CONDITIONAL on that one-word adjudication",
    "schedule": {
        "feasible": True,
        "detail": "30 quarterly ticks (10/fold, all inside exactly one fold); >= 30 total and >= 5/fold floors met exactly",
        "warmup_63_sessions_before_first_slot": True,
        "detail2": "S0 start has >= 63 pre-S0 SPY-calendar runway sessions (runway to 2010-01-04); the 63-session realized-vol window at the first tick is fully inside the authorized pre-S0 path",
    },
    "feature_computation": {
        "inputs": "{SYM}_all adjusted closes for the 11 sector ETFs + SPY calendar only; no SEC fields (as declared)",
        "measured_sigma63_annualized_at_first_tick": a5h2["sigma63_scale_sample_first_tick"],
        "sanity": "63-session realized vols 16.2-25.0% annualized across the 10 sectors eligible at 2018-04-04 - plausible sector-ETF levels; ranks well-defined, no ties observed in the sample",
        "leg_eligibility": "XLC enters 2018-09-18 (63 sessions after 2018-06-19 inception) - matches the declared '~2018-09'; 10 sectors at ticks 1-2, 11 thereafter (measured)",
    },
    "overlay_computability": {
        "declared": "c_t = min(1, 0.10/sigma_book_ann(t)); sigma_book_ann = sqrt(252*mean(r_book(u)^2, u in t-62..t)) on the UNSCALED anchor book; banded DOWN floor(10c)/10; recomputed only at slots; gross = c <= 1.0",
        "computable_from_snapshot_alone": True,
        "detail": "the unscaled book's weights between slots are a deterministic function of the rank series (measured); its daily returns over t-62..t are therefore computable from the same adjusted closes (no external data; NOT computed here - no PnL)",
        "first_slot_convention_pin_required": "at the first S0 slot the book has no prior return history under a force-flat-before-S0 reading: sigma_book = 0 -> 0.10/0 = +inf (IEEE) -> c = 1.0; alternatively a pre-S0 paper-book convention (data available to 2010-01-04) also resolves it; either is computable but the implementation MUST pin one ex ante",
        "banded_down_only": "floor(10*c)/10 is well-defined; c can rise across slots only via full 0.10 band steps (rounding direction is always down)",
        "c_zero_reachability": "c_t = 0 requires sigma_book_ann >= 200% and the effective c floor 0.1 requires >= 100% annualized book vol - unreachable for a gross-1.0 sector spread book (constituent vols measured 16-25% ann, spread-book vol is a fraction of that); the declared c=0 'legitimate flat state' is theoretically open but practically moot, so the min-positions invariant tension is theoretical only",
    },
    "identifiability": {
        "status": "CONDITIONAL",
        "declared": "(i) Spearman(anchor ranks, stale t-63 ranks) <= 0.90 at decision slots; (ii) >= 25% of slots with >= 1 differing long/short membership leg; kill if either fails",
        "measured_mean_abs_rho": a5h2["rho_mean_abs"],
        "measured_max_abs_rho": a5h2["rho_max_abs"],
        "slots_above_0.90": 6,
        "slots_total": 30,
        "measured_divergence_fraction": a5h2["divergence_fraction"],
        "gate_divergence": "PASS (90% >> 25%)",
        "gate_rho_mean_reading": "PASS (0.759 <= 0.90)",
        "gate_rho_max_reading": "FAIL (0.9545 > 0.90; 6/30 slots above 0.90)",
        "verdict_note": "the V4 L7 kills cited means (0.78-0.83), which supports the mean reading; but the text is unqualified - owner adjudication required BEFORE selection; the stale control is constructible at every tick (t-63 references exist for all 30 ticks, verified on the calendar) and the stale book genuinely diverges in membership at 27/30 slots, so the control CAN identify timeliness wherever the mean reading is accepted",
    },
    "turnover": {
        "ceiling": 6.0,
        "measured_membership_churn": {
            "legs_changed_per_transition": a5h2["anchor_legs_changed_per_transition"],
            "mean": 1.655,
            "max": 3,
        },
        "estimate_components_per_year": {
            "rebalance_mid_measured": 2.26,
            "rebalance_max_measured_path": 4.096,
            "overlay_band_declared_mid_0.3_per_slot": 1.23,
            "overlay_band_declared_max_0.4_per_slot": 1.64,
            "boundary_builds_flats_rebuilds_upper": 0.82,
        },
        "plausible_mid_total": 4.3,
        "adverse_total_measured_max_churn_plus_max_overlay": 6.6,
        "design_upper_bound_full_reconstitution": price["turnover_design_upper_bounds"]["quarterly_3v3_full_reconstitution_per_year"],
        "verdict": "inside the 6.0 ceiling under plausible fill assumptions (~4.3/yr mid, ~72% of ceiling); marginal breach (6.6/yr) only on the measured-max-churn path COMBINED with max overlay moves - consistent with the proposal's own 'headroom is thin BY DESIGN' declaration and its accepted falsification surface",
        "convention_note": "upper-bound estimate as instructed; |delta w| per replaced leg = 2 x 1/6 (exit+entry); no intraperiod rebalancing; overlay trades only at slots",
    },
    "breadth_cap_gross_net": {
        "legs_per_decision": "6 non-CASH legs in the base book at every scored tick (measured eligible 10-11 >= 6)",
        "gross": "c_t <= 1.0 by construction; net = 0 (3 x +1/6 + 3 x -1/6, scaled identically); cash absorbs 1 - net",
        "overlay_flat_state": "declared legitimate by the proposal; practically unreachable (see overlay_computability)",
    },
    "benchmark": {"covered": True, "detail": "SPY _all covers 2010-01-04..2026-08-27, superset of every slot and the 252-session risk-match runway"},
    "implementation_risks_top3": [
        "identifiability threshold ambiguity (mean vs max rho): 0.759 vs 0.9545 against the 0.90 cap - must be adjudicated before selection, not after",
        "turnover headroom is thin by design: measured-churn mid ~4.3/yr rises to ~6.6/yr on the max-churn path with max overlay movement; a ceiling breach is a live outcome, pre-declared as falsification",
        "first-slot overlay convention (flat-before-S0 -> c=1.0 vs pre-S0 paper book) must be pinned ex ante; both are computable from the snapshot",
    ],
    "notes": [
        "Confirmatory Section 1.1 family: the audit expresses no view on the raw V4 shadow number; all A7-N ancestry measurements (|rho| <= 0.20 vs the V4 semivariance shape anchor) remain A7-N's duty and were NOT in this audit's scope.",
    ],
}

proposals["a6_h2"] = {
    "hypothesis_id": "SFV5-A6-H2",
    "verdict": "FEASIBLE",
    "verdict_basis": "all feasibility checks pass on the real snapshot: 44-slot schedule inside folds with 15/15/14 scored slots (floors met), control identifiable by its own declared thresholds (mean |rho| 0.2818 < 0.60; 2-of-3-leg same-side sharing 18.2% long / 20.5% short, both < 70%), skip rule never triggered (min eligible 10), measured-churn turnover ~3.2-4.0/yr two-way inside the 6.0 ceiling, gross cap and cash identities well-formed, benchmark covers all slots",
    "schedule": {
        "feasible": True,
        "detail": "42-session global grid from S0 offset 0; 44 slots; all inside exactly one fold (no slot in the 15 fold-gap sessions); 15/15/14 scored slots per fold (>= 5/fold, >= 30 total)",
    },
    "warmup": {
        "history_before_first_slot": True,
        "detail": "252-session beta window and nested 63-session correlation window fully inside the pre-S0 runway (to 2010-01-04) at the first slot",
    },
    "feature_computation": {
        "inputs": "{SYM}_all adjusted closes (returns for coupling key, betas, and future portfolio returns) and {SYM}_none raw close for the declared nominal-price placebo only - exactly as declared",
        "leg_eligibility_rule_as_written": ">= 252 sessions of adjusted history through d -> 10 sectors eligible from S0 start (all but XLC), 11 from 2019-06-20",
        "narrative_error_note": "the proposal prose claims '9 sectors eligible from S0 start (XLC and XLRE join at ~2019-06)': measured XLRE has 252 sessions by 2016-10-07 (series starts 2015-10-08), so XLRE is eligible from S0 start and only XLC joins in-sample; the WRITTEN rule is deterministic and was used - no feasibility impact, but the prose must not be implemented literally",
        "min_eligible_measured": a6h2["min_eligible"],
        "gate_skip_never_triggered": a6h2["gate_skip_never_triggered"],
    },
    "identifiability": {
        "status": "IDENTIFIABLE",
        "declared": "kill if mean |rho| >= 0.60 across decision sessions OR >= 2 of 3 legs share the same side in >= 70% of sessions",
        "measured_mean_abs_rho": a6h2["rho_mean_abs"],
        "measured_max_abs_rho": a6h2["rho_max_abs"],
        "long_overlap_ge2_fraction": a6h2["long_overlap_ge2_fraction"],
        "short_overlap_ge2_fraction": a6h2["short_overlap_ge2_fraction"],
        "gate_mean_below_0.60": True,
        "gate_side_sharing_below_0.70": True,
        "detail": "the scale-invariance argument holds empirically: the nominal-price placebo shares only 18-20% of slots with >= 2 common basket legs; the control is a live, distinct falsification surface",
    },
    "turnover": {
        "ceiling": 6.0,
        "measured_membership_churn": {
            "legs_changed_per_transition": a6h2["anchor_legs_changed_per_transition"],
            "mean": 1.535,
            "max": 3,
        },
        "estimate_components_per_year": {
            "rebalance_mid_measured": 3.074,
            "rebalance_max_measured_path": 6.008,
            "hedge_leg_bound": "measured |dw_hedge| would require the arm's weight history (not computed); hard upper bound 0.25 per rebalance -> 1.5/yr, realistic drift well under 0.3/yr",
            "boundary_builds_flats_rebuilds_upper": 0.82,
        },
        "plausible_mid_total": 4.0,
        "design_upper_bound_full_reconstitution": price["turnover_design_upper_bounds"]["grid42_3v3_full_reconstitution_per_year"],
        "verdict": "inside the ceiling under plausible assumptions (~4.0/yr, ~67%); the measured-max-churn path alone touches 6.0/yr before boundaries - the declared falsification surface",
    },
    "breadth_cap_gross_net": {
        "legs_per_decision": "6 sector legs + 1 SPY hedge + CASH at every slot (eligible 10-11 measured)",
        "gross_cap": "1.0 + |hedge| <= 1.25, equality only at the hedge truncation bound",
        "dollar_neutral": "declared net = w_SPY in [-0.25, 0.25] (hedge design, not dollar-neutral) - consistent with the frozen accounting identity cash = 1 - net",
    },
    "benchmark": {"covered": True, "detail": "SPY _all covers every slot and the 252-session runway"},
    "implementation_risks_top3": [
        "eligibility prose/rule mismatch (XLRE): implementing the prose ('9 from S0 start') instead of the written rule would silently drop a legitimately eligible sector - pin the rule",
        "42-grid cadence gives ~6.0 rebalances/yr: turnover headroom against the 6.0 ceiling is the thinnest of the six proposals on the measured-max path (6.0/yr before hedge and boundaries)",
        "pairwise-correlation key is undefined-pair-excluding as declared; with eligible sets of 10-11 the >= 5-defined-pairs floor never binds (measured), but a frozen implementation must still carry the rule for degradation",
    ],
    "notes": [
        "The declared A7-N checks (vs variance ranks, trailing momentum, dollar-volume shock, semivariance share) are A7-N's scope and were not measured here; the anchor-vs-placebo identifiability measurement required of A9-F is done and PASSES.",
    ],
}

# ---- assemble ----------------------------------------------------------------

audit = {
    "schema": "stocks_free_v5_run/a9_f_feasibility_audit@1",
    "produced_by": "A9-F (independent feasibility auditor)",
    "cycle": "STOCKS-FREE-V5",
    "phase": "V5-D2",
    "produced_at_utc": NOW,
    "worktree": ".worktrees/stocks-free-v5/d2-a9-feasibility",
    "branch": "orca/stocks-free-v5-d2-a9-feasibility",
    "no_pnl_statement": "no strategy PnL, expectancy, PF, alpha or drawdown was computed anywhere in this audit; all measurements are PIT feature/rank arithmetic, deterministic book-weight schedules used only for churn counting, closed-form turnover arithmetic, and schedule/census verification",
    "inputs_verified": {
        "sec_store_sha256": sec["store_sha256_measured"],
        "sec_store_sha256_matches_declaration": sec["store_sha_match"],
        "sec_store_records_scanned": sec["sec_store"]["records_scanned"],
        "field_record_counts": sec["sec_store"]["records_fields_of_interest"],
        "panel_filers_mapped": sec["panel_filers_mapped"],
        "packet_census_recomputation": "pre-S0 availability fractions recomputed for all five proposal fields x 11 sectors: ZERO mismatches vs d1_proposal_packet coverage_census and p2_pit_data_audit_sec A7_warmup_coverage",
        "snapshot": "12 symbols, _all + _none paths, SPY_none_p1 session calendar (4188 sessions 2010-01-04..2026-08-27)",
        "canonical_bridge": "research/assets/stocks/pit_conditioning.py used unmodified (conditioning_panel / aggregate_sector_asof / session_gate_utc)",
    },
    "summary": {
        "a4_h1": "INFEASIBLE - 0 rank-eligible sectors at all 30 ticks (declared >= 9)",
        "a4_h2": "INFEASIBLE - max 7 eligible, never >= 9; 3v3 forms at 4/30 ticks",
        "a5_h1": "INFEASIBLE - max 5 eligible; 3v3 forms at 0/30 ticks",
        "a6_h1": "INFEASIBLE - skip rule fires at 42/44 slots; ~2 scored decisions vs floor 30",
        "a5_h2": "FEASIBLE_WITH_NOTES - identifiability conditional on mean-vs-max rho adjudication (0.759 vs 0.9545 vs cap 0.90); turnover headroom thin by design",
        "a6_h2": "FEASIBLE - control identifiable (mean |rho| 0.282), turnover ~4.0/yr, floors met",
        "selectable_families": ["a5_h2 (conditional)", "a6_h2"],
    },
    "root_cause_cross_cutting": {
        "finding": "All four SEC-conditioned proposals (A4-H1, A4-H2, A5-H1, A6-H1) share one fatal, measured infeasibility: the canonical bridge is single-vintage BY DESIGN (one effective date per sector per call = the newest fiscal period end with a gated record), so a sector's observation is pinned to the newest-vintage cohort, which is typically 1-15 filers sharing an off-cycle period end. The declared per-observation coverage floors (0.60, or 0.40 per leg) fail at 60-100% of sector-ticks, the proposals' 'cross-section never empties / >= 9 eligible at every tick' claims are falsified, and A4-H1's additional 100-day endpoint-vintage coherence gate is structurally unsatisfiable at a 252-session differencing lag (vintages advance ~91-366 days per year).",
        "evidence": {
            "median_newest_vintage_cohort_assets_gap400": price["single_vintage_cohort_stats_assets400"]["median_filers_in_newest_vintage"],
            "fraction_sector_ticks_below_60pct_coverage": price["single_vintage_cohort_stats_assets400"]["fraction_sector_ticks_below_60pct"],
            "census_vs_coverage_distinction": "census 'fundable' = filer has ANY pre-S0 record (recomputed, matches packet exactly); it does NOT measure newest-vintage cohort size, which is what the floors bind on",
        },
        "scope_note": "this is a proposal-level feasibility finding under the frozen no-retuning discipline (aggregation_declaration and gates are frozen ex ante); A1 selection must treat these four families as failing the feasibility gate, and any future re-design is a NEW family proposal, not a repair",
    },
    "schedule_feasibility": fold_block,
    "proposals": proposals,
    "artifacts": {
        "scripts": [
            "research/audits/stocks_free_v5/scripts/a9f_lib.py",
            "research/audits/stocks_free_v5/scripts/a9f_schedule.py",
            "research/audits/stocks_free_v5/scripts/a9f_sec_features.py",
            "research/audits/stocks_free_v5/scripts/a9f_price_arms.py",
            "research/audits/stocks_free_v5/scripts/a9f_assemble_audit.py",
        ],
        "raw_measurements": [
            "research/audits/stocks_free_v5/scripts/schedule_out.json",
            "research/audits/stocks_free_v5/scripts/sec_features_out.json",
            "research/audits/stocks_free_v5/scripts/price_arms_out.json",
        ],
    },
}

with open("../a9_f_feasibility_audit.json", "w") as fh:
    json.dump(audit, fh, indent=1)
print("wrote a9_f_feasibility_audit.json")
for k, v in audit["summary"].items():
    print(f"  {k}: {v}")
