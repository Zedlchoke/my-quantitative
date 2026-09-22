"""Arms: deterministic classifier, confirm-arm matrix, random-matched null,
buy-hold reference."""

from __future__ import annotations

import numpy as np
import pytest

from conftest import make_bars
from jrv2 import LABELS as L
from jrv2.arms import (
    AssetContext,
    ControlMatchingFailed,
    F_SEEDS,
    _match,
    confirmation_labels,
    random_matched_paths,
    run_always_on_mr,
    run_always_on_trend,
    run_buy_hold,
    run_confirmation_arm,
    run_deterministic_router,
    run_jev_only_router,
    run_random_matched,
)
from jrv2.data import MIN15
from jrv2.deterministic import deterministic_persisted, raw_deterministic_labels
from jrv2.engine import CostModel
from jrv2.questionio import Timeline
from jrv2.safety import UNKNOWN
from jrv2.strategies import FLAT, MR_LONG, TREND_LONG, TREND_SHORT


def _regime_bars_uptrend(n=260):
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


def test_deterministic_uptrend_classified():
    bars = _regime_bars_uptrend()
    raw = raw_deterministic_labels(bars)
    tail = [r["label"] for r in raw[-30:]]
    assert all(l == "UPTREND" for l in tail)
    labels = deterministic_persisted(bars, PARAMS)
    assert all(l == "UPTREND" for l in labels[-20:])


def test_deterministic_downtrend_classified():
    bars = _regime_bars_downtrend()
    labels = deterministic_persisted(bars, PARAMS)
    assert all(l == "DOWNTREND" for l in labels[-20:])


def test_deterministic_range_after_decline_is_accumulation():
    n = 300
    close = np.empty(n)
    close[:140] = 100 * (1 - 0.004) ** np.arange(140)
    close[140:] = close[139] * 0.92 * (1 + 0.001 * np.sin(np.arange(n - 140) * 1.7))
    high = close * 1.0015
    low = close * 0.9985
    bars = make_bars(close, high, low, close, np.ones(n), step_ns=3600 * 10**9)
    raw = raw_deterministic_labels(bars)
    assert raw[-1]["label"] == "ACCUMULATION"
    labels = deterministic_persisted(bars, PARAMS)
    assert labels[-1] == "ACCUMULATION"


def test_deterministic_warmup_region_unknown():
    bars = _regime_bars_uptrend()
    raw = raw_deterministic_labels(bars)
    assert all(not r["eligible"] for r in raw[:168])


BTC_MAPPING = {
    "ACCUMULATION": MR_LONG,
    "UPTREND": TREND_LONG,
    "DISTRIBUTION": FLAT,
    "DOWNTREND": TREND_SHORT,
    "TRANSITION_UNKNOWN": FLAT,
}


def _ctx(bars, mapping=BTC_MAPPING, period_ns=3600 * 10**9):
    folds = [(0, 200, len(bars.close) - 1)]
    return AssetContext(
        asset="btcusdt",
        cell="BTC_H1",
        exec_bars=bars,
        regime_period_ns=period_ns,
        mapping=mapping,
        folds_exec=folds,
        costs=CostModel(fee_bps=5.0, slip_bps=1.0, funding_rate=0.0),
        periods_per_year=35064.0,
    )


def test_confirm_arm_matrix_trade_or_flat():
    """The confirm-arm law as a full hand-computed matrix: trade IFF the Jev
    effective regime EQUALS the deterministic proposal; ANY disagreement ->
    FLAT. Jev never selects alone; disagreement never invents a strategy."""
    cases = []
    for det in L:
        for jev in L:
            targets = confirmation_labels([det], [jev], BTC_MAPPING)
            want = BTC_MAPPING[det] if det == jev else FLAT
            cases.append((det, jev, targets[0], want))
            assert targets[0] == want, (det, jev)
    # spot laws from the freeze text
    assert confirmation_labels(["UPTREND"], ["UPTREND"], BTC_MAPPING) == [TREND_LONG]
    assert confirmation_labels(["UPTREND"], ["DOWNTREND"], BTC_MAPPING) == [FLAT]
    assert confirmation_labels(["UPTREND"], [UNKNOWN], BTC_MAPPING) == [FLAT]
    assert confirmation_labels([UNKNOWN], ["UPTREND"], BTC_MAPPING) == [FLAT]
    assert confirmation_labels(["DOWNTREND"], ["DOWNTREND"], BTC_MAPPING) == [TREND_SHORT]
    assert confirmation_labels(["ACCUMULATION"], ["ACCUMULATION"], BTC_MAPPING) == [MR_LONG]
    assert len(cases) == 25


def test_confirm_arm_end_to_end():
    bars = _regime_bars_uptrend(n=420)
    ctx = _ctx(bars)
    ts = [int(t) for t in bars.ts_close.tolist()]
    jev_labels = [UNKNOWN] * 220 + ["UPTREND"] * (len(ts) - 220)
    tl = _timeline_from_labels(jev_labels, ts)
    res, m, targets, (det, jev) = run_confirmation_arm(ctx, bars, tl, PARAMS)
    assert m["trades"] == res.totals["trades"]
    # every invested bar's target must equal the mapping of the agreed label
    for i, tgt in enumerate(targets):
        if tgt not in (FLAT, None):
            assert det[i] == jev[i]


def test_buy_hold_is_reference_not_scored():
    bars = _regime_bars_uptrend()
    ctx = _ctx(bars)
    res, m = run_buy_hold(ctx)
    assert res.totals["trades"] >= 1
    assert m["net_pnl"] == pytest.approx(res.totals["net_pnl"])


def test_always_on_arms_run():
    bars = _regime_bars_uptrend()
    ctx = _ctx(bars)
    for runner in (run_always_on_trend, run_always_on_mr):
        res, m = runner(ctx)
        assert m["trades"] == res.totals["trades"]


def test_jev_only_router_routes_by_persisted():
    bars = _regime_bars_uptrend()
    ctx = _ctx(bars)
    ts = [int(t) for t in bars.ts_close.tolist()]
    labels = [UNKNOWN] * 210 + ["UPTREND"] * (len(ts) - 210)
    tl = _timeline_from_labels(labels, ts)
    res, m, targets = run_jev_only_router(ctx, tl)
    switch_exec = next(i for i in range(len(targets)) if targets[i] == TREND_LONG)
    assert switch_exec > 210
    assert all(t in (TREND_LONG, FLAT, None) for t in targets)


def test_deterministic_router_end_to_end():
    bars = _regime_bars_uptrend()
    ctx = _ctx(bars)
    res, m, (ts, labels) = run_deterministic_router(ctx, bars, PARAMS)
    assert len(ts) == len(labels) == len(bars.close)
    assert labels[-1] == "UPTREND"


def _timeline_from_labels(labels, ts):
    rows = [
        {
            "bar_index": i,
            "regime_bar_close_ns": ts[i],
            "state_id": f"{i:016x}",
            "status": "OK",
            "effective": labels[i],
            "eligible": labels[i] != UNKNOWN,
            "persisted": labels[i],
            "switched": i > 0 and labels[i] != labels[i - 1],
            "violations": [],
        }
        for i in range(len(labels))
    ]
    return Timeline(rows)


def test_random_matched_paths_matched_and_moved():
    labels = (
        [UNKNOWN] * 30 + ["UPTREND"] * 25 + ["TRANSITION_UNKNOWN"] * 12
        + ["DOWNTREND"] * 18 + ["ACCUMULATION"] * 20 + ["UPTREND"] * 15
    )
    invested = {"UPTREND", "DOWNTREND", "ACCUMULATION"}
    paths = random_matched_paths(labels, invested, seeds=[1, 2, 3])
    assert len(paths) == 3
    for p in paths:
        assert len(p["labels"]) == len(labels)
        ok, deltas = _match(p["labels"], labels, invested)
        assert ok, deltas
        got = sorted(p["labels"].count(l) for l in L)
        want = sorted(labels.count(l) for l in L)
        assert got == want  # bijective relabeling preserves the count multiset
    assert any(p["labels"] != labels for p in paths)


def test_random_matched_tolerance_rejects_bad_path():
    e = ["UPTREND"] * 80 + ["DOWNTREND"] * 20
    bad = ["UPTREND"] * 50 + ["DOWNTREND"] * 50  # occupancy deviates 30pp
    ok, deltas = _match(bad, e, {"UPTREND", "DOWNTREND"})
    assert not ok
    assert deltas["occupancy_max_dev_pp"] > 0.02


def test_control_matching_failed_payload():
    err = ControlMatchingFailed({"seed": 1, "attempts": 200, "measured_deltas": {}, "tolerances": {}})
    assert "NOT_RUN_CONTROL_MATCHING" in str(err)
    assert err.payload["attempts"] == 200


def test_random_matched_21_seeds_end_to_end():
    bars = _regime_bars_uptrend()
    ctx = _ctx(bars)
    ts = [int(t) for t in bars.ts_close.tolist()]
    labels = [UNKNOWN] * 200 + ["UPTREND"] * (len(ts) - 200)
    tl = _timeline_from_labels(labels, ts)
    out = run_random_matched(ctx, tl)
    assert len(out["seeds"]) == len(F_SEEDS) == 21
    assert out["headline_seed"] in [s["seed"] for s in out["seeds"]]
    assert isinstance(out["null_invalid_flag"], bool)
    assert "q11_jev_only" in out


def test_spy_mapping_long_only_enforced_by_mapping_not_engine(fz):
    raw = fz.mapping["mapping"]
    assert raw["DOWNTREND"]["SPY"] == FLAT
    assert raw["UPTREND"]["SPY"] == TREND_LONG
    assert raw["DOWNTREND"]["BTCUSDT"] == TREND_SHORT
