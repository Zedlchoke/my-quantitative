"""Engine laws (V1 math carried over): next-bar fills, cost-once, stops,
folds, funding, reconciliation identity."""

from __future__ import annotations

import numpy as np
import pytest

from conftest import make_bars
from jrv2.engine import (
    BUY_HOLD,
    CostModel,
    Engine,
    fold_partition_invariants,
    folds_from_regime_ts,
    targets_from_regime,
)
from jrv2.strategies import FLAT, MR_LONG, TREND_LONG, TREND_SHORT
from jrv2.data import DAY, MIN15


def costs_btc(mult=1.0, funding=0.0):
    return CostModel(fee_bps=5.0 * mult, slip_bps=1.0 * mult, funding_rate=funding)


def rising(n=30, start=100.0, step=1.0):
    return make_bars(start + step * np.arange(n, dtype=float),
                     start + step * np.arange(n) + 1.0,
                     start + step * np.arange(n) - 1.0,
                     start + step * np.arange(n),
                     np.ones(n))


def test_trend_long_entry_signal_on_rising_series():
    bars = rising(30)
    targets = [TREND_LONG] * 30
    folds = [(0, 0, 29)]
    eng = Engine(bars, targets, folds, costs_btc())
    res = eng.run()
    assert len(res.trades) == 1
    t = res.trades[0]
    assert t.strategy == TREND_LONG
    assert t.entry_bar == 2  # next-bar open, never same-bar
    assert t.entry_ts == int(bars.ts_open[2])
    assert t.entry_px == pytest.approx(float(bars.open[2]))
    assert t.exit_reason == "fold_flat"
    assert t.exit_bar == 29
    assert t.exit_px == pytest.approx(float(bars.close[29]))


def test_cost_debit_exactly_once_hand_computed():
    bars = rising(30)
    eng = Engine(bars, [TREND_LONG] * 30, [(0, 0, 29)], costs_btc())
    res = eng.run()
    t = res.trades[0]
    entry_px = float(bars.open[2])
    exit_px = float(bars.close[29])
    qty = round(100_000.0 / entry_px, 8)
    assert t.qty == qty
    assert t.fees == pytest.approx(5e-4 * qty * (entry_px + exit_px), rel=1e-12)
    assert t.slip == pytest.approx(1e-4 * qty * (entry_px + exit_px), rel=1e-12)
    gross = (exit_px - entry_px) * qty
    assert t.net_pnl == pytest.approx(gross - t.fees - t.slip, rel=1e-12)
    assert res.equity[-1] == pytest.approx(100_000.0 + t.net_pnl, rel=1e-12)


def test_equity_identity_with_costs_and_funding():
    rng = np.random.default_rng(3)
    rets = rng.normal(0.001, 0.02, 400)
    close = 100 * np.exp(np.cumsum(rets))
    bars = make_bars(close, close * 1.005, close * 0.995, close, np.ones(400))
    eng = Engine(bars, [TREND_LONG] * 400, [(0, 0, 399)], costs_btc(funding=1.377e-5))
    res = eng.run()
    tot = res.totals
    assert res.equity[-1] == pytest.approx(
        100_000.0 + tot["gross_pnl"] - tot["costs_fee"] - tot["costs_slip"] - tot["costs_funding"],
        rel=1e-12,
    )
    assert tot["net_pnl"] == pytest.approx(
        tot["gross_pnl"] - tot["costs_fee"] - tot["costs_slip"] - tot["costs_funding"], rel=1e-12
    )


def _delayed_entry_series(n=40, crash_bar=25, crash_low=50.0):
    close = np.full(n, 100.0)
    high = close + 1.0
    low = close - 1.0
    for i in range(15, n):
        close[i] = 100 + (i - 14)
        high[i] = close[i] + 1.0
        low[i] = close[i] - 1.0
    high[crash_bar] = 60.0
    low[crash_bar] = crash_low
    close[crash_bar] = 55.0
    return make_bars(close, high, low, close, np.ones(n))


def test_stop_after_entry_bar_only():
    bars = _delayed_entry_series()
    n = len(bars.close)
    eng = Engine(bars, [TREND_LONG] * n, [(0, 0, n - 1)], costs_btc())
    res = eng.run()
    t = res.trades[0]
    assert t.entry_bar == 16
    assert t.entry_px == pytest.approx(102.0)
    assert t.exit_reason == "stop"
    assert t.exit_bar == 25
    assert t.exit_px == pytest.approx(96.0)
    assert t.exit_px != pytest.approx(float(bars.close[25]))


def test_regime_off_exit_at_next_open():
    n = 30
    bars = rising(n)
    targets = [TREND_LONG] * 10 + [FLAT] * (n - 10)
    eng = Engine(bars, targets, [(0, 0, n - 1)], costs_btc())
    res = eng.run()
    t = res.trades[0]
    assert t.exit_reason == "regime_off"
    assert t.exit_bar == 10
    assert t.exit_px == pytest.approx(float(bars.open[10]))
    assert len(res.trades) == 1
    assert res.invested[10] == 0.0


def test_no_same_open_flip():
    n = 40
    close = 100 + np.arange(n, dtype=float)
    close[12:16] = close[11] - 5
    bars = make_bars(close, close + 1, close - 1, close, np.ones(n))
    targets = [TREND_LONG] * n
    eng = Engine(bars, targets, [(0, 0, n - 1)], costs_btc())
    res = eng.run()
    for a, b in zip(res.trades, res.trades[1:]):
        assert b.entry_bar > a.exit_bar


def test_folds_force_flat_and_no_span():
    n = 60
    bars = rising(n)
    folds = [(0, 0, 29), (1, 30, 59)]
    eng = Engine(bars, [TREND_LONG] * n, folds, costs_btc())
    res = eng.run()
    for t in res.trades:
        assert t.exit_bar == t.fold_id * 30 + 29
        assert t.exit_reason == "fold_flat"
    assert res.invested[29] == 0.0
    assert res.invested[30] == 1.0
    assert len(res.fold_net_pnl) == 2
    assert abs(sum(res.fold_net_pnl) - res.totals["net_pnl"]) <= 1e-9


def test_funding_at_8h_boundary():
    import datetime as dt

    base = int(dt.datetime(2026, 1, 2, 7, 0, tzinfo=dt.timezone.utc).timestamp() * 10**9)
    n = 9
    close = 100 + np.arange(n, dtype=float)
    bars = make_bars(close, close + 1, close - 1, close, np.ones(n), start_ts=base)
    rate = 1.377e-5
    eng = Engine(bars, [TREND_LONG] * n, [(0, 0, n - 1)], costs_btc(funding=rate))
    res = eng.run()
    t = res.trades[0]
    ref_px = float(bars.close[3])
    assert t.funding == pytest.approx(rate * t.qty * ref_px, rel=1e-12)
    dn = 108 - np.arange(n, dtype=float)
    bars_dn = make_bars(dn, dn + 1, dn - 1, dn, np.ones(n), start_ts=base)
    eng2 = Engine(bars_dn, [TREND_SHORT] * n, [(0, 0, n - 1)], costs_btc(funding=rate))
    res2 = eng2.run()
    t2 = res2.trades[0]
    ref_dn = float(bars_dn.close[3])
    assert t2.funding == pytest.approx(-rate * t2.qty * ref_dn, rel=1e-12)


def test_stale_decision_maps_to_flat():
    bars = rising(30)
    regime_ts = [int(bars.ts_open[0]) - 3600 * 10**9]
    targets = targets_from_regime(bars, regime_ts, ["UPTREND"], 3600 * 10**9,
                                  {"UPTREND": TREND_LONG})
    assert targets[1] == TREND_LONG
    stale_idx = next(i for i in range(len(targets)) if int(bars.ts_open[i]) - regime_ts[0] > 2 * 3600 * 10**9)
    assert all(targets[i] == FLAT for i in range(stale_idx, len(targets)))


def test_decision_acts_on_bars_strictly_after_close():
    bars = rising(30)
    d_ts = int(bars.ts_open[10]) - 1
    targets = targets_from_regime(bars, [d_ts], ["UPTREND"], 3600 * 10**9, {"UPTREND": TREND_LONG})
    assert targets[10] == TREND_LONG
    assert all(t is None for t in targets[:10])


def test_folds_from_regime_ts_contiguous():
    bars = rising(30)
    a1 = int(bars.ts_open[5])
    a2 = int(bars.ts_open[22])
    folds = folds_from_regime_ts(bars, [(a1, int(bars.ts_open[19])), (a2, int(bars.ts_open[27]))])
    assert folds[0][1] == 6
    assert folds[1][1] == 23
    assert folds[0][2] == 22  # owns the former gap bars
    assert folds[1][2] == 29
    assert folds[0][2] + 1 == folds[1][1]


def test_f3_gap_pattern_reconciliation_and_no_span():
    """BTC-like (15m) and SPY-like (daily) grids: contiguous partition ->
    reconciliation identity holds; the old gapped partition hard-fails."""
    for step in (MIN15, DAY):
        n = 60
        bars = make_bars(
            100.0 + np.arange(n, dtype=float),
            101.0 + np.arange(n, dtype=float),
            99.0 + np.arange(n, dtype=float),
            100.0 + np.arange(n, dtype=float),
            np.linspace(1.0, 2.0, n),
            step_ns=step,
        )
        spans = [
            (int(bars.ts_open[5]), int(bars.ts_open[24])),
            (int(bars.ts_open[30]), int(bars.ts_open[58])),
        ]
        folds_new = folds_from_regime_ts(bars, spans)
        fold_partition_invariants(folds_new, len(bars.ts_close), first_required_bar=folds_new[0][1])
        assert folds_new[0][1] == 6 and folds_new[1][1] == 31
        assert folds_new[0][2] == 30 and folds_new[1][2] == 59

        targets = [TREND_LONG] * len(bars.ts_close)
        res = Engine(bars, targets, folds_new, costs_btc()).run()
        assert abs(sum(res.fold_net_pnl) - res.totals["net_pnl"]) <= 1e-9
        ranges = {fid: (s, e) for fid, s, e in folds_new}
        for t in res.trades:
            s, e = ranges[t.fold_id]
            assert s <= t.entry_bar and t.exit_bar <= e

        # OLD gapped partition is rejected by the invariant
        old_idx0 = [k for k, t in enumerate(bars.ts_open.tolist()) if spans[0][0] < t <= spans[0][1]]
        old_idx1 = [k for k, t in enumerate(bars.ts_open.tolist()) if spans[1][0] < t <= spans[1][1]]
        folds_old = [(0, old_idx0[0], old_idx0[-1]), (1, old_idx1[0], old_idx1[-1])]
        with pytest.raises(AssertionError, match="gap/overlap"):
            fold_partition_invariants(folds_old, len(bars.ts_close), first_required_bar=folds_old[0][1])


def test_engine_reconciles_when_no_trades():
    bars = rising(20)
    folds = [(0, 0, 9), (1, 10, 19)]
    res = Engine(bars, [FLAT] * 20, folds, costs_btc()).run()
    assert res.trades == []
    assert abs(sum(res.fold_net_pnl)) <= 1e-9
    assert res.totals["net_pnl"] == 0.0


def test_buyhold_reference_enters_first_fold_bar_exits_fold_end():
    bars = rising(30)
    folds = [(0, 3, 20)]
    targets = [None] * 3 + [BUY_HOLD] * 18 + [None] * 9
    eng = Engine(bars, targets, folds, costs_btc())
    res = eng.run()
    t = res.trades[0]
    assert t.entry_bar == 4
    assert t.exit_reason == "fold_flat"
    assert t.exit_bar == 20
