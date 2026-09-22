"""Arm D classifier, arms A-F wiring, random-matched control + Q-11."""

from __future__ import annotations

import numpy as np
import pytest

from conftest import make_bars
from jrv1.arms import (
    AssetContext,
    ControlMatchingFailed,
    F_SEEDS,
    _match,
    arm_F_paths,
    run_arm_A,
    run_arm_B,
    run_arm_C,
    run_arm_D,
    run_arm_E,
    run_arm_F,
)
from jrv1.data import MIN15
from jrv1.decisions import Timeline
from jrv1.deterministic import deterministic_persisted, raw_deterministic_labels
from jrv1.engine import CostModel
from jrv1.persistence import UNKNOWN
from jrv1.strategies import FLAT, MR_LONG, TREND_LONG, TREND_SHORT


def _regime_bars_uptrend(n=260):
    """Strong monotonic uptrend with ranged pullback bars (clear ADX)."""
    close = 100 * (1 + 0.01) ** np.arange(n)
    high = close * 1.004
    low = close * 0.998
    return make_bars(close, high, low, close, np.ones(n), step_ns=3600 * 10**9)


def _regime_bars_downtrend(n=260):
    close = 100 * (1 - 0.01) ** np.arange(n)
    high = close * 1.002
    low = close * 0.996
    return make_bars(close, high, low, close, np.ones(n), step_ns=3600 * 10**9)


PARAMS = {"min_confidence": 0.5, "min_margin": 0.2, "confirm_bars": 2, "min_dwell": 6, "cooldown": 3}


def test_arm_d_uptrend_classified():
    bars = _regime_bars_uptrend()
    raw = raw_deterministic_labels(bars)
    tail = [r["label"] for r in raw[-30:]]
    assert all(l == "UPTREND" for l in tail)
    labels = deterministic_persisted(bars, PARAMS)
    assert all(l == "UPTREND" for l in labels[-20:])


def test_arm_d_downtrend_classified():
    bars = _regime_bars_downtrend()
    labels = deterministic_persisted(bars, PARAMS)
    assert all(l == "DOWNTREND" for l in labels[-20:])


def test_arm_d_range_after_decline_is_accumulation():
    """Decline then weak oscillation BELOW the 168-bar-ago close by >10%,
    with ADX < 22 -> ACCUMULATION."""
    n = 300
    close = np.empty(n)
    close[:140] = 100 * (1 - 0.004) ** np.arange(140)  # -43% grind down
    # oscillate ~7% below the decline's end so r168 vs bar t-168 < -10%
    close[140:] = close[139] * 0.92 * (1 + 0.001 * np.sin(np.arange(n - 140) * 1.7))
    high = close * 1.0015
    low = close * 0.9985
    bars = make_bars(close, high, low, close, np.ones(n), step_ns=3600 * 10**9)
    raw = raw_deterministic_labels(bars)
    assert raw[-1]["label"] == "ACCUMULATION"
    labels = deterministic_persisted(bars, PARAMS)
    assert labels[-1] == "ACCUMULATION"


def test_arm_d_warmup_region_unknown():
    bars = _regime_bars_uptrend()
    raw = raw_deterministic_labels(bars)
    assert all(not r["eligible"] for r in raw[:168])


def _ctx(bars, mapping, period_ns=3600 * 10**9):
    folds = [(0, 200, len(bars.close) - 1)]
    return AssetContext(
        asset="btcusdt",
        exec_bars=bars,
        regime_period_ns=period_ns,
        mapping=mapping,
        folds_exec=folds,
        costs=CostModel(fee_bps=5.0, slip_bps=1.0, funding_rate=0.0),
        periods_per_year=35064.0,
    )


BTC_MAPPING = {
    "ACCUMULATION": MR_LONG,
    "UPTREND": TREND_LONG,
    "DISTRIBUTION": FLAT,
    "DOWNTREND": TREND_SHORT,
    "TRANSITION_UNKNOWN": FLAT,
}


def test_arms_a_b_c_run_and_account(fz):
    bars = _regime_bars_uptrend()
    ctx = _ctx(bars, BTC_MAPPING)
    for runner in (run_arm_A, run_arm_B, run_arm_C):
        res, m = runner(ctx)
        tot = res.totals
        assert res.equity[-1] == pytest.approx(
            100_000.0 + tot["gross_pnl"] - tot["costs_fee"] - tot["costs_slip"] - tot["costs_funding"],
            rel=1e-12,
        )
        assert m["trades"] == tot["trades"]


def test_arm_d_end_to_end(fz):
    bars = _regime_bars_uptrend()
    ctx = _ctx(bars, BTC_MAPPING)
    res, m, (ts, labels) = run_arm_D(ctx, bars, PARAMS)
    assert len(ts) == len(labels) == len(bars.close)
    assert m["trades"] == res.totals["trades"]
    assert labels[-1] == "UPTREND"


def _timeline_from_labels(labels, ts):
    rows = [
        {
            "bar_index": i,
            "regime_bar_close_ns": ts[i],
            "state_id": f"{i:016x}",
            "status": "OK",
            "raw": labels[i],
            "eligible": labels[i] != UNKNOWN,
            "persisted": labels[i],
            "switched": i > 0 and labels[i] != labels[i - 1],
            "violations": [],
        }
        for i in range(len(labels))
    ]
    return Timeline(rows)


def test_arm_e_routes_by_mapping():
    bars = _regime_bars_uptrend()
    ctx = _ctx(bars, BTC_MAPPING)
    ts = [int(t) for t in bars.ts_close.tolist()]
    labels = [UNKNOWN] * 210 + ["UPTREND"] * (len(ts) - 210)
    tl = _timeline_from_labels(labels, ts)
    res, m, targets = run_arm_E(ctx, tl)
    # after the UPTREND decision, target becomes TREND_LONG (first exec bar
    # after the decision close)
    switch_exec = next(i for i in range(len(targets)) if targets[i] == TREND_LONG)
    assert switch_exec > 210
    assert all(t in (TREND_LONG, FLAT, None) for t in targets)


def test_arm_f_segment_lengths_preserved_and_matched():
    labels = (
        [UNKNOWN] * 30 + ["UPTREND"] * 25 + ["TRANSITION_UNKNOWN"] * 12
        + ["DOWNTREND"] * 18 + ["ACCUMULATION"] * 20 + ["UPTREND"] * 15
    )
    invested = {"UPTREND", "DOWNTREND", "ACCUMULATION"}
    # even a tiny path must match: segment timing is shuffled, identities
    # relabeled bijectively, so occupancy/switches/dwell stay within tolerance
    paths = arm_F_paths(labels, invested, seeds=[1, 2, 3])
    assert len(paths) == 3
    from jrv1 import LABELS as L

    for p in paths:
        assert len(p["labels"]) == len(labels)
        ok, deltas = _match(p["labels"], labels, invested)
        assert ok, deltas
        # bijective relabeling preserves the per-label count multiset exactly
        got = sorted(p["labels"].count(l) for l in L)
        want = sorted(labels.count(l) for l in L)
        assert got == want
    # the timing permutation must actually MOVE the path for at least one seed
    assert any(p["labels"] != labels for p in paths)


def test_arm_f_matching_tolerance_rejects_bad_path():
    e = ["UPTREND"] * 80 + ["DOWNTREND"] * 20
    bad = ["UPTREND"] * 50 + ["DOWNTREND"] * 50  # occupancy deviates 30pp
    ok, deltas = _match(bad, e, {"UPTREND", "DOWNTREND"})
    assert not ok
    assert deltas["occupancy_max_dev_pp"] > 0.02


def test_control_matching_failed_payload():
    err = ControlMatchingFailed({"seed": 1, "attempts": 200, "measured_deltas": {}, "tolerances": {}})
    assert "NOT_RUN_CONTROL_MATCHING" in str(err)
    assert err.payload["attempts"] == 200


def test_arm_f_end_to_end_null_verification():
    bars = _regime_bars_uptrend()
    ctx = _ctx(bars, BTC_MAPPING)
    ts = [int(t) for t in bars.ts_close.tolist()]
    labels = [UNKNOWN] * 200 + ["UPTREND"] * (len(ts) - 200)
    tl = _timeline_from_labels(labels, ts)
    out = run_arm_F(ctx, tl)
    assert len(out["seeds"]) == len(F_SEEDS)
    assert out["headline_seed"] in [s["seed"] for s in out["seeds"]]
    assert isinstance(out["null_invalid_flag"], bool)
    assert "q11_arm_E" in out


def test_q11_metrics_move():
    from jrv1.metrics import q11_metrics
    from jrv1 import LABELS as L

    # V-shaped series: falling then rising -> UPTREND on the rising half has
    # strongly positive forward returns, DOWNTREND on the falling half negative
    n = 320
    close = np.concatenate([
        100 * np.exp(-0.01 * np.arange(160)),
        100 * np.exp(-0.01 * 159) * np.exp(0.01 * np.arange(1, 161)),
    ])
    bars = make_bars(close, close * 1.001, close * 0.999, close, np.ones(n))
    codes = dict(zip(L, range(1, 6)))
    exec_idx = list(range(20, n - 30))
    k = len(exec_idx)
    labels_a = ["DOWNTREND"] * (160 - 20) + ["UPTREND"] * (k - 140)
    labels_a = labels_a[:k]
    q_a = q11_metrics(labels_a, codes, bars, exec_idx)
    # null path: fresh iid labels every bar (association ~ 0, autocorr ~ 0)
    rng = np.random.default_rng(5)
    labels_b = [str(x) for x in rng.choice(L, size=k)]
    q_b = q11_metrics(labels_b, codes, bars, exec_idx)
    assert abs(q_a["lag1_autocorr"] - q_b["lag1_autocorr"]) > 0.02
    assert abs(q_a["label_forward_assoc"] - q_b["label_forward_assoc"]) > 0.02


def test_spy_mapping_long_only_enforced_by_mapping_not_engine(fz):
    raw = fz.mapping["mapping"]  # {label: {asset: strategy}}
    assert raw["DOWNTREND"]["SPY"] == FLAT  # no short authority on SPY
    assert raw["UPTREND"]["SPY"] == TREND_LONG
    assert raw["DOWNTREND"]["BTCUSDT"] == TREND_SHORT
