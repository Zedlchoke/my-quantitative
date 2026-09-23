"""Hand-computed golden fixtures for the A5 engine/cost/churn audit.

AUDIT ARTIFACT — A5 lane, cycle REGIME-STRATEGY-MAPPING-V1. Every expected
number in this module is derived BY HAND from the pinned engine laws
(rsmv1/engine.py module docstring + dispatch laws 1-11), never from engine
internals:

- costs: fee_frac = fee_bps*1e-4, cost = fee_frac * notional, computed inline;
- quantities: round(cash / price, 8);
- equity path: equity[i] = cash_i + dir*qty*close_i traced bar by bar;
- regime targets: strictly-before-open governing law + 2-period staleness,
  tabulated bar by bar by hand.

Money assertions use 1e-6 absolute tolerance (bps-scale float noise is
~1e-11 relative); structure (bar indices, timestamps, reasons, counts) is
exact. Bar grids are 15-minute UTC bars with ts_close = ts_open + 15m (the
data.py snap convention). Signals referenced in comments are hand-derived
EMA inequalities (e.g. bar 19 of scenario A: close 102 > ema20 = 100 +
2*(2/21) = 100.190476... > ema50 = 100 + 2*(2/51) = 100.078431...), which
hold by wide, unambiguous margins.

Synthetic fixtures only — no real-corpus data, no runtime/ or evidence/
reads, no Jev calls (A5 scope).
"""

from __future__ import annotations

import datetime as dt

import numpy as np

from rsmv1.data import Bars
from rsmv1.engine import BUY_HOLD, CostModel, folds_from_regime_ts
from rsmv1.strategies import FLAT, MR_LONG, TREND_LONG, TREND_SHORT

NS = 1_000_000_000
MIN15 = 900 * NS
HOUR = 3_600 * NS
YEAR_NS = 365.25 * 86400 * NS  # metrics.py year convention

# Fixed epoch: 2025-09-01T00:00:00Z (any UTC midnight; frozen for reproducibility)
T0 = int(dt.datetime(2025, 9, 1, tzinfo=dt.timezone.utc).timestamp()) * NS

# Frozen cost models (mapping_arms_freeze.json — DECLARED_CONSERVATIVE_BOUND
# / FROZEN_BAND_MODEL_F6). The engine sees whatever CostModel it is given;
# these are the production values.
BTC_FEE_BPS, BTC_SLIP_BPS = 5.0, 1.0
SPY_FEE_BPS, SPY_SLIP_BPS = 10.0, 0.0  # all-in band booked as fees, zero slip
FUNDING_PER_8H = 1.377e-05

BTC_COSTS = CostModel(fee_bps=BTC_FEE_BPS, slip_bps=BTC_SLIP_BPS, funding_rate=0.0, label="BTC frozen")
BTC_COSTS_FUND = CostModel(
    fee_bps=BTC_FEE_BPS, slip_bps=BTC_SLIP_BPS, funding_rate=FUNDING_PER_8H, label="BTC frozen + funding"
)
SPY_COSTS = CostModel(fee_bps=SPY_FEE_BPS, slip_bps=SPY_SLIP_BPS, funding_rate=0.0, label="SPY band")

BTC_FEE = BTC_FEE_BPS * 1e-4  # 5e-4 per side
BTC_SLIP = BTC_SLIP_BPS * 1e-4  # 1e-4 per side
SPY_FEE = SPY_FEE_BPS * 1e-4  # 1e-3 per side

# Frozen BTC mapping (mapping_arms_freeze.json)
MAPPING = {
    "ACCUMULATION": MR_LONG,
    "DISTRIBUTION": FLAT,
    "DOWNTREND": TREND_SHORT,
    "TRANSITION_UNKNOWN": FLAT,
    "UPTREND": TREND_LONG,
}

MONEY_TOL = 1e-6


def mk_bars(rows: list[tuple[float, float, float, float]], t0: int = T0, step: int = MIN15) -> Bars:
    """rows of (open, high, low, close); ts_open[i] = t0 + i*step."""
    n = len(rows)
    return Bars(
        ts_open=np.array([t0 + i * step for i in range(n)], dtype=np.int64),
        ts_close=np.array([t0 + (i + 1) * step for i in range(n)], dtype=np.int64),
        open=np.array([r[0] for r in rows], dtype=np.float64),
        high=np.array([r[1] for r in rows], dtype=np.float64),
        low=np.array([r[2] for r in rows], dtype=np.float64),
        close=np.array([r[3] for r in rows], dtype=np.float64),
        volume=np.zeros(n, dtype=np.float64),
    )


def money(x: float) -> float:
    return x


# ---------------------------------------------------------------------------
# Scenario A: step-up entry, hold on plateau, trend exit — next-bar-open +
# one costed round trip under BTC costs (and the SPY band under SPY costs).
# Hand derivation (EMA seeded with first close, alpha=2/21 and 2/51):
#   bar 19  close 102 > ema20 = 100.190476... > ema50 = 100.078431  -> entry signal
#   bar 20  fill at open 100 (NOT on bar 19)
#   bars 21-28  close 102 > ema20 (< 102, converging) -> hold, no exit signal
#   bar 29  close 101.0 < ema20 = 102 - 2*(19/21)^11 = 101.335076   -> exit signal
#   bar 30  exit fill at open 100 (NOT on bar 29)
# Stop (enabled, = 100 - 3*ATR14[19] = 100 - 3*(2/14) = 99.571428...) never
# triggers: lows on held bars are 102 / 101.2, and bar 30's low 99.5 is
# irrelevant because the exit fills at that bar's OPEN (before stop checks).
# ---------------------------------------------------------------------------
def scenario_step_up_hold():
    rows = (
        [(100.0, 100.0, 100.0, 100.0)] * 19  # 0..18 flat; close > ema20 is FALSE here (strict)
        + [(100.0, 101.0, 99.0, 102.0)]  # 19 signal bar
        + [(100.0, 102.0, 100.0, 102.0)]  # 20 entry bar, open = 100
        + [(102.0, 102.0, 102.0, 102.0)] * 8  # 21..28 hold
        + [(102.0, 102.0, 101.2, 101.0)]  # 29 exit-signal bar (low stays above stop)
        + [(100.0, 101.0, 99.5, 100.0)]  # 30 exit fill at open 100
        + [(100.0, 100.0, 100.0, 100.0)] * 3  # 31..33
    )
    bars = mk_bars(rows)
    n = len(rows)
    qty = round(100_000.0 / 100.0, 8)  # 1000.0
    entry_fee = money(BTC_FEE * qty * 100.0)  # 50
    entry_slip = money(BTC_SLIP * qty * 100.0)  # 10
    cash_after_entry = 100_000.0 - qty * 100.0 - entry_fee - entry_slip  # -60
    exit_fee = money(BTC_FEE * qty * 100.0)  # 50 (exit fill also at 100)
    exit_slip = money(BTC_SLIP * qty * 100.0)  # 10
    exp = {
        "qty": qty,
        "entry_fee": entry_fee,
        "entry_slip": entry_slip,
        "cash_after_entry": cash_after_entry,
        "exit_fee": exit_fee,
        "exit_slip": exit_slip,
        "gross": 0.0,
        "fees": entry_fee + exit_fee,  # 100
        "slip": entry_slip + exit_slip,  # 20
        "net": -(entry_fee + exit_fee) - (entry_slip + exit_slip),  # -120
        # hand equity path: cash + dir*qty*close
        # bars 20..28 close 102; bar 29 close 101 (exit-signal bar); bars 30..33 flat
        "equity": [100_000.0] * 20
        + [cash_after_entry + qty * 102.0] * 9
        + [cash_after_entry + qty * 101.0]
        + [100_000.0 + (-(entry_fee + exit_fee) - (entry_slip + exit_slip))] * 4,
        "entry_bar": 20,
        "exit_bar": 30,
        "entry_ts": bars.ts_open[20],
        "exit_ts": bars.ts_open[30],
    }
    return bars, [TREND_LONG] * n, [(0, 0, n - 1)], BTC_COSTS, exp


def scenario_step_up_hold_spy():
    """Same bars under the SPY band model: fees only, zero slippage."""
    bars, targets, folds, _costs, exp = scenario_step_up_hold()
    qty = exp["qty"]
    fee_side = money(SPY_FEE * qty * 100.0)  # 100 per side
    net = -(2 * fee_side)
    exp = dict(exp)
    exp.update(
        {
            "entry_fee": fee_side,
            "entry_slip": 0.0,
            "cash_after_entry": 100_000.0 - qty * 100.0 - fee_side,  # -100
            "exit_fee": fee_side,
            "exit_slip": 0.0,
            "fees": 2 * fee_side,
            "slip": 0.0,
            "net": net,  # -200
            "equity": [100_000.0] * 20
            + [(100_000.0 - qty * 100.0 - fee_side) + qty * 102.0] * 9
            + [(100_000.0 - qty * 100.0 - fee_side) + qty * 101.0]
            + [100_000.0 + net] * 4,
        }
    )
    return bars, targets, folds, SPY_COSTS, exp


# ---------------------------------------------------------------------------
# Scenario C: intrabar stop. Bars 0..19 carry TR = 2 exactly
# (h=101, l=99, c=100: TR_0 = 2; TR_t = max(2, |101-100|, |99-100|) = 2;
# bar 19 h=101.25/l=99.25/c=100.5: TR = max(2, 1.25, 0.75) = 2), so Wilder
# ATR14 = SMA of the fourteen TRs = 2.0 from index 13 through 19.
#   bar 19  close 100.5 > ema20 = 100.047619... > ema50 = 100.019608 -> signal
#   bar 20  entry at open 100; stop = 100 - 3*2 = 94. Entry-bar low is 94
#           (<= stop) — if stops were evaluated on the entry bar this would
#           stop out instantly; the pinned law says entry bar is excluded.
#   bar 21  low 94 <= stop -> fill AT the stop price 94, stamped at
#           ts_open[21], with fee+slip debited on the 94 notional.
#   bars 22..29 close 95 < ema20 (decaying 99.56 -> 96.80) -> no re-entry.
# ---------------------------------------------------------------------------
def scenario_stop():
    rows = (
        [(100.0, 101.0, 99.0, 100.0)] * 19  # 0..18, TR = 2 each
        + [(100.0, 101.25, 99.25, 100.5)]  # 19 signal bar, TR still 2 -> ATR14[19] = 2
        + [(100.0, 100.0, 94.0, 101.0)]  # 20 entry bar, open 100, low AT stop
        + [(100.0, 100.0, 94.0, 95.0)]  # 21 stop bar
        + [(95.0, 95.0, 95.0, 95.0)] * 8  # 22..29
    )
    bars = mk_bars(rows)
    n = len(rows)
    qty = round(100_000.0 / 100.0, 8)
    entry_fee = money(BTC_FEE * qty * 100.0)
    entry_slip = money(BTC_SLIP * qty * 100.0)
    cash_after_entry = 100_000.0 - qty * 100.0 - entry_fee - entry_slip
    stop_px = 100.0 - 3.0 * 2.0  # 94
    exit_fee = money(BTC_FEE * qty * stop_px)  # 5e-4 * 94000 = 47
    exit_slip = money(BTC_SLIP * qty * stop_px)  # 1e-4 * 94000 = 9.4
    gross = (stop_px - 100.0) * qty  # -6000
    net = gross - (entry_fee + exit_fee) - (entry_slip + exit_slip)  # -6116.4
    exp = {
        "qty": qty,
        "stop_px": stop_px,
        "entry_fee": entry_fee,
        "exit_fee": exit_fee,
        "fees": entry_fee + exit_fee,  # 97
        "slip": entry_slip + exit_slip,  # 19.4
        "gross": gross,
        "net": net,
        "cash_after_entry": cash_after_entry,
        "equity": [100_000.0] * 20
        + [cash_after_entry + qty * 101.0]  # bar 20, close 101
        + [100_000.0 + net] * 9,  # bars 21..29
        "entry_bar": 20,
        "exit_bar": 21,
        "exit_ts": bars.ts_open[21],
    }
    return bars, [TREND_LONG] * n, [(0, 0, n - 1)], BTC_COSTS, exp


# ---------------------------------------------------------------------------
# Scenario D: regime-off exit at the NEXT open. Same entry as A; targets flip
# to FLAT after the entry bar:
#   bar 21  reconciliation at open 101 (reason "regime_off") — BEFORE the
#           stop check at that bar (low 100 would not trigger anyway).
#   bars 22..29  FLAT target -> no re-entry possible.
# ---------------------------------------------------------------------------
def scenario_regime_off():
    rows = (
        [(100.0, 100.0, 100.0, 100.0)] * 19
        + [(100.0, 101.0, 99.0, 102.0)]  # 19 signal
        + [(100.0, 102.0, 100.0, 102.0)]  # 20 entry at open 100
        + [(101.0, 101.0, 100.0, 101.0)]  # 21 regime_off at open 101
        + [(101.0, 101.0, 101.0, 101.0)] * 8  # 22..29
    )
    bars = mk_bars(rows)
    n = len(rows)
    qty = round(100_000.0 / 100.0, 8)
    entry_fee = money(BTC_FEE * qty * 100.0)
    entry_slip = money(BTC_SLIP * qty * 100.0)
    exit_fee = money(BTC_FEE * qty * 101.0)  # 50.5
    exit_slip = money(BTC_SLIP * qty * 101.0)  # 10.1
    gross = (101.0 - 100.0) * qty  # 1000
    net = gross - (entry_fee + exit_fee) - (entry_slip + exit_slip)  # 879.4
    targets = [TREND_LONG] * 21 + [FLAT] * (n - 21)
    exp = {
        "qty": qty,
        "gross": gross,
        "fees": entry_fee + exit_fee,  # 100.5
        "slip": entry_slip + exit_slip,  # 20.1
        "net": net,
        "cash_after_entry": 100_000.0 - qty * 100.0 - entry_fee - entry_slip,
        "equity": [100_000.0] * 20
        + [(100_000.0 - qty * 100.0 - entry_fee - entry_slip) + qty * 102.0]  # bar 20
        + [100_000.0 + net] * 9,  # bars 21..29
        "entry_bar": 20,
        "exit_bar": 21,
        "exit_ts": bars.ts_open[21],
        "exit_px": 101.0,
    }
    return bars, targets, [(0, 0, n - 1)], BTC_COSTS, exp


def scenario_entry_dropped_when_target_vanishes():
    """Signal queued at bar 19 close, but targets[20] = FLAT: the entry is
    dropped at the next open (no fill into a non-matching target)."""
    rows = (
        [(100.0, 100.0, 100.0, 100.0)] * 19
        + [(100.0, 101.0, 99.0, 102.0)]  # 19 signal
        + [(100.0, 102.0, 100.0, 102.0)]  # 20 target already FLAT -> no fill
        + [(100.0, 100.0, 100.0, 100.0)] * 9
    )
    bars = mk_bars(rows)
    n = len(rows)
    targets = [TREND_LONG] * 20 + [FLAT] * (n - 20)
    return bars, targets, [(0, 0, n - 1)], BTC_COSTS, {"n": n}


# ---------------------------------------------------------------------------
# Scenario E: direction flip TREND_LONG -> TREND_SHORT = close-then-open.
#   bar 19  close 102 > ema20 = 100.190476 > ema50 = 100.078431 -> long signal
#           (TR_19 = 2 with only TR_19 nonzero so far -> ATR14[19] = 2/14,
#            long stop = 100 - 3/7 = 99.571428...)
#   bar 20  long entry at open 100
#   bars 21-24  close 102, hold (ema20 < ema50 order still long-side)
#   bar 25  targets flip to TREND_SHORT: open 103 -> long regime_off at 103;
#           close 90 crashes below ema20 (= 99.8646) and ema20 < ema50
#           (= 100.0176) -> short entry signal at THIS close
#   bar 26  short entry at open 100, qty = round(cash/100, 8) with
#           cash = 102878.2 -> qty = 1028.782; short stop =
#           100 + 3*ATR14[25] ~ 103.1 (highs <= 100 never reach it)
#   bars 27-29  close 95 < ema20 (99.41 -> 98.61) -> no short exit
#   bar 30  fold end -> force-flat at close 95 (exit_ts = ts_close[30])
# ---------------------------------------------------------------------------
def scenario_flip():
    rows = (
        [(100.0, 100.0, 100.0, 100.0)] * 19
        + [(100.0, 102.0, 100.0, 102.0)]  # 19 signal
        + [(100.0, 102.0, 100.0, 102.0)]  # 20 long entry at open 100
        + [(102.0, 102.0, 102.0, 102.0)] * 4  # 21..24
        + [(103.0, 103.0, 90.0, 90.0)]  # 25 regime_off at open 103; short signal at close
        + [(100.0, 100.0, 95.0, 95.0)]  # 26 short entry at open 100; close 95 < ema20 (no exit)
        + [(95.0, 95.0, 95.0, 95.0)] * 3  # 27..29
        + [(95.0, 95.0, 95.0, 95.0)]  # 30 fold end
    )
    bars = mk_bars(rows)
    n = len(rows)
    targets = [TREND_LONG] * 25 + [TREND_SHORT] * (n - 25)

    qty1 = round(100_000.0 / 100.0, 8)  # 1000
    t1_entry_fee = money(BTC_FEE * qty1 * 100.0)  # 50
    t1_entry_slip = money(BTC_SLIP * qty1 * 100.0)  # 10
    cash0 = 100_000.0 - qty1 * 100.0 - t1_entry_fee - t1_entry_slip  # -60
    t1_exit_fee = money(BTC_FEE * qty1 * 103.0)  # 51.5
    t1_exit_slip = money(BTC_SLIP * qty1 * 103.0)  # 10.3
    t1_gross = (103.0 - 100.0) * qty1  # 3000
    t1_net = t1_gross - (t1_entry_fee + t1_exit_fee) - (t1_entry_slip + t1_exit_slip)  # 2878.2
    cash1 = cash0 + qty1 * 103.0 - ((t1_entry_fee + t1_exit_fee) + (t1_entry_slip + t1_exit_slip) - (t1_entry_fee + t1_entry_slip))
    # cash1 = 102878.2 (hand: -60 + 103000 - 61.8)

    qty2 = round(cash1 / 100.0, 8)  # 1028.782
    t2_entry_fee = money(BTC_FEE * qty2 * 100.0)
    t2_entry_slip = money(BTC_SLIP * qty2 * 100.0)
    cash2 = cash1 + qty2 * 100.0 - t2_entry_fee - t2_entry_slip  # short entry credits notional
    exit_notional2 = qty2 * 95.0
    t2_exit_fee = money(BTC_FEE * exit_notional2)
    t2_exit_slip = money(BTC_SLIP * exit_notional2)
    t2_gross = (95.0 - 100.0) * (-1.0) * qty2  # 5143.91
    t2_net = t2_gross - (t2_entry_fee + t2_exit_fee) - (t2_entry_slip + t2_exit_slip)
    total_net = t1_net + t2_net

    eq_long_held = cash0 + qty1 * 102.0  # bars 20..24 = 101940
    eq_short_held = cash2 - qty2 * 95.0  # bars 26..29
    exp = {
        "qty1": qty1,
        "qty2": qty2,
        "t1": {
            "entry_bar": 20,
            "exit_bar": 25,
            "entry_ts": bars.ts_open[20],
            "exit_ts": bars.ts_open[25],
            "exit_px": 103.0,
            "gross": t1_gross,
            "fees": t1_entry_fee + t1_exit_fee,  # 101.5
            "slip": t1_entry_slip + t1_exit_slip,  # 20.3
            "net": t1_net,
        },
        "t2": {
            "entry_bar": 26,
            "exit_bar": 30,
            "entry_ts": bars.ts_open[26],
            "exit_ts": bars.ts_close[30],  # force-flat at close
            "exit_px": 95.0,
            "gross": t2_gross,
            "fees": t2_entry_fee + t2_exit_fee,
            "slip": t2_entry_slip + t2_exit_slip,
            "net": t2_net,
        },
        "total_net": total_net,
        "avg_eq_numerator": (20 * 100_000.0)  # bars 0..19
        + (5 * eq_long_held)  # bars 20..24
        + cash1  # bar 25
        + (4 * eq_short_held)  # bars 26..29
        + (cash2 - exit_notional2 - (t2_exit_fee + t2_exit_slip)),  # bar 30
        "equity": [100_000.0] * 20
        + [eq_long_held] * 5
        + [cash1]
        + [eq_short_held] * 4
        + [cash2 - exit_notional2 - (t2_exit_fee + t2_exit_slip)],
        "entry_notional": qty1 * 100.0 + qty2 * 100.0,
        "invested_bars": 9,  # bars 20..24 and 26..29
    }
    return bars, targets, [(0, 0, n - 1)], BTC_COSTS, exp


# ---------------------------------------------------------------------------
# Scenario F: fold law. 20 exec bars; frozen spans hand-placed so fold 0
# starts at bar 8 (first exec bar strictly after span start = ts_open[7])
# and fold 1 at bar 18. Contiguous partition: fold 0 OWNS bars 8..17
# (through the bar before fold 1's start), fold 1 owns 18..19; bars 0..7 are
# the pre-warmup tag (-1). Entry signals on unassigned bars are refused.
#   bar 5   close 102 signal on UNASSIGNED bar -> queued, fill REFUSED at bar 6
#   bar 9   close 102 signal on assigned bar -> entry at open[10] = 100
#           (stop disabled: ATR14 is NaN before index 13)
#   bars 10..16 close 100.5 > ema20 (converging up to 100.5 from below) -> hold
#   bar 17  fold 0 END -> force-flat at close 100 (= close, kept BELOW ema20
#           so no fresh entry signal fires at the fold boundary)
#   bars 18..19 fold 1, close 100 < ema20 -> no entry; fold 1 PnL = 0
# ---------------------------------------------------------------------------
def scenario_folds():
    rows = (
        [(100.0, 100.0, 100.0, 100.0)] * 5  # 0..4 unassigned
        + [(100.0, 101.0, 99.0, 102.0)]  # 5 signal on UNASSIGNED bar
        + [(100.0, 100.0, 100.0, 100.0)] * 3  # 6..8 (8 = fold 0 start)
        + [(100.0, 101.0, 99.0, 102.0)]  # 9 signal (assigned)
        + [(100.0, 100.75, 100.25, 100.5)]  # 10 entry at open 100
        + [(100.5, 100.5, 100.5, 100.5)] * 6  # 11..16
        + [(100.0, 100.0, 100.0, 100.0)]  # 17 fold 0 end: force-flat at close 100
        + [(100.0, 100.0, 100.0, 100.0)] * 2  # 18..19 fold 1
    )
    bars = mk_bars(rows)
    n = len(rows)
    folds = folds_from_regime_ts(bars, [(T0 + 7 * MIN15, T0 + 20 * MIN15), (T0 + 17 * MIN15, T0 + 20 * MIN15)])
    assert folds == [(0, 8, 17), (1, 18, 19)], folds  # hand-derived partition

    qty = round(100_000.0 / 100.0, 8)
    entry_fee = money(BTC_FEE * qty * 100.0)
    entry_slip = money(BTC_SLIP * qty * 100.0)
    cash_after_entry = 100_000.0 - qty * 100.0 - entry_fee - entry_slip
    exit_fee = money(BTC_FEE * qty * 100.0)  # force-flat fill at close 100
    exit_slip = money(BTC_SLIP * qty * 100.0)
    gross = 0.0
    net = gross - (entry_fee + exit_fee) - (entry_slip + exit_slip)  # -120
    exp = {
        "folds": folds,
        "fold_id": [-1] * 8 + [0] * 10 + [1] * 2,
        "qty": qty,
        "gross": gross,
        "fees": entry_fee + exit_fee,  # 100
        "slip": entry_slip + exit_slip,  # 20
        "net": net,
        "fold_net": [net, 0.0],
        "equity": [100_000.0] * 10
        + [cash_after_entry + qty * 100.5] * 7  # bars 10..16, close 100.5
        + [100_000.0 + net] * 3,  # bars 17..19
        "entry_bar": 10,
        "exit_bar": 17,
        "exit_ts": bars.ts_close[17],
        "first_fold_start": 8,
    }
    return bars, [TREND_LONG] * n, folds, BTC_COSTS, exp


# ---------------------------------------------------------------------------
# Scenario G: BTC funding. Grid anchored at UTC midnight so 8h boundaries are
# bar opens. Entry fills at open of bar 31 = 07:45Z; funding boundaries:
# 08:00Z (charged on the entry bar, ref = close of bar 31) and 16:00Z
# (charged on bar 63 = 15:45-16:00 whose ts_close IS the boundary, ref =
# close of bar 63). Exit (regime_off) at open of bar 64 = 16:00Z charges
# nothing further (funding_up_to already 16:00Z). Longs pay (+), shorts
# receive (-).
# ---------------------------------------------------------------------------
def _funding_grid(long_side: bool) -> tuple:
    """Shared grid: flat 100 bars 0..29, signal bar 30, entry bar 31 (07:45Z),
    hold bars 32..63, exit bar 64 (16:00Z), tail bars 65..69.

    Funding refs (hand-pinned): the 08:00Z boundary is charged on the entry
    bar with ref = close of bar 31; the 16:00Z boundary is charged on bar 63
    (ts_close == 16:00Z) with ref = close of bar 63. Long: both refs 102.
    Short: both refs 98. Exit (regime_off at open of bar 64) charges nothing
    further."""
    if long_side:
        signal = (100.0, 101.0, 99.0, 102.0)
        entry_bar = (100.0, 102.0, 100.0, 102.0)  # entry at open 100, close 102 (funding ref)
        hold = (102.0, 102.0, 102.0, 102.0)  # bar 63 closes AT 16:00Z (funding ref)
        exit_bar = (100.0, 101.0, 99.0, 100.0)  # regime_off at open 100 (16:00Z)
        tail_c = 100.0
    else:
        signal = (100.0, 100.0, 98.0, 98.0)
        entry_bar = (100.0, 101.0, 98.0, 98.0)  # entry at open 100, close 98 (funding ref)
        hold = (98.0, 98.0, 98.0, 98.0)
        exit_bar = (98.0, 98.0, 97.0, 98.0)  # regime_off at open 98
        tail_c = 98.0
    rows = (
        [(100.0, 100.0, 100.0, 100.0)] * 30
        + [signal]  # 30
        + [entry_bar]  # 31 (07:45Z)
        + [hold] * 32  # 32..63 (63 closes AT 16:00Z)
        + [exit_bar]  # 64 (16:00Z)
        + [(tail_c, tail_c, tail_c, tail_c)] * 5  # 65..69
    )
    return rows


def scenario_funding_long():
    rows = _funding_grid(long_side=True)
    bars = mk_bars(rows)
    n = len(rows)
    targets = [TREND_LONG] * 64 + [FLAT] * (n - 64)
    qty = round(100_000.0 / 100.0, 8)
    entry_fee = money(BTC_FEE * qty * 100.0)
    entry_slip = money(BTC_SLIP * qty * 100.0)
    f1 = money(FUNDING_PER_8H * 1.0 * qty * 102.0)  # 08:00Z event, ref = close of bar 31
    f2 = money(FUNDING_PER_8H * 1.0 * qty * 102.0)  # 16:00Z event, ref = close of bar 63
    funding = f1 + f2  # long PAYS
    exit_fee = money(BTC_FEE * qty * 100.0)
    exit_slip = money(BTC_SLIP * qty * 100.0)
    net = 0.0 - (entry_fee + exit_fee) - (entry_slip + exit_slip) - funding
    cash_after_entry = 100_000.0 - qty * 100.0 - entry_fee - entry_slip
    exp = {
        "qty": qty,
        "funding": funding,
        "fees": entry_fee + exit_fee,
        "slip": entry_slip + exit_slip,
        "net": net,
        "equity": [100_000.0] * 31
        + [cash_after_entry + qty * 102.0] * 33  # bars 31..63
        + [100_000.0 + net] * 6,  # bars 64..69
        "entry_bar": 31,
        "entry_ts": bars.ts_open[31],  # 07:45Z — first boundary 08:00Z is strictly after
        "exit_bar": 64,
        "exit_ts": bars.ts_open[64],  # 16:00Z
    }
    return bars, targets, [(0, 0, n - 1)], BTC_COSTS_FUND, exp


def scenario_funding_short():
    rows = _funding_grid(long_side=False)
    bars = mk_bars(rows)
    n = len(rows)
    targets = [TREND_SHORT] * 64 + [FLAT] * (n - 64)
    qty = round(100_000.0 / 100.0, 8)
    entry_fee = money(BTC_FEE * qty * 100.0)
    entry_slip = money(BTC_SLIP * qty * 100.0)
    f1 = money(FUNDING_PER_8H * (-1.0) * qty * 98.0)  # short RECEIVES (signed credit)
    f2 = money(FUNDING_PER_8H * (-1.0) * qty * 98.0)
    funding = f1 + f2  # negative
    exit_fee = money(BTC_FEE * qty * 98.0)
    exit_slip = money(BTC_SLIP * qty * 98.0)
    gross = (98.0 - 100.0) * (-1.0) * qty  # 2000
    net = gross - (entry_fee + exit_fee) - (entry_slip + exit_slip) - funding  # funding credit adds
    cash_after_entry = 100_000.0 + qty * 100.0 - entry_fee - entry_slip  # short credits notional
    exp = {
        "qty": qty,
        "funding": funding,
        "fees": entry_fee + exit_fee,  # 99
        "slip": entry_slip + exit_slip,  # 19.8
        "gross": gross,
        "net": net,
        "equity": [100_000.0] * 31
        + [cash_after_entry - qty * 98.0] * 33  # bars 31..63
        + [100_000.0 + net] * 6,
        "entry_bar": 31,
        "exit_bar": 64,
    }
    return bars, targets, [(0, 0, n - 1)], BTC_COSTS_FUND, exp


# ---------------------------------------------------------------------------
# Scenario H: BUY_HOLD reference. The engine module docstring pins BUY_HOLD
# as "enters TREND_LONG at the first exec bar open of each fold, exits only
# via fold force-flat". Observed engine behavior differs (finding A5-F1):
# the position is opened as a plain TREND_LONG and exits on the trend exit
# signal, then stays flat (re-entry only at fold starts).
#   bar 0   fold start -> entry queued; fills at open[1] = 100
#   bar 2   close 98 < ema20 = 99.809519... -> trend exit signal
#   bar 3   exit at open 98 (reason "strategy_exit"), fold ends at bar 19
#   bars 4..19  flat; NO re-entry (bar 3 is not a fold start)
# ---------------------------------------------------------------------------
def scenario_buy_hold():
    rows = (
        [(100.0, 100.0, 100.0, 100.0)] * 2  # 0 (fold start), 1 (entry at open 100)
        + [(100.0, 100.0, 98.0, 98.0)]  # 2 exit signal
        + [(98.0, 98.0, 98.0, 98.0)]  # 3 exit at open 98
        + [(98.0, 98.0, 98.0, 98.0)] * 16  # 4..19
    )
    bars = mk_bars(rows)
    n = len(rows)
    targets = [BUY_HOLD] * n
    qty = round(100_000.0 / 100.0, 8)
    entry_fee = money(BTC_FEE * qty * 100.0)
    entry_slip = money(BTC_SLIP * qty * 100.0)
    exit_fee = money(BTC_FEE * qty * 98.0)
    exit_slip = money(BTC_SLIP * qty * 98.0)
    gross = (98.0 - 100.0) * qty
    net = gross - (entry_fee + exit_fee) - (entry_slip + exit_slip)  # -2118.8
    cash_after_entry = 100_000.0 - qty * 100.0 - entry_fee - entry_slip
    exp = {
        "qty": qty,
        "net": net,
        "equity": [100_000.0]
        + [cash_after_entry + qty * 100.0]  # bar 1
        + [cash_after_entry + qty * 98.0]  # bar 2
        + [100_000.0 + net] * 17,  # bars 3..19
        "entry_bar": 1,
        "exit_bar": 3,
        "fold_end": 19,
    }
    return bars, targets, [(0, 0, n - 1)], BTC_COSTS, exp


# ---------------------------------------------------------------------------
# Regime-clock governing law (laws 9/11): hand tables. H1 period = 1h,
# H4 period = 4h; staleness gate = 2 periods (strictly greater maps FLAT);
# governing decision = latest regime close STRICTLY BEFORE the exec open.
# ---------------------------------------------------------------------------
H1_PERIOD = HOUR
H4_PERIOD = 4 * HOUR


def h1_timeline():
    """Decisions at R0, R0+1h, R0+3h; exec opens T0+8h .. T0+18h (41 bars).

    Hand table (k = exec bar index, ts_o = T0+8h+k*15m):
      k 0..8   ts_o <= R0=T0+10h                 -> None (k=8: ts_o == R0, strictly-before law)
      k 9..12  R0 < ts_o <= R0+1h (gov R0)       -> UPTREND -> TREND_LONG (k=12: ts_o == R0+1h)
      k 13..20 R0+1h < ts_o <= R0+3h (gov R0+1h) -> DOWNTREND -> TREND_SHORT (k=20: ts_o == R0+3h, age 2h: NOT stale)
      k 21..28 R0+3h < ts_o <= R0+5h (gov R0+3h) -> ACCUMULATION -> MR_LONG (k=28: ts_o == R0+5h, age exactly 2h: NOT stale)
      k 29..40 ts_o > R0+5h, age > 2h            -> FLAT (stale)
    """
    r = [T0 + 10 * HOUR, T0 + 11 * HOUR, T0 + 13 * HOUR]
    labels = ["UPTREND", "DOWNTREND", "ACCUMULATION"]
    opens = [T0 + 8 * HOUR + k * MIN15 for k in range(41)]
    expected = (
        [None] * 9
        + [TREND_LONG] * 4
        + [TREND_SHORT] * 8
        + [MR_LONG] * 8
        + [FLAT] * 12
    )
    return opens, r, labels, H1_PERIOD, expected


def h4_timeline():
    """Decisions at R0=T0, R0+4h, R0+12h; exec opens T0 .. T0+24h (97 bars).

    Hand table:
      k 0       ts_o == R0                       -> None (strictly-before)
      k 1..16   R0 < ts_o <= R0+4h (gov R0)      -> UPTREND -> TREND_LONG
      k 17..48  gov R0+4h, age 4h..8h            -> UPTREND -> TREND_LONG
                (k=48: ts_o == R0+12h, age exactly 8h = 2 periods: NOT stale)
      k 49..80  gov R0+12h, age 15m..8h          -> DOWNTREND -> TREND_SHORT
                (k=80: ts_o == R0+20h, age exactly 8h: NOT stale)
      k 81..96  age > 8h                          -> FLAT (stale)
    """
    r = [T0, T0 + 4 * HOUR, T0 + 12 * HOUR]
    labels = ["UPTREND", "UPTREND", "DOWNTREND"]
    opens = [T0 + k * MIN15 for k in range(97)]
    expected = (
        [None]
        + [TREND_LONG] * 16
        + [TREND_LONG] * 32
        + [TREND_SHORT] * 32
        + [FLAT] * 16
    )
    return opens, r, labels, H4_PERIOD, expected
