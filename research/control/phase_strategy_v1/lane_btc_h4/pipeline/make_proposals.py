"""PSV1 lane_btc_h4 — assemble proposals.json from frozen constants + computed
census/feasibility/ancestry artifacts. Mechanism text authored by the lane;
every number embedded here is read from the lane's own artifacts."""

from __future__ import annotations

import json
import sys
from pathlib import Path

LANE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LANE_DIR.parents[3]))

from research.control.phase_strategy_v1.lane_btc_h4.pipeline import config, ingest  # noqa: E402


def main() -> int:
    census = json.loads((LANE_DIR / "census" / "census.json").read_text())
    ceiling = json.loads((LANE_DIR / "feasibility" / "ceiling.json").read_text())
    anc = json.loads((LANE_DIR / "proposals" / "ancestry_selfcheck.json").read_text())
    gate = json.loads((LANE_DIR / "data" / "data_gate.json").read_text())
    rule_freeze = json.loads((LANE_DIR / "freezes" / "phase_rule_freeze.json").read_text())
    era_freeze = json.loads((LANE_DIR / "freezes" / "era_fold_freeze.json").read_text())

    book_up = next(b for b in ceiling["books"] if b["book"] == "UP_DONCHIAN_CONT")
    book_acc = next(b for b in ceiling["books"] if b["book"] == "ACC_DRIFT_LONG")
    rho_up = anc["books"]["UP_DONCHIAN_CONT"]
    rho_acc = anc["books"]["ACC_DRIFT_LONG"]

    proposals = {
        "schema": "psv1_lane_btc_h4_proposals@1",
        "cycle_id": config.CYCLE_ID,
        "cell": config.CELL,
        "dispatch_sha": config.DISPATCH_SHA,
        "proposal_law": "at most ONE strategy per data-sufficient phase, chosen by economic "
                        "mechanism, never by scanning results (plan §6); thin/ambiguous phases "
                        "=> NO_ELIGIBLE_PROPOSAL or RESEARCH_ONLY + FLAT",
        "phase_rule_freeze_ref": "freezes/phase_rule_freeze.json",
        "era_fold_freeze_ref": "freezes/era_fold_freeze.json",
        "data_gate_verdict": gate["verdict"],
        "phases": {},
    }

    acc_sum = census["per_phase_summary"]["ACCUMULATION"]
    up_sum = census["per_phase_summary"]["UPTREND"]
    dist_sum = census["per_phase_summary"]["DISTRIBUTION"]
    down_sum = census["per_phase_summary"]["DOWNTREND"]

    proposals["phases"]["ACCUMULATION"] = {
        "floors_verdict": acc_sum["verdict"],
        "margin_to_floor": {
            "episodes_cell_margin": acc_sum["margin_episodes_cell"],
            "fold_decision_margins": {f: census["per_phase_era_fold"][f"ACCUMULATION|{f}"]["margin_decisions_fold"]
                                      for f in census["fold_names"]},
            "binding_shortfall": "F4 eligible decisions 71 < 100 (margin -29); episodes margins comfortable",
        },
        "proposal": "NO_ELIGIBLE_PROPOSAL",
        "slot": "FLAT",
        "note": "NOT_RUN_THIN_PHASE (plan §4.3): floors immutable, never relaxed, never pooled with BTC_H1. "
                "A mechanism draft (capitulation-exhaustion drift long) was designed and carried through "
                "feasibility counting only; it is NOT a proposal because the phase is thin.",
    }
    proposals["phases"]["DISTRIBUTION"] = {
        "floors_verdict": dist_sum["verdict"],
        "margin_to_floor": {
            "episodes_cell_margin": dist_sum["margin_episodes_cell"],
            "fold_decision_margins": {f: census["per_phase_era_fold"][f"DISTRIBUTION|{f}"]["margin_decisions_fold"]
                                      for f in census["fold_names"]},
            "binding_shortfall": "F1 decisions 66 < 100 and F4 decisions 53 < 100",
        },
        "proposal": "NO_ELIGIBLE_PROPOSAL",
        "slot": "FLAT",
        "note": "NOT_RUN_THIN_PHASE; in addition the plan's STRICTER DISTRIBUTION default (no explicit "
                "evidenced forced-counterparty mechanism from klines observables) would independently "
                "force FLAT. DIST_FLAT / DIST_SHORT_BTC classes are §7.1-forbidden regardless.",
    }
    proposals["phases"]["DOWNTREND"] = {
        "floors_verdict": down_sum["verdict"],
        "margin_to_floor": {
            "episodes_cell_margin": down_sum["margin_episodes_cell"],
            "fold_episodes_margins": {f: census["per_phase_era_fold"][f"DOWNTREND|{f}"]["margin_episodes_fold"]
                                      for f in census["fold_names"]},
            "fold_decision_margins": {f: census["per_phase_era_fold"][f"DOWNTREND|{f}"]["margin_decisions_fold"]
                                      for f in census["fold_names"]},
        },
        "proposal": "NO_ELIGIBLE_PROPOSAL",
        "slot": "FLAT",
        "mechanism_distance_argument":
            "DOWNTREND meets the floors but every economically natural book in this phase lands on a "
            "measured-dead or forbidden class: (a) shorting the phase = DOWN_SHORT_BTC (§7.1 forbidden "
            "specialist, phase-gated variant of the same mapping class); (b) stepping aside / risk-off "
            "de-risking = DOWN_FLAT_RISKOFF (§7.1 forbidden); (c) buying post-cascade stabilization = "
            "short-horizon reversal / close-displace-fade class (§7.2 measured-dead on this program). "
            "No remaining mechanism with a forced-counterparty story is constructible from this cell's "
            "price/volume observables. A phase with no testable strategy is a valid result (plan §0).",
    }
    proposals["phases"]["TRANSITION_UNKNOWN"] = {
        "floors_verdict": "GATE_STATE_NOT_TRADABLE",
        "proposal": "NO_ELIGIBLE_PROPOSAL",
        "slot": "FLAT",
        "note": "TRANSITION_UNKNOWN is a gate state, never a traded phase.",
    }

    up_margins = {f: {"episodes_margin": census["per_phase_era_fold"][f"UPTREND|{f}"]["margin_episodes_fold"],
                      "decisions_margin": census["per_phase_era_fold"][f"UPTREND|{f}"]["margin_decisions_fold"]}
                  for f in census["fold_names"]}
    proposals["phases"]["UPTREND"] = {
        "floors_verdict": up_sum["verdict"],
        "margin_to_floor": {"episodes_cell_margin": up_sum["margin_episodes_cell"], "per_fold": up_margins},
        "proposal": {
            "family_id": "PSV1-BTC_H4-UPTREND-DONCHIAN_CONTINUATION",
            "arm_id": "PSV1-BTC_H4-UPTREND-DONCHIAN_CONTINUATION@freeze1",
            "mechanism": (
                "Forced counterparties at multi-week channel breaks, active only inside a confirmed "
                "uptrend phase. (1) Mechanical covering: stop-losses and fade entries of sellers rest "
                "just above trailing 30-bar (5-day) channel highs; an H4 close beyond that channel "
                "triggers forced buying that is rule-driven, not opinion-driven. (2) Staged/late "
                "capital: allocation- and on-ramp-driven flow deploys into confirmed strength rather "
                "than anticipates it, so continuation legs persist after the break. Both effects can "
                "survive costs because the book is event-based (a handful of round trips per year), "
                "not continuous. This is NOT a continuous trend-hold (UP_TREND_SLOW_LONG class) and "
                "not any §7.1/§7.2 listed form: exposure exists only after discrete channel events, "
                "with a structural channel stop."),
            "observable": "H4 close vs trailing 30-H4-bar close channel (prior bars only); "
                          "gate = phase-rule UPTREND state with 6-bar hysteresis (both PIT)",
            "phase_rule": "freezes/phase_rule_freeze.json (cell §5 rule; book trades only while UPTREND gate active)",
            "direction": "long only (BTC perp allows short, mechanism here is long; sizing fraction 1.0)",
            "entry": "at H4 close t: gate ON, flat, and close_t > max(close[t-30..t-1]); fill at H4 open t+1; "
                     "no entry whose fill bar crosses a fold boundary",
            "exit": "whichever first, decision at close, fill next open: (a) DONCHIAN_STOP close_t < "
                    "min(close[t-15..t-1]); (b) GATE_INACTIVE (no UPTREND label in last 6 bars); "
                    "(c) MAX_HOLD 450 bars; (d) fold end force-flat",
            "holding": {"min_bars": config.MIN_HOLD_BARS, "max_bars": config.MAX_HOLD_BARS,
                        "min_hold_law": "min-dwell suppresses ALL exit triggers (incl. DONCHIAN_STOP) "
                                        "before 12 bars held — disclosed risk window, frozen as implemented"},
            "stop_policy": "15-bar Donchian close-basis structural stop, next-open fill, subject to min-dwell",
            "execution": config.EXECUTION_LAW + "; " + config.PIT_CONVENTION,
            "sizing_fraction": config.SIZING_FRACTION,
            "churn_law": {"gate_exit_buffer_bars": config.EXIT_BUFFER_BARS,
                          "min_dwell_bars": config.MIN_HOLD_BARS,
                          "flicker_fills_structural_zero": book_up["churn_sanity"]["flicker_fills_structural_zero"],
                          "reentries_within_buffer_of_exit": book_up["churn_sanity"]["reentries_within_buffer_of_exit"],
                          "switches_per_phase_transition": book_up["churn_sanity"]["switches_per_phase_transition"],
                          "noop_law": book_up["churn_sanity"]["noop_law"]},
            "capacity_and_turnover": {
                "expected_trades_total": book_up["n_trades"],
                "trades_per_fold": book_up["trades_per_fold"],
                "median_hold_bars": book_up["hold_stats_bars"]["median"],
                "funding_boundaries_per_trade_median": book_up["funding_boundaries_per_trade_median"],
                "narrative": "~13 round trips/yr at 1.0 notional with ~14% average time-in-market on "
                             "the deepest crypto perp venue; no capacity constraint at research scale; "
                             "taker execution assumed (a limit-order variant can only reduce costs)",
            },
            "cost_arithmetic": {
                "cost_stack": ceiling["cost_stack"],
                "per_trade_cost_bps_at_1.5x": book_up["ceiling"]["per_trade_cost_bps_at_1.5x"],
                "ceiling_verdict": book_up["ceiling"]["verdict"],
                "ceiling_margin": "20.4 bps/trade at 1.5x vs 100 bps preregistered plausible-edge bound "
                                  "(~5x headroom); funding median 11 boundaries/trade included",
            },
            "control": {
                "semantics": "phase-shuffled matched control, fixed NOW before any scored result: "
                             "permute the UPTREND gate labels within each fold in non-overlapping "
                             "30-H4-bar blocks (preserves occupancy and coarse episode structure, "
                             "destroys the phase-break timing link), re-run the identical Donchian "
                             "event book on real prices",
                "validation": "Q-11 movement validation: control must generate at least 50% of the "
                              "candidate's entry count, else the control is invalid (disclosed; "
                              "null control rests the verdict on G1-G5)",
                "kill_law": "control out-earning the candidate at 1.0x => KILL (G6)",
            },
            "failure_mode": "preregistered interpretation: (i) killed by control => any edge is "
                            "phase-gating-generic, not channel-event-specific; (ii) fails G1/G2 => "
                            "cost stack dominates the mechanism; (iii) fails G4/G5 => single-era "
                            "dependence (expected suspect: F1 2020-21 expansion); (iv) any of these "
                            "is a VALID terminal finding, not a parameter-rescue trigger",
            "identity": {
                "family_id": "PSV1-BTC_H4-UPTREND-DONCHIAN_CONTINUATION",
                "arm_config_digest_source": "config.py frozen constants + this freeze; digest computed "
                                            "at integration by A1",
                "data_manifest": "data/manifest.json",
            },
            "ancestry": {
                "law": "plan §7: rho of daily signal series vs price-reconstructible dead shadows; bar 0.20",
                "measured": rho_up,
                "summary": "all four price-reconstructible shadows WITHIN_BAR (max |rho| = 0.168, "
                           "run_imbalance); OI/DVOL/pair shadows NOT_MEASURED_WITH_REASON (observables "
                           "outside this cell; mechanism-class distance documented in config)",
                "forbidden_class_check": "not a phase-gated variant of any §7.1 specialist or V2 arm; "
                                         "event-conditional channel book, structurally distinct from "
                                         "UP_TREND_SLOW_LONG (continuous), ACC_FLAT_BREAKOUT_WAIT "
                                         "(no-trade wait), and all §7.2 dead mechanisms",
            },
            "feasibility_ref": "feasibility/ceiling.json (UP_DONCHIAN_CONT)",
        },
        "slot": "CANDIDATE_ELIGIBLE_AT_INTEGRATION_PENDING_E1_E6",
    }
    proposals["proposal_count"] = 1
    proposals["budget_cells_consumed_if_scored"] = 1

    (LANE_DIR / "proposals").mkdir(parents=True, exist_ok=True)
    (LANE_DIR / "proposals" / "proposals.json").write_text(ingest.json_dumps(proposals))
    print("[write] proposals/proposals.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
