"""A4 specialist library -> executable StrategySpecs (frozen parameters).

Every parameter below is copied VERBATIM from
freezes/specialist_library_proposal.json (A4 outcome-blind architect;
A1 froze it). No value here may be tuned against any outcome; any change
requires a new freeze + fresh audit.

Specialists (<= 2/regime; SPY long/flat only; UNK fixed FLAT):
  ACC-BASE-RECLAIM-L  long  BTC+SPY  failed-low reclaim -> SMA20 mean
  UPT-DIPBUY-L        long  BTC+SPY  EMA20 dip held inside EMA20>EMA50
  UPT-BREAKOUT-L      long  BTC+SPY  20-bar high close breakout, 10-bar exit
  DIS-FAILED-HIGH-S   short BTC only  failed-high upthrust -> SMA20 cover
  DNT-CASCADE-S       short BTC only  20-bar breakdown inside EMA20<EMA50
  DNT-RALLY-SOLD-S    short BTC only  rally to EMA20 rejected

A4 exit precedence (implemented by the engine): intrabar stop + fold-flat
never suppressed; regime-bar time stop never suppressed; RULE exits
suppressed until min_hold_regime_bars (=6) elapse.
"""

from __future__ import annotations

import numpy as np

from .data import Bars
from .specialist_engine import StrategySpec
from .strategies import ExecIndicators, exec_indicators

MIN_HOLD_REGIME_BARS = 6
ACC_MAX_HOLD = 24
DIS_MAX_HOLD = 24
DNT_RALLY_MAX_HOLD = 24
STRUCT_STOP_ATR = 0.5
TREND_STOP_ATR = 3.0


def trailing_max(arr: np.ndarray, window: int) -> np.ndarray:
    """HH(i,n): highest of the n COMPLETED bars i-1..i-n (excludes bar i,
    PIT law). NaN until i >= window."""
    out = np.full(arr.shape[0], np.nan)
    for i in range(arr.shape[0]):
        if i >= window:
            out[i] = float(np.max(arr[i - window : i]))
    return out


def trailing_min(arr: np.ndarray, window: int) -> np.ndarray:
    out = np.full(arr.shape[0], np.nan)
    for i in range(arr.shape[0]):
        if i >= window:
            out[i] = float(np.min(arr[i - window : i]))
    return out


class SpecialistIndicators:
    """Precomputed trailing windows + EMAs + ATR + SMA20 for one Bars set."""

    def __init__(self, bars: Bars) -> None:
        self.x: ExecIndicators = exec_indicators(bars)
        self.hh20 = trailing_max(bars.high, 20)
        self.ll20 = trailing_min(bars.low, 20)
        self.hh10 = trailing_max(bars.high, 10)
        self.ll10 = trailing_min(bars.low, 10)
        self.sma20 = self.x.boll_mid  # BOLL(20,2) mid == SMA20
        self.high = bars.high
        self.low = bars.low
        self.close = bars.close


def build_specs(bars: Bars) -> dict[str, StrategySpec]:
    ind = SpecialistIndicators(bars)
    x, hh20, ll20, hh10, ll10, sma20 = (
        ind.x, ind.hh20, ind.ll20, ind.hh10, ind.ll10, ind.sma20,
    )
    high, low, close = ind.high, ind.low, ind.close

    def _fin(v: float) -> bool:
        return bool(np.isfinite(v))

    # -- ACC-BASE-RECLAIM-L -------------------------------------------------
    def acc_entry(i, b, xi):
        return (
            _fin(ll20[i]) and _fin(sma20[i])
            and float(low[i]) < ll20[i]
            and float(close[i]) > ll20[i]
            and float(close[i]) < sma20[i]
        )

    def acc_exit(i, b, xi, held):
        return _fin(sma20[i]) and float(close[i]) >= sma20[i]

    def acc_struct_stop(fill_i):
        s = fill_i - 1  # signal bar
        if s < 0 or not _fin(ll20[s]) or not _fin(x.atr14[s]):
            return float("nan")
        return float(min(low[s], ll20[s]) - STRUCT_STOP_ATR * x.atr14[s])

    acc = StrategySpec(
        name="ACC-BASE-RECLAIM-L", direction=1, entry=acc_entry, exit_=acc_exit,
        stop_atr_mult=TREND_STOP_ATR, max_hold_exec_bars=None,
        max_hold_regime_bars=ACC_MAX_HOLD, min_hold_regime_bars=MIN_HOLD_REGIME_BARS,
        structural_stop=acc_struct_stop,
        economic_mechanism="failed-low reclaim: trapped shorts cover into exhausted supply",
        failure_mode="decline-pause misread: spring keeps breaking; dead-range cost bleed",
    )

    # -- UPT-DIPBUY-L --------------------------------------------------------
    def upt_dip_entry(i, b, xi):
        return (
            _fin(x.ema20[i]) and _fin(x.ema50[i])
            and x.ema20[i] > x.ema50[i]
            and float(low[i]) <= x.ema20[i]
            and float(close[i]) > x.ema20[i]
        )

    def upt_dip_exit(i, b, xi, held):
        return _fin(x.ema20[i]) and float(close[i]) < x.ema20[i]

    upt_dip = StrategySpec(
        name="UPT-DIPBUY-L", direction=1, entry=upt_dip_entry, exit_=upt_dip_exit,
        stop_atr_mult=TREND_STOP_ATR, max_hold_exec_bars=None,
        max_hold_regime_bars=None, min_hold_regime_bars=MIN_HOLD_REGIME_BARS,
        economic_mechanism="dip to the fast mean absorbed by trend-aligned demand",
        failure_mode="trend exhaustion: dips stop being absorbed; EMA whipsaw",
    )

    # -- UPT-BREAKOUT-L ------------------------------------------------------
    def upt_brk_entry(i, b, xi):
        return _fin(hh20[i]) and float(close[i]) > hh20[i]

    def upt_brk_exit(i, b, xi, held):
        return _fin(ll10[i]) and float(close[i]) < ll10[i]

    upt_brk = StrategySpec(
        name="UPT-BREAKOUT-L", direction=1, entry=upt_brk_entry, exit_=upt_brk_exit,
        stop_atr_mult=TREND_STOP_ATR, max_hold_exec_bars=None,
        max_hold_regime_bars=None, min_hold_regime_bars=MIN_HOLD_REGIME_BARS,
        economic_mechanism="stop-cluster conversion above the trailing 20-bar high",
        failure_mode="fakeout environments: buys the top of failed probes",
    )

    # -- DIS-FAILED-HIGH-S (BTC only) ----------------------------------------
    def dis_entry(i, b, xi):
        return (
            _fin(hh20[i]) and _fin(sma20[i])
            and float(high[i]) > hh20[i]
            and float(close[i]) < hh20[i]
            and float(close[i]) > sma20[i]
        )

    def dis_exit(i, b, xi, held):
        return _fin(sma20[i]) and float(close[i]) <= sma20[i]

    def dis_struct_stop(fill_i):
        s = fill_i - 1
        if s < 0 or not _fin(hh20[s]) or not _fin(x.atr14[s]):
            return float("nan")
        return float(max(high[s], hh20[s]) + STRUCT_STOP_ATR * x.atr14[s])

    dis = StrategySpec(
        name="DIS-FAILED-HIGH-S", direction=-1, entry=dis_entry, exit_=dis_exit,
        stop_atr_mult=TREND_STOP_ATR, max_hold_exec_bars=None,
        max_hold_regime_bars=DIS_MAX_HOLD, min_hold_regime_bars=MIN_HOLD_REGIME_BARS,
        structural_stop=dis_struct_stop, tie_break_class="BTC_ONLY_SHORT",
        economic_mechanism="trapped breakout buyers forced to sell at the top",
        failure_mode="top resolves up: re-accumulation runs over the short",
    )

    # -- DNT-CASCADE-S (BTC only) ---------------------------------------------
    def dnt_cas_entry(i, b, xi):
        return (
            _fin(ll20[i]) and _fin(x.ema20[i]) and _fin(x.ema50[i])
            and float(close[i]) < ll20[i]
            and x.ema20[i] < x.ema50[i]
        )

    def dnt_cas_exit(i, b, xi, held):
        return _fin(hh10[i]) and float(close[i]) > hh10[i]

    dnt_cas = StrategySpec(
        name="DNT-CASCADE-S", direction=-1, entry=dnt_cas_entry, exit_=dnt_cas_exit,
        stop_atr_mult=TREND_STOP_ATR, max_hold_exec_bars=None,
        max_hold_regime_bars=None, min_hold_regime_bars=MIN_HOLD_REGIME_BARS,
        tie_break_class="BTC_ONLY_SHORT",
        economic_mechanism="position with the liquidation engine; positive carry",
        failure_mode="cascade exhaustion: late entry shorts the final leg",
    )

    # -- DNT-RALLY-SOLD-S (BTC only) ------------------------------------------
    def dnt_ral_entry(i, b, xi):
        return (
            _fin(x.ema20[i]) and _fin(x.ema50[i])
            and x.ema20[i] < x.ema50[i]
            and float(high[i]) >= x.ema20[i]
            and float(close[i]) < x.ema20[i]
        )

    def dnt_ral_exit(i, b, xi, held):
        return _fin(x.ema20[i]) and float(close[i]) > x.ema20[i]

    dnt_ral = StrategySpec(
        name="DNT-RALLY-SOLD-S", direction=-1, entry=dnt_ral_entry,
        exit_=dnt_ral_exit, stop_atr_mult=TREND_STOP_ATR, max_hold_exec_bars=None,
        max_hold_regime_bars=DNT_RALLY_MAX_HOLD,
        min_hold_regime_bars=MIN_HOLD_REGIME_BARS,
        tie_break_class="BTC_ONLY_SHORT",
        economic_mechanism="contingent supply activates at the fast mean; rallies sold",
        failure_mode="decline ends: rallies hold above EMA20 and become bases",
    )

    return {
        acc.name: acc,
        upt_dip.name: upt_dip,
        upt_brk.name: upt_brk,
        dis.name: dis,
        dnt_cas.name: dnt_cas,
        dnt_ral.name: dnt_ral,
    }


# Regime -> eligible specialist ids per asset (frozen from the library).
LIBRARY_BY_REGIME = {
    "ACCUMULATION": ["ACC-BASE-RECLAIM-L"],
    "UPTREND": ["UPT-DIPBUY-L", "UPT-BREAKOUT-L"],
    "DISTRIBUTION": ["DIS-FAILED-HIGH-S"],  # BTC only; SPY -> FLAT
    "DOWNTREND": ["DNT-CASCADE-S", "DNT-RALLY-SOLD-S"],  # BTC only
    "TRANSITION_UNKNOWN": [],  # fixed FLAT, not selectable
}


def eligible_for(asset: str, regime: str) -> list[str]:
    ids = LIBRARY_BY_REGIME.get(regime, [])
    if asset == "SPY":
        return [s for s in ids if not s.endswith("-S")]
    return list(ids)
