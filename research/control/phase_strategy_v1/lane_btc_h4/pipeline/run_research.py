"""PSV1 lane_btc_h4 — research driver (freeze -> census -> feasibility -> ancestry).

Order is epistemic, not just procedural: `freezes` writes the phase-rule and
era/fold freeze files from config.py (constants fixed before any label exists),
THEN `census` computes labels. No strategy returns are computed anywhere.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

LANE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LANE_DIR.parents[3]))

import pandas as pd  # noqa: E402
import numpy as np  # noqa: E402

from research.control.phase_strategy_v1.lane_btc_h4.pipeline import (  # noqa: E402
    config, ingest, phase_rule, census as census_mod, events, costs, ancestry,
)

STAGING = LANE_DIR / "data_staging"


def _dump(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(ingest.json_dumps(obj))
    print(f"[write] {path}")


def load_scored() -> tuple[pd.DataFrame, dict]:
    gate = json.loads((LANE_DIR / "data" / "data_gate.json").read_text())
    if gate["verdict"] == "BLOCKED":
        raise SystemExit("data gate BLOCKED — census refused")
    h4 = pd.read_parquet(STAGING / "scored_h4.parquet")
    return h4, gate


# ---------------------------------------------------------------------------
def write_freezes(gate: dict) -> None:
    p = phase_rule.FROZEN
    rule_freeze = {
        "schema": "psv1_lane_btc_h4_phase_rule_freeze@1",
        "cycle_id": config.CYCLE_ID,
        "cell": config.CELL,
        "dispatch_sha": config.DISPATCH_SHA,
        "frozen_at": config.DATA_RETRIEVED_AT,
        "law": "deterministic causal rule on H4 closes (UTC); decision at close; "
               "first executable fill at NEXT H4 open; TRANSITION_UNKNOWN assigned "
               "by explicit uncertainty conditions U1-U4, never model abstention",
        "observables": {
            "sma": f"SMA(close, {p.n_sma} H4 bars = 20 days)",
            "slope": f"sma_t / sma_(t-{p.m_slope}) - 1  ({p.m_slope} H4 bars = 5 days)",
            "side": f"close_t / sma_t - 1",
        },
        "classification": {
            "U1_warmup": f"bar index < {p.warmup} -> TRANSITION_UNKNOWN",
            "U2_slope_deadband": f"|slope| < {p.deadband_slope} -> TRANSITION_UNKNOWN",
            "U3_side_deadband": f"|side| < {p.deadband_side} -> TRANSITION_UNKNOWN",
            "quadrants": {
                "slope>0, side<0": "ACCUMULATION",
                "slope>0, side>=0": "UPTREND",
                "slope<0, side>0": "DISTRIBUTION",
                "slope<0, side<=0": "DOWNTREND",
            },
            "U4_confirmation": f"raw state must repeat {p.confirm} consecutive bars, else TRANSITION_UNKNOWN",
        },
        "params": {
            "n_sma": p.n_sma, "m_slope": p.m_slope,
            "deadband_slope": p.deadband_slope, "deadband_side": p.deadband_side,
            "confirm": p.confirm, "warmup_bars": p.warmup,
        },
        "param_provenance": "round domain-standard constants fixed BEFORE any history-wide "
                            "measurement (config.py, committed in the single lane commit); "
                            "bins from conventions, not from PnL (none exists) and not from label sweeps",
        "notch_ladder": config.NOTCH_LADDER,
        "sensitivity_law": "+-1 notch => label-agreement % reported, NEVER optimized",
        "no_jev_law": "no Jev label or cached V2 decision is an input anywhere",
    }
    _dump(LANE_DIR / "freezes" / "phase_rule_freeze.json", rule_freeze)

    era_fold = {
        "schema": "psv1_lane_btc_h4_era_fold_freeze@1",
        "cycle_id": config.CYCLE_ID,
        "cell": config.CELL,
        "clock": "UTC",
        "eras": [
            {**e, "end_effective": gate["data_end"] if e["end"] is None else e["end"] + "T23:59:59.999Z"}
            for e in config.ERAS
        ],
        "era_anchor_note": "halvings 2020-05-11 / 2024-04-20, cycle top 2021-04, bear bottom 2022-12: "
                           "public calendar anchors, never moved (plan §4.1)",
        "folds": [
            {"fold": f"F{i+1}", "era": e["era"],
             "start": e["start"],
             "end": gate["data_end"] if e["end"] is None else e["end"] + "T23:59:59.999Z",
             "force_flat": True}
            for i, e in enumerate(config.ERAS)
        ],
        "fold_law": config.FOLD_LAW,
        "fold_membership": "by H4 bucket OPEN time",
        "warmup_bars": p.warmup,
        "warmup_note": f"first {p.warmup} H4 bars (index 0..{p.warmup-1}) excluded from eras/floors/census",
        "floors": {
            "episodes_per_phase_cell": config.FLOOR_EPISODES_CELL,
            "episodes_per_phase_fold": config.FLOOR_EPISODES_FOLD,
            "eligible_decisions_per_phase_fold": config.FLOOR_DECISIONS_FOLD,
            "below_floor": "NOT_RUN_THIN_PHASE, strategy slot FLAT — a VALID reported result",
        },
        "data_end": gate["data_end"],
        "data_gate_verdict": gate["verdict"],
        "pit_disclosure": config.PIT_CONVENTION,
    }
    _dump(LANE_DIR / "freezes" / "era_fold_freeze.json", era_fold)


# ---------------------------------------------------------------------------
def run_census() -> None:
    h4, _ = load_scored()
    labels = phase_rule.classify(h4["close"])
    assign = census_mod.era_fold_assignment(h4["bucket_ms"], int(h4["bucket_ms"].iloc[-1] + config.H4_MS - 1),
                                            phase_rule.FROZEN.warmup)
    result = census_mod.census_for_labels(labels, assign)
    result["sensitivity_label_agreement"] = sensitivity_table(labels, h4["close"])
    result["phase_counts_total"] = labels.value_counts().to_dict()
    result["window"] = {
        "n_h4_complete": int(len(h4)),
        "first_bucket": ingest.utc_ms_to_iso(int(h4["bucket_ms"].iloc[0])),
        "last_bucket": ingest.utc_ms_to_iso(int(h4["bucket_ms"].iloc[-1])),
        "warmup_bars": phase_rule.FROZEN.warmup,
        "post_warmup_buckets": int(len(h4) - phase_rule.FROZEN.warmup),
    }
    (LANE_DIR / "census").mkdir(parents=True, exist_ok=True)
    _dump(LANE_DIR / "census" / "census.json", result)
    pd.DataFrame({"bucket_ms": h4["bucket_ms"], "phase": labels}).to_parquet(
        STAGING / "labels_frozen.parquet", index=False)
    print(f"[write] {STAGING / 'labels_frozen.parquet'}")


def sensitivity_table(base_labels: pd.Series, close: pd.Series) -> list[dict]:
    rows = []
    for key, params in phase_rule.notch_variants().items():
        variant = phase_rule.classify(close, params)
        agree = phase_rule.label_agreement(base_labels, variant)
        rows.append({"notch": key, "label_agreement_fraction": round(agree, 6),
                     "label_agreement_pct": round(100 * agree, 3)})
    return rows


# ---------------------------------------------------------------------------
BOOKS = [
    events.BookSpec(name="ACC_DRIFT_LONG", phase="ACCUMULATION", trigger="phase_start"),
    events.BookSpec(name="UP_DONCHIAN_CONT", phase="UPTREND", trigger="donchian_breakout"),
]


def run_feasibility() -> None:
    h4, _ = load_scored()
    labels = pd.read_parquet(STAGING / "labels_frozen.parquet")["phase"].to_numpy()
    close = h4["close"].to_numpy()
    assign = census_mod.era_fold_assignment(h4["bucket_ms"], int(h4["bucket_ms"].iloc[-1] + config.H4_MS - 1),
                                            phase_rule.FROZEN.warmup)
    fold_ids = assign["fold"].to_numpy()
    fills_ms = h4["bucket_ms"].to_numpy()

    out_books = []
    for spec in BOOKS:
        book = events.run_book(labels, close, spec, fold_ids)
        churn = events.churn_sanity(labels, book, spec)
        # funding-boundary exposure per trade (timestamp-exact count)
        boundaries = []
        for f, trs in book["_trade_records"].items():
            for tr in trs:
                eb, xb = tr["entry_bar"], tr["exit_bar"]
                boundaries.append(events.funding_boundary_count(int(fills_ms[eb]), int(fills_ms[xb])))
        med_hold = book["hold_stats"]["median"] if book["hold_stats"]["n"] else None
        ceil = costs.ceiling_check(book["trades_per_fold"], int(med_hold) if med_hold else None)
        out_books.append({
            "book": spec.name, "phase": spec.phase, "trigger": spec.trigger,
            "n_entries": book["n_entries"], "n_exits": book["n_exits"],
            "exit_reason_counts": book["exit_reason_counts"],
            "n_trades": book["n_trades"],
            "trades_per_fold": {str(k): v for k, v in book["trades_per_fold"].items()},
            "hold_stats_bars": book["hold_stats"],
            "funding_boundaries_total": int(sum(boundaries)),
            "funding_boundaries_per_trade_median": float(np.median(boundaries)) if boundaries else None,
            "churn_sanity": churn,
            "ceiling": ceil,
            "open_at_series_end": book["open_at_series_end"],
        })
    ceiling_doc = {
        "schema": "psv1_lane_btc_h4_feasibility_ceiling@1",
        "law": "signal-event counting ONLY (entries, exits, hold times, funding-boundary "
               "exposures); NO per-trade returns/equity exists in this lane (plan §7.3/§11)",
        "cost_stack": {
            "taker_bps_per_side": config.TAKER_FEE_BPS,
            "slippage_bps_per_side": config.SLIPPAGE_BPS,
            "round_trip_bps": config.COST_ROUND_TRIP_BPS,
            "funding_per_8h": config.FUNDING_PER_8H,
            "tiers": config.COST_TIERS,
            "tier_law": "multiplier applies to the FULL stack (fees+slippage+funding)",
        },
        "execution": config.EXECUTION_LAW,
        "sizing_fraction": config.SIZING_FRACTION,
        "books": out_books,
    }
    _dump(LANE_DIR / "feasibility" / "ceiling.json", ceiling_doc)


# ---------------------------------------------------------------------------
def run_ancestry() -> None:
    h4, _ = load_scored()
    labels = pd.read_parquet(STAGING / "labels_frozen.parquet")["phase"]
    assign = census_mod.era_fold_assignment(h4["bucket_ms"], int(h4["bucket_ms"].iloc[-1] + config.H4_MS - 1),
                                            phase_rule.FROZEN.warmup)
    fold_ids = assign["fold"].to_numpy()
    close_s = h4["close"]
    shadows = ancestry.shadow_series(close_s, h4["quote_volume"])
    results = {"schema": "psv1_lane_btc_h4_ancestry@1", "rho_bar": config.RHO_BAR, "books": {}}
    for spec in BOOKS:
        book = events.run_book(labels.to_numpy(), close_s.to_numpy(), spec, fold_ids)
        pos = _position_series(book, labels.to_numpy(), spec)
        pos_daily = ancestry.daily_sample(pd.Series(pos), h4["bucket_ms"])
        rho = ancestry.rho_vs_shadows(pos_daily, shadows, h4["bucket_ms"])
        results["books"][spec.name] = rho
    _dump(LANE_DIR / "proposals" / "ancestry_selfcheck.json", results)


def _position_series(book: dict, labels: np.ndarray, spec: events.BookSpec) -> np.ndarray:
    """FLAT=0 / LONG=+1 state series from the trade records (information content)."""
    n = len(labels)
    pos = np.zeros(n)
    for f, trs in book["_trade_records"].items():
        for tr in trs:
            pos[tr["entry_bar"]: tr["exit_bar"]] = 1.0
    return pos


def main() -> int:
    step = sys.argv[1] if len(sys.argv) > 1 else "all"
    if step in ("freezes", "all"):
        _, gate = load_scored()
        write_freezes(gate)
    if step in ("census", "all"):
        run_census()
    if step in ("feasibility", "all"):
        run_feasibility()
    if step in ("ancestry", "all"):
        run_ancestry()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
