"""Artifact driver for lane L3_SPY_D1 (cycle PHASE-STRATEGY-V1).

Emits, deterministically (no wall-clock except data/manifest.json):
  data/manifest.json
  census/census.json, census/CENSUS.md
  proposals/proposals.json, proposals/PROPOSALS.md
  feasibility/ceiling.json

Outcome-blindness: this driver never computes a return, an equity curve or
any strategy PnL (plan section 7.3). All numbers are counts, shares, dwell
statistics, calendar/digest facts and cost-side arithmetic.
"""

import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path

LANE = Path(__file__).resolve().parent.parent
CODE = LANE / "code"
sys.path.insert(0, str(CODE))

from psv1_spy.snapshot import (  # noqa: E402
    SNAPSHOT_PATH,
    SNAPSHOT_SHA256,
    load_sessions,
    measure_calendar,
)
from psv1_spy.phase_rule import (  # noqa: E402
    ACCUMULATION,
    DISTRIBUTION,
    DOWNTREND,
    RuleParams,
    UNKNOWN,
    UPTREND,
    compute_labels,
    sensitivity_table,
)
from psv1_spy.census import fold_census, floor_margins  # noqa: E402
from psv1_spy.gates import weekday_rotation_replay  # noqa: E402
from psv1_spy import costs  # noqa: E402

FOLDS_ABS = [
    ("F1", "ERA-S1", 219, 1005),
    ("F2", "ERA-S2", 1006, 1510),
    ("F3", "ERA-S3", 1511, 2013),
    ("F4", "ERA-S4", 2014, 2942),
]
WARMUP = RuleParams().warmup  # 219


def jdump(obj, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(obj, f, indent=2, sort_keys=True, ensure_ascii=False)
        f.write("\n")


def pearson(a, b):
    ma = sum(a) / len(a)
    mb = sum(b) / len(b)
    va = sum((x - ma) ** 2 for x in a)
    vb = sum((x - mb) ** 2 for x in b)
    if va == 0 or vb == 0:
        return float("nan")
    cab = sum((x - ma) * (y - mb) for x, y in zip(a, b))
    return round(cab / (va ** 0.5 * vb ** 0.5), 6)


def calendar_class_rho(dates, sessions):
    """Measured cohesion of calendar-timing signal classes (dates only).
    Documents the ancestry foreclosure of calendar-timing books:
    - tom  = canonical month-settle (turn-of-month) window dummy
    - qopx = quarter-opex week dummy (5 sessions ending at the 3rd Friday
             of Mar/Jun/Sep/Dec)
    - exdv = dividend ex-date window dummy (+/-2 sessions around the 46
             measured ex-dividend steps)"""
    n = len(dates)
    tom = [0] * n
    for i, d in enumerate(dates):
        if i == n - 1 or dates[i + 1].month != d.month:
            tom[i] = 1
            for j in range(1, 4):
                if i + j < n:
                    tom[i + j] = 1

    def third_friday(y, m):
        d0 = date(y, m, 1)
        off = (4 - d0.weekday()) % 7
        return date(y, m, 1 + off + 14)

    opex_set = {third_friday(d.year, m) for d in dates for m in (3, 6, 9, 12)}
    qopx = [0] * n
    for i, d in enumerate(dates):
        if d in opex_set:
            for j in range(5):
                if i - j >= 0:
                    qopx[i - j] = 1
    cal = measure_calendar(sessions)
    exd = {st["date"] for st in cal["adjustment"]["steps"]}
    exdv = [0] * n
    for i, s in enumerate(sessions):
        if s.date in exd:
            for j in range(-2, 3):
                if 0 <= i + j < n:
                    exdv[i + j] = 1
    return {
        "definition": "Pearson rho of session-level dummy signal series (information-content correlation, pre-PnL, V2 D2 convention); post-warmup window",
        "rho_month_settle_vs_quarter_opex": pearson(tom[WARMUP:], qopx[WARMUP:]),
        "rho_month_settle_vs_exdiv_window": pearson(tom[WARMUP:], exdv[WARMUP:]),
        "rho_quarter_opex_vs_exdiv_window": pearson(qopx[WARMUP:], exdv[WARMUP:]),
        "note": "quarter-anchored timing subclasses (opex, dividend) form one correlated class (rho 0.56 > 0.20 bar); month-settle timing is a distinct subclass that is itself a measured-dead family (SFV3-A6-TOM-SETTLE)",
    }


def main() -> None:
    sessions = load_sessions()  # fail-closed digest verification
    cal = measure_calendar(sessions)
    dates_iso = [s.date for s in sessions]
    dates = [date.fromisoformat(d) for d in dates_iso]
    closes = [s.adjusted_close for s in sessions]

    # ---- data manifest -------------------------------------------------
    manifest = {
        "schema": "psv1_data_manifest@1",
        "cycle_id": "PHASE-STRATEGY-V1",
        "lane": "L3_SPY_D1",
        "snapshot": {
            "path": SNAPSHOT_PATH,
            "sha256": SNAPSHOT_SHA256,
            "digest_verified_at_load": True,
            "reuse_law": "read-only frozen snapshot; NO re-pull (plan section 9.2)",
            "extension_pre_2015": "NOT_RUN by default (plan section 9.2); no external data pulled",
        },
        "measured": dict(cal, measured_at_utc=datetime.now(timezone.utc).isoformat(timespec="seconds")),
        "price_series_choice": {
            "label_input": "adjusted_close",
            "reason": "dividend-adjusted, anchored to raw close at final session; removes mechanical ex-div gaps; structurally excludes the dividend-transition dead class from the label input",
            "raw_fields_present": ["open", "high", "low", "close", "volume"],
        },
        "calendar_law_frozen": {
            "decision": "session close VALUE of session d (date-only stamps measured in the file; no next-midnight convention present)",
            "fill": "next session open (next row of the session list)",
            "session_calendar": "XNYS sessions as present in the frozen bytes; measured 0 weekend sessions; gaps follow Fri->Mon and holiday closures",
            "intraday_execution": "NONE",
            "short_or_leverage": "FORBIDDEN (long/flat only, no owner authority for SPY short)",
        },
        "warmup_sessions": WARMUP,
        "first_post_warmup_session": dates_iso[WARMUP],
    }
    jdump(manifest, LANE / "data" / "manifest.json")

    # ---- labels + sensitivity ------------------------------------------
    labels = compute_labels(closes)
    sens = sensitivity_table(closes)
    post = labels[WARMUP:]
    cen = fold_census(post, [
        (fid, era, a - WARMUP, b - WARMUP) for fid, era, a, b in FOLDS_ABS
    ])
    floors = floor_margins(cen)

    # ---- calendar-defect gate (10.3a) ----------------------------------
    gate = weekday_rotation_replay(closes, dates_iso, FOLDS_ABS)

    rho = calendar_class_rho(dates, sessions)

    census_doc = {
        "schema": "psv1_census@1",
        "cycle_id": "PHASE-STRATEGY-V1",
        "lane": "L3_SPY_D1",
        "rule_id": "PSV1-SPYD1-QUAD-SMA200-SLOPE20",
        "price_input": "adjusted_close (dividend-adjusted)",
        "post_warmup_sessions": len(post),
        "census": cen,
        "floor_margins": floors,
        "floors_law": {
            "episodes_per_phase_per_cell_total": 20,
            "episodes_per_phase_per_fold": 3,
            "eligible_decisions_per_phase_per_fold": 100,
            "below_floor": "NOT_RUN_THIN_PHASE (slot FLAT, VALID result); never pooled with BTC cells",
        },
        "sensitivity_table": {
            "law": "single-notch perturbations are REPORTED, never optimized; parameters frozen in freezes/phase_rule_freeze.json before any label was computed on real history",
            "notches": sens,
            "min_agreement_observed": min(v["label_agreement_post_warmup"] for v in sens.values()),
        },
        "calendar_defect_gate": {
            "gate_10_3a_weekday_rotation_replay": gate,
            "gate_10_3b_tuesday_test": "executed in tests_py (synthetic defect-shape fixture); package runtime counter clock_attributable_force_flats is structurally 0 and asserted 0 there and by the hygiene test",
            "structural_no_flat_law": "no staleness/holding-duration flat law exists in the lane package; the only fill rule is target change (events.py); enforced by AST hygiene test",
            "calendar_law": manifest["calendar_law_frozen"],
        },
        "ancestry_measurements": rho,
        "verdicts": {},
    }

    # ---- verdicts --------------------------------------------------------
    named = (ACCUMULATION, UPTREND, DISTRIBUTION, DOWNTREND)
    verdicts = {}
    for p in named:
        verdicts[p] = {
            "floors_met": floors["phases"][p]["floors_met"],
            "slot": None,  # filled below
        }
    verdicts[UNKNOWN] = {
        "floors_met": None,
        "slot": "NO_ELIGIBLE_PROPOSAL",
        "reason": "by construction: TRANSITION_UNKNOWN is the explicit-uncertainty state; uncertainty maps to FLAT and never hosts a strategy slot (plan section 5)",
    }
    for p in named:
        if not floors["phases"][p]["floors_met"]:
            verdicts[p]["slot"] = "NOT_RUN_THIN_PHASE"
    if verdicts[UPTREND]["slot"] is None:
        verdicts[UPTREND]["slot"] = "NO_ELIGIBLE_PROPOSAL"
    census_doc["verdicts"] = verdicts
    jdump(census_doc, LANE / "census" / "census.json")

    # ---- proposals -------------------------------------------------------
    proposals = {
        "schema": "psv1_proposals@1",
        "cycle_id": "PHASE-STRATEGY-V1",
        "lane": "L3_SPY_D1",
        "cell": "SPY_D1",
        "direction_law": "SPY long/flat ONLY; short or leverage forbidden (no owner authority)",
        "proposal_count": 0,
        "phases": {
            ACCUMULATION: {
                "slot": verdicts[ACCUMULATION]["slot"],
                "floors": {
                    "episodes_cell_total": floors["phases"][ACCUMULATION]["episodes_cell_total"],
                    "episodes_per_fold": floors["phases"][ACCUMULATION]["episodes_per_fold"],
                    "eligible_decisions_per_fold": floors["phases"][ACCUMULATION]["eligible_decisions_per_fold"],
                },
                "reason": "below immutable floors (15 fold-local episodes < 20; fold decisions max 24 < 100). NOT_RUN_THIN_PHASE is a valid result; not pooled with any other cell.",
                "proposal": None,
            },
            UPTREND: {
                "slot": "NO_ELIGIBLE_PROPOSAL",
                "floors": {
                    "episodes_cell_total": floors["phases"][UPTREND]["episodes_cell_total"],
                    "episodes_per_fold": floors["phases"][UPTREND]["episodes_per_fold"],
                    "eligible_decisions_per_fold": floors["phases"][UPTREND]["eligible_decisions_per_fold"],
                },
                "reason": (
                    "Floors ARE met (margin +3 episodes; thin, F3 exactly at the fold floor). "
                    "No strategy is proposed because every economic-mechanism class expressible as a "
                    "long/flat book from this cell's own data (single-asset SPY OHLCV daily) is "
                    "forbidden or measured dead on this program: "
                    "(1) trend participation = phase-gated always-on-trend class, plan section 7.1 "
                    "(UP_TREND_SLOW_LONG; dead stocks family A5-SFV2-TREND-DEFENSIVE); "
                    "(2) mean-reversion = always-on-MR class, plan section 7.1 (ACC_RANGE_MR; dead "
                    "family SFV3-A5-IDIO-SHOCK-REVERSAL); "
                    "(3) calendar month-settle timing = measured-dead family SFV3-A6-TOM-SETTLE "
                    "(SCIENTIFIC_REJECTION, FAMILY_FAILURES.jsonl) - proposing it is a reopening, "
                    "independent of rho; "
                    "(4) quarter-anchored calendar timing (opex/buyback-window/dividend-transition) "
                    "= measured rho +0.559 vs the cell-reconstructed dividend ex-date window dummy "
                    "(> 0.20 bar) against the plan section 7.2 dead class dividend-transition books; "
                    "(5) volatility-state or participation conditioning = plan section 7.2 dead "
                    "classes and measured-dead families SFV4-A4-H1-SEMIVARIANCE-SHARE and "
                    "SFV4-A5-H1-PARTICIPATION-SHIFT; "
                    "(6) breadth/relative-rotation = plan section 7.2 dead class and requires QQQ "
                    "(not in this cell); "
                    "(7) single-name earnings/filing mechanisms = data-dead in this cell. "
                    "A phase-gated variant of any of these is the same mapping class (plan section 7.1) "
                    "and would be vetoed at integration; the lane declines rather than hazards it."
                ),
                "proposal": None,
            },
            DISTRIBUTION: {
                "slot": verdicts[DISTRIBUTION]["slot"],
                "floors": {
                    "episodes_cell_total": floors["phases"][DISTRIBUTION]["episodes_cell_total"],
                    "episodes_per_fold": floors["phases"][DISTRIBUTION]["episodes_per_fold"],
                    "eligible_decisions_per_fold": floors["phases"][DISTRIBUTION]["eligible_decisions_per_fold"],
                },
                "reason": "below immutable floors (5 episodes < 20; fold decisions max 22 < 100); additionally the plan section 6 stricter default applies: no short authority on SPY and no evidenced forced-counterparty long mechanism, so DISTRIBUTION defaults FLAT regardless.",
                "proposal": None,
            },
            DOWNTREND: {
                "slot": verdicts[DOWNTREND]["slot"],
                "floors": {
                    "episodes_cell_total": floors["phases"][DOWNTREND]["episodes_cell_total"],
                    "episodes_per_fold": floors["phases"][DOWNTREND]["episodes_per_fold"],
                    "eligible_decisions_per_fold": floors["phases"][DOWNTREND]["eligible_decisions_per_fold"],
                },
                "reason": "below immutable floors (11 episodes < 20; fold decisions 26/32/141/7, three folds < 100). Long/flat only: there is no long-side thesis in a markdown phase; short books are forbidden (DOWN_SHORT_BTC class / no SPY short authority) and risk-off-exit books are the SPARSE_RISK_OFF baseline class and DOWN_FLAT_RISKOFF specialist class, both forbidden as candidates.",
                "proposal": None,
            },
            UNKNOWN: {
                "slot": "NO_ELIGIBLE_PROPOSAL",
                "reason": "by construction: uncertainty state maps to FLAT, never a strategy slot.",
                "proposal": None,
            },
        },
        "ancestry_self_check": {
            "law": "plan section 7: rho bar 0.20 vs applicable frozen dead shadows; if a named dead shadow's signal is reconstructible from the cell's own data, measure it; otherwise NOT_MEASURED_WITH_REASON plus mechanism-class distance.",
            "named_dead_classes_stocks": {
                "relative_breadth_rotation": "rho NOT_MEASURED_WITH_REASON: shadow requires QQQ/SPY ratio; QQQ is not in this cell (single-asset snapshot); no candidate signal series exists in this lane to correlate.",
                "vol_state_bear_trap_books": "rho NOT_MEASURED_WITH_REASON: no frozen shadow series accessible to lanes; no candidate exists. Class distance: the frozen phase rule uses SMA level/slope only - no volatility conditioning anywhere in the rule or in any proposal.",
                "filing_event_amendment_cadence": "rho NOT_MEASURED_WITH_REASON: data-dead class; filing events are absent from the cell's data; no candidate exists.",
                "dividend_transition_books": "MEASURED (cell-constructed proxy): ex-date window dummy reconstructed from the 46 measured adjustment steps; rho(quarter-opex dummy, ex-div dummy) = +0.559 > 0.20, so any quarter-anchored calendar book would inherit the dead class's information and be ancestry-vetoed. Additionally the label input itself (adjusted_close) structurally contains ZERO dividend steps, so the dead class's signal is absent from this lane's own pipeline.",
            },
            "measured_calendar_class_rho": rho,
            "section_7_1_forbidden_check": "no proposed strategy exists; the lane confirms no RSM-V1 specialist, V2 arm, always-on MR/trend, or phase-gated variant of these was proposed or renamed.",
            "adjudication": "A1 adjudicates at integration (rubric E3).",
        },
    }
    jdump(proposals, LANE / "proposals" / "proposals.json")

    # ---- feasibility ceiling ----------------------------------------------
    trans = cen["transition_matrix_post_warmup"]
    up_exits = trans[UPTREND][UNKNOWN] + trans[UPTREND][ACCUMULATION] + trans[UPTREND][DISTRIBUTION] + trans[UPTREND][DOWNTREND]
    ceiling = {
        "schema": "psv1_ceiling@1",
        "cycle_id": "PHASE-STRATEGY-V1",
        "lane": "L3_SPY_D1",
        "scope": "plan section 11 pre-PnL feasibility; counts and cost arithmetic ONLY (no returns path exists in lane code)",
        "candidates": 0,
        "verdict": "NO_CANDIDATE_NO_PER_TRADE_ARITHMETIC_REQUIRED",
        "churn_bound": {
            "definition": "upper bound on position switches for any UPTREND-gated long book = UPTREND departures in the post-warmup transition matrix",
            "uptrend_departures_post_warmup": up_exits,
            "post_warmup_sessions": len(post),
            "annualized_switch_rate": round(up_exits / (len(post) / 251.0), 3),
            "phase_transitions_total_post_warmup": sum(
                trans[a][b] for a in trans for b in trans if a != b and trans[a][b] > 0
            ),
        },
        "cost_law_frozen": {
            "per_fill_bps": costs.PER_FILL_BPS,
            "round_trip_bps": costs.ROUND_TRIP_BPS,
            "tiers": list(costs.TIERS),
            "tier_multiplier_applies_to": "full stack",
            "reference_points": {
                f"{int(rt)}_round_trips": costs.tier_table(rt * 2, rt)
                for rt in (4, 8, 12, 26)
            },
            "note": "reference points are cost-side only; per-trade gross-edge margins require a candidate, and no candidate exists in this lane",
        },
        "no_op_law": "structural: the reducer fills only on target change; same-direction label noise produces zero fills (events.py; tested)",
        "per_phase": {
            p: {"slot": verdicts[p]["slot"] if p in verdicts else None}
            for p in (ACCUMULATION, UPTREND, DISTRIBUTION, DOWNTREND, UNKNOWN)
        },
    }
    jdump(ceiling, LANE / "feasibility" / "ceiling.json")

    # ---- markdown summaries ------------------------------------------------
    cm = []
    cm.append("# CENSUS — SPY_D1 (lane L3, cycle PHASE-STRATEGY-V1)\n")
    cm.append(f"Rule `PSV1-SPYD1-QUAD-SMA200-SLOPE20` on `adjusted_close`; warmup {WARMUP} sessions; "
              f"post-warmup window {len(post)} sessions "
              f"({dates_iso[WARMUP]} → {dates_iso[-1]}); folds = eras on session-index edges "
              f"(see freezes/era_fold_freeze.json).\n")
    cm.append("## Cell occupancy (post-warmup)\n")
    cm.append("| phase | occupancy | episodes (global / fold-local sum) | dwell median / max (sessions) |")
    cm.append("|---|---|---|---|")
    for p in (ACCUMULATION, UPTREND, DISTRIBUTION, DOWNTREND, UNKNOWN):
        c = cen["cell"][p]
        d = c["dwell_global"]
        cm.append(f"| {p} | {c['occupancy_share']:.2%} | {c['episode_count_global_runs']} / "
                  f"{c['episode_count_sum_of_folds']} | {d['median']} / {d['max']} |")
    cm.append("")
    cm.append(f"UNKNOWN share {cen['cell_unknown']['share']:.2%}; longest UNKNOWN run "
              f"{cen['cell_unknown']['longest_run']} sessions.\n")
    cm.append("## Floors (immutable 20 / 3 / 100) and verdicts\n")
    cm.append("| phase | episodes cell (floor 20) | episodes per fold (floor 3) | decisions per fold (floor 100) | verdict |")
    cm.append("|---|---|---|---|---|")
    for p in (ACCUMULATION, UPTREND, DISTRIBUTION, DOWNTREND):
        f = floors["phases"][p]
        eps = ", ".join(
            f"{k}:{v['value']}({v['margin']:+d})"
            for k, v in f["episodes_per_fold"].items()
        )
        dec = ", ".join(
            f"{k}:{v['value']}({v['margin']:+d})"
            for k, v in f["eligible_decisions_per_fold"].items()
        )
        cm.append(f"| {p} | {f['episodes_cell_total']['value']} ({f['episodes_cell_total']['margin']:+d}) | {eps} | {dec} | "
                  f"**{verdicts[p]['slot']}** |")
    cm.append(f"\n| {UNKNOWN} | n/a | n/a | n/a | **NO_ELIGIBLE_PROPOSAL** (uncertainty state by construction) |\n")
    cm.append("## Sensitivity (±1 notch, reported never optimized)\n")
    for k, v in sens.items():
        cm.append(f"- `{k}`: label agreement {v['label_agreement_post_warmup']:.4f}")
    cm.append("")
    cm.append("## Calendar-defect gate\n")
    cm.append(f"- Gate 10.3a weekday-rotation replay: **{'PASS' if gate['pass'] else 'FAIL'}** "
              f"(+1..+4 day date relabels; labels, per-fold occupancy and transitions invariant).")
    cm.append("- Gate 10.3b Tuesday test: PASS in tests_py (synthetic predecessor defect shape produces weekly "
              "Tuesday force-flats in the defective reference engine; this lane's pipeline produces ZERO "
              "weekday-attributable force-flats; `clock_attributable_force_flats == 0`).")
    cm.append("- Structural: no staleness/holding-duration flat law exists in the lane package.\n")
    cm.append("## Ancestry measurements (rho, pre-PnL)\n")
    cm.append(f"- month-settle vs quarter-opex dummies: rho {rho['rho_month_settle_vs_quarter_opex']:+.3f}")
    cm.append(f"- month-settle vs ex-div-window dummies: rho {rho['rho_month_settle_vs_exdiv_window']:+.3f}")
    cm.append(f"- quarter-opex vs ex-div-window dummies: rho {rho['rho_quarter_opex_vs_exdiv_window']:+.3f}")
    cm.append("\nQuarter-anchored timing subclasses form one correlated class (0.56 > 0.20 bar); month-settle "
              "timing is a measured-dead family (SFV3-A6-TOM-SETTLE). See proposals/proposals.json.\n")
    (LANE / "census" / "CENSUS.md").write_text("\n".join(cm) + "\n")

    pm = []
    pm.append("# PROPOSALS — SPY_D1 (lane L3, cycle PHASE-STRATEGY-V1)\n")
    pm.append("Direction law: **SPY long/flat ONLY** (no short/leverage authority).\n")
    pm.append("## Outcome: ZERO proposals frozen (proposal_count = 0)\n")
    pm.append("| phase | floors met | slot |")
    pm.append("|---|---|---|")
    for p in (ACCUMULATION, UPTREND, DISTRIBUTION, DOWNTREND, UNKNOWN):
        sl = verdicts[p]["slot"] if p in verdicts else "NO_ELIGIBLE_PROPOSAL"
        fm_ = floors["phases"][p]["floors_met"] if p in floors["phases"] else None
        pm.append(f"| {p} | {fm_} | **{sl}** |")
    pm.append("")
    pm.append("### Why the single data-sufficient phase (UPTREND) still carries no proposal\n")
    pm.append(proposals["phases"][UPTREND]["reason"])
    pm.append("")
    pm.append("### Thin phases\n")
    for p in (ACCUMULATION, DISTRIBUTION, DOWNTREND):
        pm.append(f"- **{p}**: {proposals['phases'][p]['reason']}")
    pm.append(f"- **{UNKNOWN}**: uncertainty state maps to FLAT by construction (plan section 5).\n")
    pm.append("### Ancestry self-check (plan section 7; A1 adjudicates)\n")
    for k, v in proposals["ancestry_self_check"]["named_dead_classes_stocks"].items():
        pm.append(f"- `{k}`: {v}")
    pm.append("")
    pm.append("Measured calendar-class cohesion rho (dates-only, pre-PnL): "
              f"month-settle↔quarter-opex {rho['rho_month_settle_vs_quarter_opex']:+.3f}, "
              f"month-settle↔ex-div {rho['rho_month_settle_vs_exdiv_window']:+.3f}, "
              f"quarter-opex↔ex-div {rho['rho_quarter_opex_vs_exdiv_window']:+.3f}.\n")
    pm.append("§7.1 check: no RSM-V1 specialist, V2 arm, always-on MR/trend, or phase-gated variant of these "
              "was proposed or renamed. The lane's negative is a mechanism-foreclosure result, not a PnL "
              "observation: no returns path exists in lane code.\n")
    (LANE / "proposals" / "PROPOSALS.md").write_text("\n".join(pm) + "\n")

    print("artifacts written under", LANE)
    print("gate 10.3a pass:", gate["pass"])
    print("verdicts:", {p: verdicts[p]["slot"] for p in verdicts})


if __name__ == "__main__":
    main()
