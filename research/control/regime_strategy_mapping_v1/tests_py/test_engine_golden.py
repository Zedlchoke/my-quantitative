"""A5 golden-fixture tests — engine, cost and churn audit (runnable).

One test per pinned law (dispatch laws 1-11) plus the ALSO-AUDIT items
(metrics.py churn/dwell/occupancy, equity MTM identity). Expected values
live in fixtures_engine_golden.py and are hand-derived there from the
pinned laws — never from engine internals.

Synthetic fixtures only: no real-corpus runs, no runtime/ or evidence/
reads, no Jev calls, no paper/live surface (A5 scope).
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from rsmv1 import arms  # noqa: E402
from rsmv1.engine import (  # noqa: E402
    BUY_HOLD,
    Engine,
    fold_partition_invariants,
    targets_from_regime,
)
from rsmv1.metrics import compute_arm_metrics, regime_stats_from_timeline  # noqa: E402
from rsmv1.strategies import FLAT, TREND_LONG, TREND_SHORT  # noqa: E402

from fixtures_engine_golden import (  # noqa: E402
    HOUR,
    MIN15,
    MAPPING,
    T0,
    YEAR_NS,
    scenario_buy_hold,
    scenario_entry_dropped_when_target_vanishes,
    scenario_funding_long,
    scenario_funding_short,
    scenario_flip,
    scenario_folds,
    scenario_regime_off,
    scenario_stop,
    scenario_step_up_hold,
    scenario_step_up_hold_spy,
    h1_timeline,
    h4_timeline,
)


def _run(bars, targets, folds, costs):
    return Engine(bars, targets, folds, costs).run()


def _assert_equity(res, expected, tol=1e-6):
    assert len(res.equity) == len(expected)
    for i, (got, want) in enumerate(zip(res.equity.tolist(), expected)):
        assert got == pytest.approx(want, abs=tol), f"equity[{i}]: {got!r} != {want!r}"


# ---------------------------------------------------------------------------
# Law 1 — next-bar-open fills; no same-bar fills; no same-open flip
# ---------------------------------------------------------------------------


def test_law1_next_bar_open_fills():
    bars, targets, folds, costs, exp = scenario_step_up_hold()
    res = _run(bars, targets, folds, costs)
    assert len(res.trades) == 1
    t = res.trades[0]
    # signal fired at close of bar 19; the fill is at bar 20, never bar 19
    assert res.invested[19] == 0.0
    assert res.equity[19] == pytest.approx(100_000.0, abs=1e-9)
    assert t.entry_bar == exp["entry_bar"] == 20
    assert t.entry_ts == exp["entry_ts"] == bars.ts_open[20]
    assert t.entry_px == pytest.approx(100.0, abs=1e-9)
    # exit signal fired at close of bar 29; fill at bar 30 open
    assert t.exit_bar == exp["exit_bar"] == 30
    assert t.exit_ts == exp["exit_ts"] == bars.ts_open[30]
    assert t.exit_reason == "strategy_exit"
    assert t.exit_px == pytest.approx(100.0, abs=1e-9)
    assert t.exit_ts > t.entry_ts


# ---------------------------------------------------------------------------
# Law 2 — costs debited exactly once per fill (BTC fee+slip; SPY band as fees)
# ---------------------------------------------------------------------------


def test_law2_costs_exactly_once_btc():
    bars, targets, folds, costs, exp = scenario_step_up_hold()
    res = _run(bars, targets, folds, costs)
    t = res.trades[0]
    # one entry fill + one exit fill: fee/slip are the exact sums of the two sides
    assert t.fees == pytest.approx(exp["fees"], abs=1e-6)  # 100 = 50 + 50
    assert t.slip == pytest.approx(exp["slip"], abs=1e-6)  # 20 = 10 + 10
    assert res.totals["costs_fee"] == pytest.approx(exp["fees"], abs=1e-6)
    assert res.totals["costs_slip"] == pytest.approx(exp["slip"], abs=1e-6)
    assert res.totals["costs_funding"] == pytest.approx(0.0, abs=1e-12)
    assert res.totals["net_pnl"] == pytest.approx(exp["net"], abs=1e-6)  # -120
    assert res.totals["trades"] == 1
    # the hand-traced equity path is only consistent with single-charging
    _assert_equity(res, exp["equity"])


def test_law2_spy_band_booked_as_fees_zero_slippage():
    bars, targets, folds, costs, exp = scenario_step_up_hold_spy()
    res = _run(bars, targets, folds, costs)
    t = res.trades[0]
    assert t.slip == 0.0  # SPY model: zero slippage, exactly
    assert res.totals["costs_slip"] == 0.0
    assert t.fees == pytest.approx(exp["fees"], abs=1e-6)  # 2 * 1e-3 * 100000 = 200
    assert res.totals["net_pnl"] == pytest.approx(exp["net"], abs=1e-6)  # -200
    _assert_equity(res, exp["equity"])


# ---------------------------------------------------------------------------
# Law 3 — intrabar stops only after the entry bar; fill at the stop price,
# slippage debited separately
# ---------------------------------------------------------------------------


def test_law3_stop_after_entry_bar_at_stop_price():
    bars, targets, folds, costs, exp = scenario_stop()
    res = _run(bars, targets, folds, costs)
    assert len(res.trades) == 1
    t = res.trades[0]
    # entry bar low (94) touches the stop (94): the entry bar is EXCLUDED
    assert res.invested[20] == 1.0, "stop must not fire on the entry bar"
    assert t.entry_bar == 20 and t.exit_bar == 21
    assert t.exit_reason == "stop"
    assert t.exit_px == pytest.approx(exp["stop_px"], abs=1e-9)  # exactly 94.0
    assert t.exit_ts == bars.ts_open[21]
    # stop fill carries its own fee AND slippage on the 94 notional, once
    assert t.fees == pytest.approx(exp["fees"], abs=1e-6)  # 50 + 47 = 97
    assert t.slip == pytest.approx(exp["slip"], abs=1e-6)  # 10 + 9.4 = 19.4
    assert t.gross_pnl == pytest.approx(exp["gross"], abs=1e-6)  # -6000
    assert t.net_pnl == pytest.approx(exp["net"], abs=1e-6)  # -6116.4
    _assert_equity(res, exp["equity"])


# ---------------------------------------------------------------------------
# Law 4 — strategy/regime-off exits at the NEXT open; reconcile to the new
# target at the next open
# ---------------------------------------------------------------------------


def test_law4_regime_off_exit_at_next_open():
    bars, targets, folds, costs, exp = scenario_regime_off()
    res = _run(bars, targets, folds, costs)
    assert len(res.trades) == 1
    t = res.trades[0]
    assert t.exit_reason == "regime_off"  # reconciliation, not stop (runs first)
    assert t.exit_bar == exp["exit_bar"] == 21  # first FLAT-target bar
    assert t.exit_ts == exp["exit_ts"] == bars.ts_open[21]  # that bar's OPEN
    assert t.exit_px == pytest.approx(exp["exit_px"], abs=1e-9)  # 101
    assert t.net_pnl == pytest.approx(exp["net"], abs=1e-6)  # 879.4
    _assert_equity(res, exp["equity"])
    # no re-entry while target stays FLAT
    assert res.invested[22:].sum() == 0.0


def test_law4_entry_dropped_when_target_vanishes_before_fill():
    bars, targets, folds, costs, exp = scenario_entry_dropped_when_target_vanishes()
    res = _run(bars, targets, folds, costs)
    assert res.trades == []
    assert res.invested.sum() == 0.0
    assert all(v == pytest.approx(100_000.0, abs=1e-9) for v in res.equity.tolist())


# ---------------------------------------------------------------------------
# Law 5 — contiguous fold partition; no position across a fold boundary;
# force-flat at the fold's last exec bar close with costs; equity continuous;
# sum(fold_net_pnl) == totals.net_pnl; entries refused on unassigned bars
# ---------------------------------------------------------------------------


def test_law5_fold_partition_and_force_flat():
    bars, targets, folds, costs, exp = scenario_folds()
    res = _run(bars, targets, folds, costs)
    # hand-derived contiguous partition
    assert res.fold_id.tolist() == exp["fold_id"]  # [-1]*8 + [0]*10 + [1]*2
    assert exp["folds"] == [(0, 8, 17), (1, 18, 19)]
    # pre-warmup refusal: signal on unassigned bar 5 produces no fill
    assert res.invested[:8].sum() == 0.0
    assert all(v == pytest.approx(100_000.0, abs=1e-9) for v in res.equity[:8].tolist())
    # the single trade lives inside fold 0
    assert len(res.trades) == 1
    t = res.trades[0]
    assert t.entry_bar == 10 and t.exit_bar == 17
    assert t.exit_reason == "fold_flat"
    assert t.exit_ts == bars.ts_close[17]  # force-flat at the fold's LAST exec bar CLOSE
    assert t.exit_px == pytest.approx(100.0, abs=1e-9)
    assert t.fees == pytest.approx(exp["fees"], abs=1e-6)  # 100 (costs on the force-flat)
    assert t.slip == pytest.approx(exp["slip"], abs=1e-6)  # 20
    assert t.fold_id == 0
    # equity continuous across the fold boundary; fold 1 has no position and zero PnL
    _assert_equity(res, exp["equity"])
    assert res.equity[17] == pytest.approx(res.equity[18], abs=1e-12)
    assert res.fold_net_pnl == pytest.approx(exp["fold_net"], abs=1e-9)  # [-120, 0]
    assert sum(res.fold_net_pnl) == pytest.approx(res.totals["net_pnl"], abs=1e-9)
    # partition invariants: post-warmup coverage required, pre-warmup not
    fold_partition_invariants(folds, len(bars.ts_close), first_required_bar=8)
    with pytest.raises(AssertionError):
        fold_partition_invariants(folds, len(bars.ts_close), first_required_bar=7)


# ---------------------------------------------------------------------------
# Law 6 — BTC funding at 8h UTC boundaries strictly after entry up to exit;
# longs pay, shorts receive
# ---------------------------------------------------------------------------


def test_law6_funding_long_pays_at_boundaries():
    bars, targets, folds, costs, exp = scenario_funding_long()
    res = _run(bars, targets, folds, costs)
    assert len(res.trades) == 1
    t = res.trades[0]
    assert t.entry_ts == bars.ts_open[31]  # 07:45Z; boundary 08:00Z is strictly after
    assert t.exit_ts == bars.ts_open[64]  # 16:00Z
    # exactly two events: 08:00Z and 16:00Z, each rate * qty * ref(102)
    assert t.funding == pytest.approx(exp["funding"], abs=1e-9)
    assert t.funding > 0.0, "long must PAY funding (positive cost)"
    assert t.net_pnl == pytest.approx(exp["net"], abs=1e-6)
    _assert_equity(res, exp["equity"])


def test_law6_funding_short_receives_signed_credit():
    bars, targets, folds, costs, exp = scenario_funding_short()
    res = _run(bars, targets, folds, costs)
    assert len(res.trades) == 1
    t = res.trades[0]
    assert t.funding == pytest.approx(exp["funding"], abs=1e-9)
    assert t.funding < 0.0, "short must RECEIVE funding (signed credit)"
    assert t.gross_pnl == pytest.approx(exp["gross"], abs=1e-6)
    # net includes the funding credit: net = gross - fees - slip - funding
    assert t.net_pnl == pytest.approx(exp["net"], abs=1e-6)
    _assert_equity(res, exp["equity"])


# ---------------------------------------------------------------------------
# Law 7 — one trade per position cycle; flips are close-then-open, both fills
# costed, never a netted single fill
# ---------------------------------------------------------------------------


def test_law7_flip_is_close_then_open_two_costed_fills():
    bars, targets, folds, costs, exp = scenario_flip()
    res = _run(bars, targets, folds, costs)
    assert len(res.trades) == 2  # two cycles -> exactly two trade records
    t1, t2 = res.trades
    assert t1.direction == 1 and t2.direction == -1
    assert t1.exit_reason == "regime_off"
    assert t1.exit_bar == 25 and t1.exit_ts == bars.ts_open[25]
    assert t2.entry_bar == 26 == t1.exit_bar + 1  # distinct opens, close-then-open
    assert t2.entry_ts == bars.ts_open[26] > t1.exit_ts
    assert t2.exit_reason == "fold_flat"
    assert t2.exit_ts == bars.ts_close[30]
    # both fills costed (no netting): each trade carries entry+exit fee and slip
    assert t1.fees == pytest.approx(exp["t1"]["fees"], abs=1e-6)  # 101.5
    assert t1.slip == pytest.approx(exp["t1"]["slip"], abs=1e-6)  # 20.3
    assert t2.fees == pytest.approx(exp["t2"]["fees"], abs=1e-6)
    assert t2.slip == pytest.approx(exp["t2"]["slip"], abs=1e-6)
    assert t1.net_pnl == pytest.approx(exp["t1"]["net"], abs=1e-6)  # 2878.2
    assert t2.net_pnl == pytest.approx(exp["t2"]["net"], abs=1e-6)
    assert res.totals["trades"] == 2
    assert res.totals["net_pnl"] == pytest.approx(exp["total_net"], abs=1e-6)
    _assert_equity(res, exp["equity"])
    assert res.trades[0].qty == pytest.approx(exp["qty1"], abs=1e-9)
    assert res.trades[1].qty == pytest.approx(exp["qty2"], abs=1e-9)  # 1028.782


# ---------------------------------------------------------------------------
# Law 8 — unchanged per-bar target => no reconciliation, no fill
# ---------------------------------------------------------------------------


def test_law8_noop_target_no_reconciliation_no_churn():
    bars, targets, folds, costs, exp = scenario_step_up_hold()
    res = _run(bars, targets, folds, costs)
    # constant TREND_LONG target throughout: exactly ONE entry and NO
    # reconciliation fills — the only exit is the strategy's own signal
    reasons = [t.exit_reason for t in res.trades]
    assert reasons == ["strategy_exit"]
    assert len(res.trades) == 1
    # on the holding plateau (bars 21..28, unchanged target, unchanged close)
    # equity is exactly flat: zero fills, zero costs, MTM unchanged
    for k in range(21, 29):
        assert res.equity[k] == pytest.approx(res.equity[k - 1], abs=1e-9)
        assert res.invested[k] == 1.0


# ---------------------------------------------------------------------------
# Law 9 — H1/H4 regime clock -> 15m exec bars, strictly-before-open law,
# asserted bar by bar on hand-built timelines
# ---------------------------------------------------------------------------


def test_law9_regime_clock_governing_h1():
    opens, regime_ts, labels, period, expected = h1_timeline()

    class _Grid:
        ts_open = np.array(opens, dtype=np.int64)
        ts_close = np.array([t + MIN15 for t in opens], dtype=np.int64)

    got = targets_from_regime(_Grid(), regime_ts, labels, period, MAPPING)
    assert got == expected
    # spot-boundaries (hand): strictly-before at ts_o == decision ts
    assert got[8] is None  # ts_o == R0 -> prior regime, None before first
    assert got[12] == TREND_LONG  # ts_o == R0+1h -> governed by R0 (strict)
    assert got[20] == TREND_SHORT  # ts_o == R0+3h -> governed by R0+1h
    assert got[28] == "MR_LONG"  # age exactly 2h: not stale


def test_law9_regime_clock_governing_h4():
    opens, regime_ts, labels, period, expected = h4_timeline()

    class _Grid:
        ts_open = np.array(opens, dtype=np.int64)
        ts_close = np.array([t + MIN15 for t in opens], dtype=np.int64)

    got = targets_from_regime(_Grid(), regime_ts, labels, period, MAPPING)
    assert got == expected
    assert got[0] is None  # ts_o == R0
    assert got[48] == TREND_LONG  # age exactly 8h = 2 x H4: not stale (boundary)
    assert got[80] == TREND_SHORT  # age exactly 8h after the 12h decision
    assert got[81] == FLAT  # first stale bar


def test_law9_unknown_and_unmapped_labels_map_flat():
    opens = [T0 + k * MIN15 for k in range(5)]

    class _Grid:
        ts_open = np.array(opens, dtype=np.int64)
        ts_close = np.array([t + MIN15 for t in opens], dtype=np.int64)

    got = targets_from_regime(_Grid(), [T0 + MIN15], ["TRANSITION_UNKNOWN"], HOUR, MAPPING)
    # k=0: ts_o = T0 < decision -> None; k=1: ts_o == decision (strictly-before) -> None
    assert got == [None, None, FLAT, FLAT, FLAT]
    got2 = targets_from_regime(_Grid(), [T0 + MIN15], ["MYSTERY_LABEL"], HOUR, MAPPING)
    assert got2 == [None, None, FLAT, FLAT, FLAT]  # mapping.get default


def test_law9_arms_target_grid_matches_governing_law():
    """arms._targets_from_regime_target_grid must agree with
    targets_from_regime on the same timeline (helper consistency)."""
    opens, regime_ts, labels, period, expected = h1_timeline()

    class _Grid:
        ts_open = np.array(opens, dtype=np.int64)
        ts_close = np.array([t + MIN15 for t in opens], dtype=np.int64)

    grid_targets = [MAPPING.get(l, FLAT) for l in labels]
    via_arms = arms._targets_from_regime_target_grid(_Grid(), regime_ts, grid_targets, period)
    via_engine = targets_from_regime(_Grid(), regime_ts, labels, period, MAPPING)
    assert via_arms == via_engine == expected


# ---------------------------------------------------------------------------
# Law 10 — determinism: same inputs -> byte-identical trades and equity
# ---------------------------------------------------------------------------


def test_law10_determinism_byte_identical_reruns():
    bars, targets, folds, costs, _exp = scenario_flip()
    a = _run(bars, targets, folds, costs)
    b = _run(bars, targets, folds, costs)
    assert a.equity.tobytes() == b.equity.tobytes()
    assert a.invested.tobytes() == b.invested.tobytes()
    assert a.fold_id.tobytes() == b.fold_id.tobytes()
    assert a.fold_net_pnl == b.fold_net_pnl
    assert a.totals == b.totals
    assert len(a.trades) == len(b.trades)
    for ta, tb in zip(a.trades, b.trades):
        for f in (
            "strategy", "direction", "qty", "entry_bar", "entry_ts", "entry_px",
            "exit_bar", "exit_ts", "exit_px", "exit_reason", "gross_pnl",
            "fees", "slip", "funding", "net_pnl", "fold_id",
        ):
            assert getattr(ta, f) == getattr(tb, f), f


# ---------------------------------------------------------------------------
# Law 11 — stale-data rejection: decision older than 2 regime periods -> FLAT
# (boundary equality is governed: covered inside the law-9 hand tables at
# H1 k=28 (age 2h) and H4 k=48/k=80 (age 8h); here the strict-> side)
# ---------------------------------------------------------------------------


def test_law11_stale_beyond_two_periods_maps_flat():
    opens = [T0 + k * MIN15 for k in range(12)]  # T0 .. T0+2h45m

    class _Grid:
        ts_open = np.array(opens, dtype=np.int64)
        ts_close = np.array([t + MIN15 for t in opens], dtype=np.int64)

    # single decision at T0; period 1h; stale gate 2h
    got = targets_from_regime(_Grid(), [T0], ["UPTREND"], HOUR, MAPPING)
    assert got[0] is None  # strictly-before
    assert got[8] == TREND_LONG  # age exactly 2h: NOT stale (k=8, ts_o = T0+2h)
    assert got[8] is not FLAT
    assert all(g == FLAT for g in got[9:])  # age > 2h: FLAT


# ---------------------------------------------------------------------------
# ALSO AUDIT — metrics.py churn/dwell/occupancy + equity MTM identity
# ---------------------------------------------------------------------------


def test_mtm_identity_on_flip_and_stop_scenarios():
    for scenario in (scenario_flip, scenario_stop):
        bars, targets, folds, costs, exp = scenario()
        res = _run(bars, targets, folds, costs)
        assert 100_000.0 + res.totals["net_pnl"] == pytest.approx(float(res.equity[-1]), abs=1e-9)
        assert res.totals["net_pnl"] == pytest.approx(
            sum(t.net_pnl for t in res.trades), abs=1e-9
        )


def test_metrics_turnover_and_time_in_market_hand_check():
    bars, targets, folds, costs, exp = scenario_flip()
    res = _run(bars, targets, folds, costs)
    m = compute_arm_metrics(res, bars, periods_per_year=1.0, initial_equity=100_000.0)
    avg_eq = sum(exp["equity"]) / len(exp["equity"])
    years = (float(bars.ts_close[-1]) - float(bars.ts_close[0])) / YEAR_NS
    assert m["turnover"] == pytest.approx(exp["entry_notional"] / avg_eq / years, rel=1e-9)
    assert m["time_in_market"] == pytest.approx(exp["invested_bars"] / len(exp["equity"]), abs=1e-12)
    assert m["expectancy_per_trade"] == pytest.approx(exp["total_net"] / 2, abs=1e-6)
    assert m["win_rate"] == pytest.approx(1.0, abs=1e-12)  # both flip trades are winners


def test_metrics_regime_stats_hand_case():
    rs = regime_stats_from_timeline(["A", "A", "B", "B", "B", "A", "C", "C"])
    assert rs.switches == 3  # A->B, B->A, A->C
    assert rs.occupancy == {"A": 3 / 8, "B": 3 / 8, "C": 2 / 8}
    assert rs.avg_dwell == pytest.approx((2 + 3 + 1 + 2) / 4, abs=1e-12)  # 2.0
    assert rs.unknown_share == 0.0
    rs2 = regime_stats_from_timeline(["TRANSITION_UNKNOWN"] * 4 + ["UPTREND"] * 4)
    assert rs2.unknown_share == pytest.approx(0.5, abs=1e-12)
    assert rs2.switches == 1


# ---------------------------------------------------------------------------
# Finding A5-F1 — BUY_HOLD reference violates its documented hold-to-end law
# (engine docstring: "exits only via fold force-flat"). Proven deviation:
# the engine opens the BUY_HOLD position as a plain TREND_LONG, so the trend
# exit signal closes it mid-fold ("strategy_exit") and it stays flat until
# the next fold start (re-entry only at fold starts).
# ---------------------------------------------------------------------------


@pytest.mark.xfail(
    reason="A5-F1 (MEDIUM): BUY_HOLD exits on the TREND_LONG strategy signal "
    "mid-fold and is not re-entered until the next fold start; the "
    "documented 'exits only via fold force-flat' law is not enforced "
    "by the engine",
    strict=True,
)
def test_buyhold_documented_hold_to_end_law():
    bars, targets, folds, costs, exp = scenario_buy_hold()
    res = _run(bars, targets, folds, costs)
    assert len(res.trades) == 1
    t = res.trades[0]
    # documented law: the only permitted exit is the fold force-flat
    assert t.exit_reason == "fold_flat"
    assert t.exit_bar == exp["fold_end"]
    assert t.exit_ts == bars.ts_close[exp["fold_end"]]


def test_buyhold_observed_deviation_documented():
    """Companion (PASS) test: pins the OBSERVED behavior so the deviation is
    fully characterized for the audit report and for A1."""
    bars, targets, folds, costs, exp = scenario_buy_hold()
    res = _run(bars, targets, folds, costs)
    assert len(res.trades) == 1
    t = res.trades[0]
    assert t.exit_reason == "strategy_exit"  # NOT fold_flat — the deviation
    assert t.entry_bar == 1 and t.exit_bar == 3 < exp["fold_end"]
    assert t.exit_ts == bars.ts_open[3]
    assert t.net_pnl == pytest.approx(exp["net"], abs=1e-6)  # -2118.8
    _assert_equity(res, exp["equity"])
    # after the mid-fold exit the reference sits flat through the fold end
    assert res.invested[3:].sum() == 0.0
