"""Lane orchestrator L1_BTC_H1 — builds every lane artifact deterministically.

Order of operations honors the freeze law:
  1. data gate (integrity + manifest) on the staged retrieval
  2. labels (frozen params) + the ONE-SHOT sensitivity table (reported, not
     iterated) + the ONE-SHOT ancestry rho measurements
  3. census (floors, margin-to-floor)
  4. signal-event dry-runs for the mechanism-frozen candidates (counts only)
  5. artifacts: manifest, census, ceiling, proposals

NO returns / equity / PnL path exists in this lane.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

CODE = Path(__file__).resolve().parent
LANE = CODE.parent
sys.path.insert(0, str(CODE))

import data_gate as dg  # noqa: E402
import census as cen  # noqa: E402
import phase_rule as pr  # noqa: E402
import proposals as prop  # noqa: E402
import ancestry as anc  # noqa: E402
import costs as costs  # noqa: E402
from guards import scan_lane_sources  # noqa: E402

PIT_DISCLOSURE = (
    "PIT: Vision klines are retrospective exchange snapshots (retrieved "
    "2026-09-23; no per-bar publication timestamps). Frozen convention: a bar "
    "is knowable at its close; first executable fill at the NEXT bar open "
    "(>=1 executable-bar latency). Every label/decision uses only bars closed "
    "at or before decision time. Class: DISCOVERY_ON_NEVER_COMPUTED_HISTORY "
    "(S0 discovery, not OOS). Outcome-blindness: no strategy PnL exists in "
    "this lane."
)
XCHECK_INCIDENT = (
    "INCIDENT XCHECK-FAIL: the mandatory cross-check of the frozen 15m "
    "catalog (sha 81d4f147..., verified) resampled to 1h vs the Vision 1h "
    "series FAILED at the pre-declared tolerance (price 0.01 abs / volume "
    "1e-9 rel). Forensics: alignment is correct (shift scan optimum at 0h; "
    "close correlation 0.999969); both volume fields decode sanely (VWAP "
    "inside bar range); nevertheless per-hour volume differs by ~12x at the "
    "median (per-day vision/catalog ratios 0.01..32) and close diffs reach "
    "+/-6800 points. Conclusion: the frozen catalog is NOT a complete, "
    "consistent trade record of BTCUSDT-PERP over the overlap; identity "
    "assurance for the V2-era window could NOT be established. Law applied: "
    "no smoothing, no tolerance relaxation. The plan-prescribed SCORED source "
    "(Vision klines, independently retrieved, sha-pinned, integrity PASS, "
    "zero interior gaps) proceeds; the assurance failure is escalated to A1 "
    "for adjudication and disclosed in every artifact."
)

FLOORS = {
    "episodes_per_phase_per_cell_total": 20,
    "episodes_per_phase_per_fold": 3,
    "eligible_decisions_per_phase_per_fold": 100,
}


def sha256_json(obj: dict) -> str:
    return hashlib.sha256(
        json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def main() -> None:
    staging = LANE / "data_staging"

    # ---------- 1. data gate ----------
    entries = json.loads((staging / "manifest_raw.json").read_text())
    vision = pd.read_parquet(staging / "vision_1h.parquet")
    integrity = dg.integrity_checks(vision)
    if integrity["gap_verdict"] != "PASS":
        raise SystemExit("GAP VERDICT BLOCKED — lane must stop")
    xcheck = dg.cross_check_1h(vision)
    manifest = {
        "schema": "psv1_data_manifest@1",
        "cycle_id": "PHASE-STRATEGY-V1",
        "cell": "BTC_H1",
        "lane": "L1_BTC_H1",
        "source": "Binance Vision keyless USDT-M futures klines, BTCUSDT perpetual",
        "retrieved_utc": "2026-09-23",
        "window": {
            "first_open": integrity["first_open"],
            "last_open": integrity["last_open"],
            "last_close": integrity["last_close"],
            "data_end": "2026-09-23T00:00:00Z (close of last complete hour)",
            "data_end_definition": "daily tail stitched through 2026-09-22 "
                                   "(2026-09-23 daily zip not yet published at "
                                   "retrieval: HTTP 404 probed); last complete "
                                   "hour closes 2026-09-23T00:00Z",
        },
        "files": entries,
        "integrity": integrity,
        "cross_check_15m_catalog": xcheck,
        "cross_check_incident": XCHECK_INCIDENT,
        "scored_representation": "Vision 1h series (this manifest); the frozen "
                                 "15m catalog is used ONLY for the failed "
                                 "cross-check and corpus disclosure",
        "pit_disclosure": PIT_DISCLOSURE,
    }
    (LANE / "data" / "manifest.json").write_text(
        json.dumps(manifest, indent=1, default=str) + "\n")

    # ---------- 2. labels + one-shot tables ----------
    labels_df = pr.compute_labels(vision)
    opens = pd.DatetimeIndex(labels_df["open_time"])
    post = np.arange(len(labels_df)) >= pr.WARMUP_BARS

    base_state = labels_df["state_label"].to_numpy()
    variants = {}
    for name, kw in [
        ("adx_threshold_19", dict(adx_threshold=19.0)),
        ("adx_threshold_21", dict(adx_threshold=21.0)),
        ("adx_margin_1", dict(adx_margin=1.0)),
        ("adx_margin_3", dict(adx_margin=3.0)),
    ]:
        alt = pr.compute_labels(vision, **kw)["state_label"].to_numpy()
        variants[name] = float((alt[post] == base_state[post]).mean())
    for name, buf in [("buffer_12", 12), ("buffer_48", 48)]:
        alt = pr.compute_labels(vision, buffer_bars=buf)["state_label"].to_numpy()
        variants[name] = float((alt[post] == base_state[post]).mean())
    sensitivity = {
        "type": "LABEL_AGREEMENT_REPORTING_ONLY (one-shot; never iterated)",
        "grid": "post-warmup bars, state labels",
        "table": variants,
    }

    # ancestry (one-shot, signal-level, no PnL)
    close = labels_df["close"].to_numpy(float)
    qv = labels_df["quote_volume"].to_numpy(float)
    sig_a = np.zeros(len(close))
    sig_b = np.zeros(len(close))
    sig_c = np.zeros(len(close))
    fold_ids = np.zeros(len(close), dtype=int)
    for i, o in enumerate(opens):
        if o >= pd.Timestamp("2021-05-01", tz="UTC"):
            fold_ids[i] = 1
        if o >= pd.Timestamp("2023-01-01", tz="UTC"):
            fold_ids[i] = 2
        if o >= pd.Timestamp("2025-01-01", tz="UTC"):
            fold_ids[i] = 3
    # candidate signal series (position books from the frozen rules; labels only)
    from signal_path import book_from_events
    ev_a, trig_a = prop.signals_uptrend_breakout(labels_df, fold_ids)
    ev_b, trig_b = prop.signals_acc_floor_provision(labels_df, fold_ids)
    ev_c, trig_c = prop.signals_downtrend_breakdown_cont(labels_df, fold_ids)
    n_bars = len(labels_df)
    sig_a = book_from_events(ev_a, n_bars, direction=1).astype(float)
    sig_b = book_from_events(ev_b, n_bars, direction=1).astype(float)
    sig_c = book_from_events(ev_c, n_bars, direction=-1).astype(float)
    ancestry = anc.measure(close, qv, {
        "PSV1-BTC_H1-UPTREND-BREAKOUT_CONT": sig_a,
        "PSV1-BTC_H1-ACC-FLOOR_PROVISION": sig_b,
        "PSV1-BTC_H1-DOWNTREND-BREAKDOWN_CONT": sig_c,
    })
    ancestry["bar_reading"] = (
        "applied eligibility reading: |rho| <= 0.20 => distinct mechanism "
        "(plan sec13 E3); |rho| > 0.20 => same-mechanism self-veto. The "
        "plan sec7.2 parenthetical states the bar inversely; the ambiguity "
        "is disclosed for A1 adjudication."
    )
    ancestry["self_veto_any"] = any(
        r["self_veto"] for r in ancestry["per_candidate"].values())

    # ---------- 3. census ----------
    freeze_era = json.loads((LANE / "freezes" / "era_fold_freeze.json").read_text())
    bounds = [
        (pd.Timestamp("2020-01-31", tz="UTC"), pd.Timestamp("2021-05-01", tz="UTC")),
        (pd.Timestamp("2021-05-01", tz="UTC"), pd.Timestamp("2023-01-01", tz="UTC")),
        (pd.Timestamp("2023-01-01", tz="UTC"), pd.Timestamp("2025-01-01", tz="UTC")),
        (pd.Timestamp("2025-01-01", tz="UTC"), opens[-1] + pd.Timedelta(hours=1)),
    ]
    labels_post = list(np.array(labels_df["state_label"])[post])
    opens_post = opens[post]
    census = cen.census_cell(labels_post, opens_post, bounds, FLOORS)
    census["sensitivity_table"] = sensitivity
    census["ancestry"] = ancestry
    census["pit_disclosure"] = PIT_DISCLOSURE
    census["xcheck_incident"] = XCHECK_INCIDENT
    (LANE / "census" / "census.json").write_text(
        json.dumps(census, indent=1, default=str) + "\n")

    # ---------- 4. dry-runs (counts only) + ceiling ----------
    dry = {}
    n_transitions = int(sum(1 for t in range(1, len(base_state))
                            if base_state[t] != base_state[t - 1]))
    for key, ev in [("UPTREND_BREAKOUT_CONT", ev_a),
                    ("ACC_FLOOR_PROVISION", ev_b),
                    ("DOWNTREND_BREAKDOWN_CONT", ev_c)]:
        d = ev.summary()
        per_fold = {}
        for f in (1, 2, 3, 4):
            per_fold[f"F{f}"] = int(sum(
                1 for e in ev.entries if fold_ids[e] == f - 1))
        d["entries_per_fold"] = per_fold
        d["phase_label_transitions_total"] = n_transitions
        d["switch_fraction_of_transitions"] = round(
            d["position_switches"] / n_transitions, 5) if n_transitions else None
        dry[key] = d
    # census-driven eligibility (which phases can carry a proposal)
    thin = set(census["thin_phases"])
    eligible = [p for p in ["ACCUMULATION", "UPTREND", "DOWNTREND"]
                if p not in thin]
    ceiling = {
        "schema": "psv1_feasibility_ceiling@1",
        "law": "plan sec 11: counts/hold-times ONLY; cost arithmetic vs "
               "stated argued-edge assumptions; no returns anywhere",
        "cost_model": {
            "taker_fee_bps_per_side": costs.FEE_TAKER_BPS_PER_SIDE,
            "slippage_bps_per_side": costs.SLIPPAGE_BPS_PER_SIDE,
            "round_trip_bps": costs.ROUND_TRIP_BPS,
            "funding_per_8h": costs.FUNDING_PER_8H,
            "funding_bps_per_day_adverse_allowance": round(
                costs.FUNDING_PER_8H * 3 * 1e4, 4),
            "tiers": list(costs.TIERS),
            "tier_law": "multiplier applies to fees+slippage AND funding "
                        "(full stack)",
        },
        "dry_runs": dry,
        "eligible_phases": eligible,
        "thin_phases": sorted(thin),
        "candidates": {},
        "pit_disclosure": PIT_DISCLOSURE,
        "xcheck_incident": XCHECK_INCIDENT,
    }

    # ceiling arithmetic per candidate (stated assumptions, frozen)
    stated = {
        "UPTREND_BREAKOUT_CONT": {
            "argued_gross_edge_bps_per_episode": 200,
            "argument": "the defining anatomy of a UPTREND episode (ADX>=22 "
                        "persistence + Donchian-20d breakout) is a sustained "
                        "directional structure; an episode failing to move "
                        "+2% over its multi-day dwell would not satisfy it; "
                        "stated as assumption, adjudicated by the scored run",
        },
        "ACC_FLOOR_PROVISION": {
            "argued_gross_edge_bps_per_episode": 500,
            "argument": "entry in the lower quartile of a 30d range; the "
                        "mechanism's minimum DEFINED capture is the "
                        "range-floor-to-midpoint span (>= 25% of range "
                        "height); a 30d BTC range under 5% height is "
                        "extraordinarily dead; stated as assumption",
        },
        "DOWNTREND_BREAKDOWN_CONT": {
            "argued_gross_edge_bps_per_episode": 200,
            "argument": "mirror of the UPTREND anatomy for breakdown "
                        "persistence; deleveraging cascades are persistent; "
                        "stated as assumption",
        },
    }
    for key, s in stated.items():
        if key not in dry:
            continue
        holds = dry[key]["hold_bars_median"] or 0.0
        days = holds / 24.0
        trades = dry[key]["entries"]
        years = len(labels_post) / 24.0 / 365.25
        per_year = trades / years if years > 0 else 0.0
        row = {
            "stated_assumption": s,
            "median_hold_days": round(days, 2),
            "entries_total": trades,
            "entries_per_year_est": round(per_year, 2),
            "cost_bps_round_trip_by_tier": {},
            "cost_plus_funding_allowance_bps_by_tier": {},
            "margin_edge_over_cost_by_tier": {},
            "ceiling_verdict": {},
        }
        for tier in costs.TIERS:
            fees = costs.round_trip_cost_fraction(tier) * 1e4
            fund = float(costs.FUNDING_PER_8H * 3 * days * tier * 1e4)
            load = fees + fund
            edge = float(s["argued_gross_edge_bps_per_episode"])
            row["cost_bps_round_trip_by_tier"][str(tier)] = round(fees, 3)
            row["cost_plus_funding_allowance_bps_by_tier"][str(tier)] = round(load, 3)
            row["margin_edge_over_cost_by_tier"][str(tier)] = round(edge / load, 2) if load > 0 else None
            row["ceiling_verdict"][str(tier)] = (
                "PASS" if edge > 2.0 * load else
                ("STRUCK_BY_CEILING" if edge < load else "MARGIN_THIN"))
        ceiling["candidates"][key] = row
    (LANE / "feasibility" / "ceiling.json").write_text(
        json.dumps(ceiling, indent=1, default=str) + "\n")

    # ---------- 5. proposals ----------
    arm_digests = {}
    proposal_defs = build_proposal_defs(eligible, ceiling, ancestry)
    for fam, p in proposal_defs.items():
        arm_digests[fam] = sha256_json(p["arm_config"])
    proposals = {
        "schema": "psv1_proposals@1",
        "cycle_id": "PHASE-STRATEGY-V1",
        "cell": "BTC_H1",
        "lane": "L1_BTC_H1",
        "pit_disclosure": PIT_DISCLOSURE,
        "xcheck_incident": XCHECK_INCIDENT,
        "phase_slots": {},
        "proposals": {},
    }
    for phase in ["ACCUMULATION", "UPTREND", "DISTRIBUTION", "DOWNTREND",
                  "TRANSITION_UNKNOWN"]:
        if phase in thin:
            slot = "NOT_RUN_THIN_PHASE (slot FLAT)"
        elif phase == "DISTRIBUTION":
            slot = "NO_ELIGIBLE_PROPOSAL (strict default: no evidenced " \
                   "forced-counterparty mechanism from OHLCV observables)"
        elif phase == "TRANSITION_UNKNOWN":
            slot = "NO_ELIGIBLE_PROPOSAL (uncertainty buffer by construction)"
        else:
            fam = next((f for f, p in proposal_defs.items()
                        if p["phase"] == phase), None)
            slot = f"FROZEN: {fam}" if fam else "NO_ELIGIBLE_PROPOSAL"
        proposals["phase_slots"][phase] = slot
    for fam, p in proposal_defs.items():
        p["arm_config_digest"] = arm_digests[fam]
        proposals["proposals"][fam] = p
    (LANE / "proposals" / "proposals.json").write_text(
        json.dumps(proposals, indent=1, default=str) + "\n")

    scan = scan_lane_sources(LANE)
    (LANE / "data" / "guard_scan.json").write_text(
        json.dumps(scan, indent=1) + "\n")
    print(json.dumps({
        "thin_phases": sorted(thin),
        "eligible": eligible,
        "dry_run_entries": {k: v["entries"] for k, v in dry.items()},
        "self_veto_any": ancestry["self_veto_any"],
        "sensitivity": variants,
        "guard_scan_clean": scan["clean"],
    }, indent=1, default=str))


def build_proposal_defs(eligible, ceiling, ancestry):
    """Frozen proposal contracts (plan sec 6). Mechanisms were fixed BEFORE
    dry-run counts were seen; this function only assembles the artifacts."""
    defs = {}
    if "UPTREND" in eligible:
        defs["PSV1-BTC_H1-UPTREND-BREAKOUT_CONT"] = {
            "phase": "UPTREND",
            "family_id": "PSV1-BTC_H1-UPTREND-BREAKOUT_CONT",
            "mechanism": "forced-counterparty anatomy of BTC markup legs: "
                         "shorts are stopped/liquidated into standing highs "
                         "and late momentum chasers lift offers; continuation "
                         "after a 20d-high breakout is supplied by these "
                         "forced buyers, and the effect survives costs "
                         "because episodes are sparse (few round trips/yr) "
                         "and multi-day.",
            "observable": "PIT: close vs trailing 480-bar high of highs "
                          "(Donchian-20d) on the H1 UTC grid, gated by the "
                          "cell's frozen phase rule state UPTREND",
            "phase_rule": "cell's frozen ADX/DI+SMA720 rule (sec5 freeze)",
            "direction": "LONG only (BTC perp)",
            "entry": "state==UPTREND AND close > max(high, previous 480 bars)",
            "exit": "STOP: close < min(low, trailing 240 bars) [risk stop, "
                    "pre-min-hold allowed]; gate-off exit: state leaves "
                    "UPTREND after min-hold; fold-end force-flat",
            "holding": "min hold 24 bars (churn law); max hold unbounded "
                       "(structure-exited)",
            "sizing": "fraction 1.0 (V2 accounting)",
            "stop_policy": "the 240-bar-low close IS the stop "
                           "(structure stop); no separate ATR stop",
            "execution": "decision at bar close; fill at NEXT bar open; no "
                         "mid-bar fills",
            "churn_law": "min-dwell 24 bars == phase-rule transition buffer; "
                         "same-direction label noise produces zero fills "
                         "(no-op law, engine-structurally-enforced)",
            "capacity": "BTCUSDT-PERP is the deepest crypto venue; hourly "
                        "decisions with multi-day holds at 1.0 book fraction "
                        "are negligible vs top-of-book depth; turnover = "
                        "entries/yr x 2 sides (see ceiling.json)",
            "control": {
                "type": "phase-shuffled matched control with movement "
                        "validation",
                "semantics_frozen_now": "permute phase-label EPISODE blocks "
                                        "within each fold (seed 20260923, 100 "
                                        "draws); apply the identical entry/"
                                        "exit rule under the shuffled gate; "
                                        "control is VALID only if its entry-"
                                        "time 24h realized-move distribution "
                                        "matches the candidate's (KS stat <= "
                                        "0.15), computed in the scored run; "
                                        "control out-earning => kill (G6)",
            },
            "failure_mode": "expected failure: breakout continuation is "
                            "already arbitraged in BTC perps (mechanism-dead "
                            "or cost-eaten at 1.5x); fold concentration in "
                            "one bull era is the secondary failure signature",
            "ancestry_self_check": "not an RSM-V1 specialist: UP_TREND_SLOW_"
                                   "LONG is a continuously-held regime long; "
                                   "this is an event-conditional breakout book "
                                   "with structure stop; not any sec7.2 dead "
                                   "class (reversal/imbalance/illiquidity/OI/"
                                   "vol-shock/pair); rho measured in census",
            "arm_config": {
                "entry_donchian_bars": prop.DONCHIAN_ENTRY_BARS,
                "stop_donchian_bars": prop.DONCHIAN_EXIT_BARS,
                "min_hold_bars": prop.MIN_HOLD_BARS,
                "sizing_fraction": 1.0,
                "direction": "long",
                "execution": "next_open",
            },
        }
    if "ACCUMULATION" in eligible:
        defs["PSV1-BTC_H1-ACC-FLOOR_PROVISION"] = {
            "phase": "ACCUMULATION",
            "family_id": "PSV1-BTC_H1-ACC-FLOOR_PROVISION",
            "mechanism": "at range floors after declines, forced sellers "
                         "(margin-stressed longs, redemption flows, impatient "
                         "holders) hit thin books; patient accumulation "
                         "provides the other side and inventory is held "
                         "through the range until markup; effect survives "
                         "costs because entries are sparse deep-in-range "
                         "events with multi-week holds.",
            "observable": "PIT: close position within the trailing 720-bar "
                          "(30d) close range, gated by state ACCUMULATION",
            "phase_rule": "cell's frozen ADX/DI+SMA720 rule (sec5 freeze)",
            "direction": "LONG only",
            "entry": "state==ACCUMULATION AND close <= 30d-range low + 25% "
                     "of range height",
            "exit": "hold gate {ACCUMULATION, UPTREND}: exit when state "
                    "leaves the gate after min-hold (markup ride through "
                    "ACC->UP is intended); STOP: close below the 30d range "
                    "low observed at the entry bar (structure break, "
                    "pre-min-hold allowed); fold-end force-flat",
            "holding": "min hold 24 bars; max hold unbounded",
            "sizing": "fraction 1.0",
            "stop_policy": "entry-time 30d range low = structure stop",
            "execution": "decision at close; fill next open",
            "churn_law": "min-dwell 24 bars; same-direction label noise "
                         "produces zero fills",
            "capacity": "sparse floor entries, multi-week holds; turnover "
                        "counts in ceiling.json",
            "control": {
                "type": "clock-only control",
                "semantics_frozen_now": "identical structure entry rule "
                                        "WITHOUT the phase gate; entries "
                                        "thinned deterministically (keep "
                                        "every k-th event) to the candidate's "
                                        "entry count (k frozen from the "
                                        "candidate dry-run count); exits on a "
                                        "frozen 720-bar clock instead of the "
                                        "phase hold-gate; control out-earning "
                                        "=> kill (G6)",
            },
            "failure_mode": "expected failure: ranges resolve DOWN more often "
                            "than UP in contraction eras (falling-knife "
                            "capture), or floor provision is just low-"
                            "volatility beta that the baselines beat",
            "ancestry_self_check": "not ACC_RANGE_MR: that specialist fades "
                                   "range excursions (two-sided, mean-target "
                                   "exits, high trade count); this is a "
                                   "one-sided liquidity-provision book with "
                                   "structure stop and markup-ride exit; not "
                                   "ACC_FLAT_BREAKOUT_WAIT (no breakout "
                                   "entries in ACC); rho measured in census",
            "arm_config": {
                "range_window_bars": prop.RANGE_WINDOW_BARS,
                "entry_quantile": prop.RANGE_ENTRY_QUANTILE,
                "min_hold_bars": prop.MIN_HOLD_BARS,
                "sizing_fraction": 1.0,
                "direction": "long",
                "execution": "next_open",
            },
        }
    if "DOWNTREND" in eligible:
        defs["PSV1-BTC_H1-DOWNTREND-BREAKDOWN_CONT"] = {
            "phase": "DOWNTREND",
            "family_id": "PSV1-BTC_H1-DOWNTREND-BREAKDOWN_CONT",
            "mechanism": "deleveraging cascades are persistent: forced "
                         "selling (margin calls, stop cascades, fund "
                         "redemptions) begets forced selling; unlevered "
                         "holders exit late and market makers reprice thin "
                         "books slowly; breakdown continuation after a 20d-"
                         "low break survives costs (sparse events, multi-day "
                         "holds, funding typically a short rebate in "
                         "contraction).",
            "observable": "PIT: close vs trailing 480-bar low of lows, gated "
                          "by state DOWNTREND",
            "phase_rule": "cell's frozen ADX/DI+SMA720 rule (sec5 freeze)",
            "direction": "SHORT only (BTC perp; allowed by plan sec6)",
            "entry": "state==DOWNTREND AND close < min(low, previous 480 bars)",
            "exit": "STOP: close > max(high, trailing 240 bars); gate-off "
                    "exit after min-hold; fold-end force-flat",
            "holding": "min hold 24 bars; max unbounded",
            "sizing": "fraction 1.0",
            "stop_policy": "the 240-bar-high close IS the stop",
            "execution": "decision at close; fill next open",
            "churn_law": "min-dwell 24 bars; same-direction label noise "
                         "produces zero fills",
            "capacity": "sparse breakdown events, multi-day holds; counts in "
                        "ceiling.json",
            "control": {
                "type": "phase-shuffled matched control with movement "
                        "validation",
                "semantics_frozen_now": "same as the UPTREND candidate "
                                        "control (episode-block permutation "
                                        "within fold, seed 20260923, 100 "
                                        "draws, KS<=0.15 movement validation)",
            },
            "failure_mode": "expected failure: breakdown entries cluster at "
                            "local lows that mean-revert (stop churn), or "
                            "the effect is indistinguishable from SPARSE_"
                            "RISK_OFF-style avoidance",
            "ancestry_self_check": "not DOWN_SHORT_BTC: that specialist is a "
                                   "continuously-held regime short; this is "
                                   "an event-conditional breakdown book with "
                                   "structure stop; not any sec7.2 dead class "
                                   "(not reversal: entries require a NEW 20d "
                                   "low with ADX>=22 structure, not a fade "
                                   "signal); rho measured in census",
            "arm_config": {
                "entry_donchian_bars": prop.DONCHIAN_ENTRY_BARS,
                "stop_donchian_bars": prop.DONCHIAN_EXIT_BARS,
                "min_hold_bars": prop.MIN_HOLD_BARS,
                "sizing_fraction": 1.0,
                "direction": "short",
                "execution": "next_open",
            },
        }
    return defs


if __name__ == "__main__":
    main()
