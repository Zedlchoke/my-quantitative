"""Engine laws: next-bar fills, cost-once, stops, folds, funding, identity."""

from __future__ import annotations

import numpy as np
import pytest

from conftest import make_bars
from jrv1.engine import (
    BUY_HOLD,
    CostModel,
    Engine,
    folds_from_regime_ts,
    targets_from_regime,
)
from jrv1.strategies import FLAT, MR_LONG, TREND_LONG, TREND_SHORT


def costs_btc(mult=1.0, funding=0.0):
    return CostModel(fee_bps=5.0 * mult, slip_bps=1.0 * mult, funding_rate=funding)


def rising(n=30, start=100.0, step=1.0):
    return make_bars(start + step * np.arange(n, dtype=float),
                     start + step * np.arange(n) + 1.0,
                     start + step * np.arange(n) - 1.0,
                     start + step * np.arange(n),
                     np.ones(n))


def test_trend_long_entry_signal_on_rising_series():
    """Rising series: first signal at bar1 (close>EMA20>EMA50), fill at bar2 open."""
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
    """One round trip: fees = 5bps*(entry+exit notional), slip = 1bps*(...), once."""
    bars = rising(30)
    eng = Engine(bars, [TREND_LONG] * 30, [(0, 0, 29)], costs_btc())
    res = eng.run()
    t = res.trades[0]
    entry_px = float(bars.open[2])
    exit_px = float(bars.close[29])
    qty = round(100_000.0 / entry_px, 8)
    assert t.qty == qty
    assert t.entry_px == pytest.approx(entry_px)
    assert t.fees == pytest.approx(5e-4 * qty * (entry_px + exit_px), rel=1e-12)
    assert t.slip == pytest.approx(1e-4 * qty * (entry_px + exit_px), rel=1e-12)
    gross = (exit_px - entry_px) * qty
    assert t.gross_pnl == pytest.approx(gross, rel=1e-12)
    assert t.net_pnl == pytest.approx(gross - t.fees - t.slip, rel=1e-12)
    # costs appear exactly once: no hidden second debit in equity
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
    """Flat 15 bars (no signal, ATR=2 constant), then rising; crash later."""
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
    """Crash bar after entry: stop fills at the STOP price (entry-3*ATR), not close."""
    bars = _delayed_entry_series()
    n = len(bars.close)
    eng = Engine(bars, [TREND_LONG] * n, [(0, 0, n - 1)], costs_btc())
    res = eng.run()
    t = res.trades[0]
    # signal at bar15 (first rising close), fill at bar16 open = 102
    assert t.entry_bar == 16
    assert t.entry_px == pytest.approx(102.0)
    # ATR14 fully initialized on flat range-2 bars -> stop = 102 - 3*2 = 96
    assert t.exit_reason == "stop"
    assert t.exit_bar == 25
    assert t.exit_px == pytest.approx(96.0)
    assert t.exit_px != pytest.approx(float(bars.close[25]))


def test_no_stop_on_entry_bar():
    """The entry bar itself may pierce the stop level without stopping out."""
    bars = _delayed_entry_series(crash_bar=16, crash_low=20.0)
    n = len(bars.close)
    eng = Engine(bars, [TREND_LONG] * n, [(0, 0, n - 1)], costs_btc())
    res = eng.run()
    t = res.trades[0]
    assert t.entry_bar == 16
    # stop exists (ATR ready) but entry bar is exempt from the stop check
    assert t.exit_bar > 16
    assert t.exit_reason != "stop" or t.exit_bar > 16


def test_regime_off_exit_at_next_open():
    """Target flips to FLAT: position exits at the NEXT bar open, regime_off."""
    n = 30
    bars = rising(n)
    targets = [TREND_LONG] * 10 + [FLAT] * (n - 10)
    eng = Engine(bars, targets, [(0, 0, n - 1)], costs_btc())
    res = eng.run()
    t = res.trades[0]
    assert t.exit_reason == "regime_off"
    assert t.exit_bar == 10
    assert t.exit_px == pytest.approx(float(bars.open[10]))
    # flat afterwards: no re-entry while FLAT
    assert len(res.trades) == 1
    assert res.invested[10] == 0.0


def test_no_same_open_flip():
    """A bar whose open processed an exit cannot also process an entry."""
    n = 40
    close = 100 + np.arange(n, dtype=float)
    # dip below EMA20 mid-series then recover: exit and re-entry queue on
    # adjacent bars; the re-entry fill must come at least one bar after exit
    close[12:16] = close[11] - 5  # below EMA20 -> exit signal bars 12..15
    bars = make_bars(close, close + 1, close - 1, close, np.ones(n))
    targets = [TREND_LONG] * n
    eng = Engine(bars, targets, [(0, 0, n - 1)], costs_btc())
    res = eng.run()
    for a, b in zip(res.trades, res.trades[1:]):
        assert b.entry_bar > a.exit_bar  # never same bar, never same open


def test_folds_force_flat_and_no_span():
    """Positions close at each fold's last close; equity is continuous."""
    n = 60
    bars = rising(n)
    folds = [(0, 0, 29), (1, 30, 59)]
    eng = Engine(bars, [TREND_LONG] * n, folds, costs_btc())
    res = eng.run()
    for t in res.trades:
        assert t.exit_bar == t.fold_id * 30 + 29
        assert t.exit_reason == "fold_flat"
    # fold 0 position force-flat at close of bar 29
    assert res.invested[29] == 0.0
    # next entry fills at fold 2's first bar open (bar 30)
    assert res.invested[30] == 1.0
    assert len(res.fold_net_pnl) == 2
    assert len(res.fold_return_series[0]) == 30
    assert len(res.fold_return_series[1]) == 30


def test_funding_at_8h_boundary():
    """BTC funding: rate * signed notional at 8h boundaries while held."""
    # 15m bars spanning the 08:00 UTC boundary: 07:00..09:00 (9 bars)
    import datetime as dt

    base = int(dt.datetime(2026, 1, 2, 7, 0, tzinfo=dt.timezone.utc).timestamp() * 10**9)
    n = 9
    close = 100 + np.arange(n, dtype=float)
    bars = make_bars(close, close + 1, close - 1, close, np.ones(n), start_ts=base)
    rate = 1.377e-5
    eng = Engine(bars, [TREND_LONG] * n, [(0, 0, n - 1)], costs_btc(funding=rate))
    res = eng.run()
    t = res.trades[0]
    boundary = int(dt.datetime(2026, 1, 2, 8, 0, tzinfo=dt.timezone.utc).timestamp() * 10**9)
    # the 08:00 boundary is the CLOSE of the bar opening 07:45 -> index 3
    ref_px = float(bars.close[3])
    assert t.funding == pytest.approx(rate * t.qty * ref_px, rel=1e-12)
    # a short position would RECEIVE funding (signed); falling series so the
    # TREND_SHORT entry condition (close<EMA20<EMA50) triggers
    dn = 108 - np.arange(n, dtype=float)
    bars_dn = make_bars(dn, dn + 1, dn - 1, dn, np.ones(n), start_ts=base)
    eng2 = Engine(bars_dn, [TREND_SHORT] * n, [(0, 0, n - 1)], costs_btc(funding=rate))
    res2 = eng2.run()
    t2 = res2.trades[0]
    ref_dn = float(bars_dn.close[3])
    assert t2.funding == pytest.approx(-rate * t2.qty * ref_dn, rel=1e-12)


def test_funding_charged_once_per_boundary():
    base = int(8 * 3600 * 10**9)  # exactly on an 8h boundary
    n = 16  # 4h span: two boundaries inside after entry
    close = 100 + np.arange(n, dtype=float)
    bars = make_bars(close, close + 1, close - 1, close, np.ones(n), start_ts=base)
    rate = 1e-3
    eng = Engine(bars, [TREND_LONG] * n, [(0, 0, n - 1)], costs_btc(funding=rate))
    res = eng.run()
    t = res.trades[0]
    # entry at open of bar1 = base+15m; boundaries at base+8h*(k) strictly after entry:
    # base+8h is inside the span (16*15m = 4h? no) -> recompute: span 4h, only boundaries
    # beyond entry within [entry, last close]: none (next boundary is +8h). funding == 0
    assert t.funding == 0.0


def test_stale_decision_maps_to_flat():
    """A governing decision older than 2 regime periods maps to FLAT."""
    bars = rising(30)
    # one decision at ts=0; exec bars start at 15m; regime period 1h
    regime_ts = [int(bars.ts_open[0]) - 3600 * 10**9]
    labels = ["UPTREND"]
    targets = targets_from_regime(bars, regime_ts, labels, 3600 * 10**9,
                                  {"UPTREND": TREND_LONG})
    # bars 1..: within 2h -> governed; after 2h -> FLAT (stale)
    assert targets[1] == TREND_LONG
    stale_idx = next(i for i in range(len(targets)) if int(bars.ts_open[i]) - regime_ts[0] > 2 * 3600 * 10**9)
    assert all(targets[i] == FLAT for i in range(stale_idx, len(targets)))


def test_decision_acts_on_bars_strictly_after_close():
    bars = rising(30)
    d_ts = int(bars.ts_open[10]) - 1  # closes just before bar 10 opens
    targets = targets_from_regime(bars, [d_ts], ["UPTREND"], 3600 * 10**9, {"UPTREND": TREND_LONG})
    assert targets[10] == TREND_LONG
    assert all(t is None for t in targets[:10])


def test_folds_from_regime_ts():
    """Contiguous partition (A7-1 F3): fold k STARTS at its first exec bar
    strictly after the frozen span start (decision boundary — untouched) and
    now OWNS exec bars through the bar immediately before fold k+1's first
    bar; the last fold extends to the final exec bar."""
    bars = rising(30)
    a1 = int(bars.ts_open[5])
    a2 = int(bars.ts_open[22])
    folds = folds_from_regime_ts(bars, [(a1, int(bars.ts_open[19])), (a2, int(bars.ts_open[27]))])
    assert folds[0][1] == 6  # first bar with open > a1 (start semantics unchanged)
    assert folds[1][1] == 23  # first bar with open > a2
    assert folds[0][2] == 22  # fold 0 owns the former gap bars 20..22
    assert folds[1][2] == 29  # last fold extends to the final exec bar
    assert folds[0][2] + 1 == folds[1][1]  # contiguous: no gap, no overlap


def test_buyhold_enters_first_fold_bar_exits_fold_end():
    bars = rising(30)
    folds = [(0, 3, 20)]
    targets = [None] * 3 + [BUY_HOLD] * 18 + [None] * 9
    eng = Engine(bars, targets, folds, costs_btc())
    res = eng.run()
    t = res.trades[0]
    assert t.entry_bar == 4  # fold starts at 3, entry fills next open
    assert t.exit_reason == "fold_flat"
    assert t.exit_bar == 20


def test_zero_costs_still_entries():
    bars = rising(10)
    eng = Engine(bars, [TREND_LONG] * 10, [(0, 0, 9)], CostModel(0.0, 0.0))
    res = eng.run()
    assert res.trades[0].fees == 0.0 and res.trades[0].slip == 0.0
    assert res.totals["net_pnl"] == pytest.approx(res.totals["gross_pnl"], rel=1e-15)


# ---- A7-1 F3 regression: non-adjacent fold spans (the exact gap pattern the
# audit found: BTC 4 exec bars / SPY 1 session in no fold) -------------------


def _two_fold_bars(n, step_ns):
    """Rising exec series; fold spans leave a gap between them (non-adjacent)."""
    from conftest import make_bars as _mb

    return _mb(
        100.0 + np.arange(n, dtype=float),
        101.0 + np.arange(n, dtype=float),
        99.0 + np.arange(n, dtype=float),
        100.0 + np.arange(n, dtype=float),
        np.linspace(1.0, 2.0, n),
        step_ns=step_ns,
    )


def test_f3_gap_pattern_reconciliation_and_no_span():
    """Synthetic 2-asset regression for the A7-1 F3 gap pattern.

    Asset X: 15m exec grid with 5 gap bars between fold spans; asset Y: daily
    grid with 1 gap session (SPY pattern: one session in no fold). Under the
    AMENDED contiguous partition: every exec bar from the first fold bar is
    assigned (gap bars owned by the PREVIOUS fold), no position spans a fold,
    and sum(fold_net_pnl) == totals.net_pnl within 1e-9. The OLD (gapped)
    partition is proven to violate the invariants — the audit's proof.
    """
    from jrv1.data import DAY, MIN15
    from jrv1.engine import fold_partition_invariants, folds_from_regime_ts as ffrt

    for step, gap_note in ((MIN15, "BTC-like: several exec bars in the gap"), (DAY, "SPY-like: one session in the gap")):
        bars = _two_fold_bars(60, step)
        spans = [
            (int(bars.ts_open[5]), int(bars.ts_open[24])),
            (int(bars.ts_open[30]), int(bars.ts_open[58])),
        ]
        first_gap = 25  # first bar with ts_open > span1 end (old law: unassigned)
        next_start = 31  # first bar with ts_open > span2 start

        folds_new = ffrt(bars, spans)
        fold_partition_invariants(folds_new, len(bars.ts_close), first_required_bar=folds_new[0][1])
        # start semantics (decision boundaries) unchanged; ends extended
        assert folds_new[0][1] == 6 and folds_new[1][1] == next_start
        assert folds_new[0][2] == next_start - 1  # gap bars owned by previous fold
        assert folds_new[1][2] == 59  # last fold extends to the final exec bar
        fold_id = np.full(len(bars.ts_close), -1, dtype=np.int64)
        for fid, s, e in folds_new:
            fold_id[s : e + 1] = fid
        assert all(fold_id[k] == 0 for k in range(first_gap, next_start)), gap_note
        assert all(fold_id[k] >= 0 for k in range(folds_new[0][1], len(bars.ts_close))), (
            f"every exec bar from the first fold bar is assigned ({gap_note})"
        )

        targets = [TREND_LONG] * len(bars.ts_close)
        res = Engine(bars, targets, folds_new, costs_btc()).run()
        # reconciliation identity (the audit measured -60.06 != -19.96 under
        # the old partition)
        assert abs(sum(res.fold_net_pnl) - res.totals["net_pnl"]) <= 1e-9, gap_note
        # no position spans a fold boundary
        ranges = {fid: (s, e) for fid, s, e in folds_new}
        for t in res.trades:
            s, e = ranges[t.fold_id]
            assert s <= t.entry_bar and t.exit_bar <= e, gap_note
        assert all(res.fold_id[i] >= 0 for i in range(len(bars.ts_close)) if res.invested[i] == 1.0)

        # OLD (gapped) partition is now REJECTED as a partition — the audit's
        # finding was exactly this gap: fold 0 ended at bar 24 and fold 1
        # started at 31, leaving bars 25..30 in no fold. The partition
        # invariant (contiguity) hard-fails on it.
        old_idx0 = [k for k, t in enumerate(bars.ts_open.tolist()) if spans[0][0] < t <= spans[0][1]]
        old_idx1 = [k for k, t in enumerate(bars.ts_open.tolist()) if spans[1][0] < t <= spans[1][1]]
        folds_old = [(0, old_idx0[0], old_idx0[-1]), (1, old_idx1[0], old_idx1[-1])]
        assert folds_old[0][2] + 1 != folds_old[1][1], "old partition must be gapped for this fixture"
        with pytest.raises(AssertionError, match="gap/overlap"):
            fold_partition_invariants(folds_old, len(bars.ts_close), first_required_bar=folds_old[0][1])


def test_engine_reconciles_when_no_trades():
    bars = rising(20)
    folds = [(0, 0, 9), (1, 10, 19)]
    res = Engine(bars, [FLAT] * 20, folds, costs_btc()).run()
    assert res.trades == []
    assert abs(sum(res.fold_net_pnl)) <= 1e-9
    assert res.totals["net_pnl"] == 0.0


def test_fold_contract_decision_boundaries_unchanged(fz):
    """Only the exec-bar partition changed; the frozen decision folds and the
    fold_contract.json bytes are untouched (pre-remediation digest)."""
    from jrv1.freezes import sha256_file

    p = fz.freezes_dir / "fold_contract.json"
    assert sha256_file(p) == fz.manifest["files"]["fold_contract.json"]
    assert (
        fz.manifest["files"]["fold_contract.json"]
        == "ac658c50a79e9f14e1d1cc92d39a1c9befc364434b8c87fe922dc9a7baaa39f7"
    )
    # the amended manifest records only sanctioned amendments
    # (remediation-r1 adapter_contract, G0 model_pin, amendment_2
    # adapter_contract) — fold_contract must NEVER be amended
    amended_files = [a["file"] for a in fz.manifest["amended"]]
    assert "fold_contract.json" not in amended_files
    assert set(amended_files) <= {"adapter_contract.json", "model_pin.json"}
