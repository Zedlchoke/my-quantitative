"""DT100 fixtures — hand-computed golden cases + falsification mutations.

These tests use SYNTHETIC bars only (never production outcomes).
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dt100 import config, signals
from dt100.engine import clock_shadow, run_arm

FOLDS = [("F1", "2021-01-01", "2021-12-31")]


def toy(n=600, seed=7):
    rng = np.random.default_rng(seed)
    ts = pd.date_range("2021-01-01", periods=n, freq="1min", tz="UTC")
    px = 100 + np.cumsum(rng.normal(0, 0.05, n))
    return pd.DataFrame({"ts": ts, "o": px, "h": px + 0.02, "l": px - 0.02,
                         "c": px, "v": 10.0, "tb": 5.0})


def test_golden_execution_math():
    """pos decided at close t fills at open t+1 (hand-checked)."""
    df = toy(12, seed=1)
    df.loc[:, "o"] = [100, 101, 102, 103, 102, 101, 100, 100, 100, 100, 100, 100]
    df.loc[:, "c"] = df["o"]
    pos = pd.Series(0.0, index=df.index)
    pos.iloc[3] = 1.0   # decided close3 -> fill open[4]=102
    pos.iloc[4] = 1.0
    pos.iloc[5] = 1.0
    pos.iloc[6] = 0.0   # flat decided close6 -> exit fill open[7]=100
    st = run_arm(df, pos, FOLDS, "crypto", "BTCUSDT")
    assert st["trades"] == 1
    # gross = (100/102-1)*1e4 = -196.078 bps ; cost = 2*(5+1) = 12 bps
    assert abs(st["expectancy_bps"] - (-196.078 - 12.0)) < 0.01


def test_fx_uses_measured_spread():
    df = toy(12, seed=2)
    df["o"] = [1.1000, 1.1001, 1.1002, 1.1003, 1.1002, 1.1001] * 2
    df["c"] = df["o"]
    df["spread_bps"] = 0.8
    pos = pd.Series(0.0, index=df.index)
    pos.iloc[1] = 1.0
    pos = signals._hold_until(pos, df, 2)
    st = run_arm(df, pos, FOLDS, "fx", "EURUSD")
    assert st["trades"] == 1
    # RT cost = half(0.8)+half(0.8) = 0.8 bps (per-bar measured, stress 1.0)
    assert abs(st["max_cost_bps"] - 0.8) < 1e-9


def test_no_lookahead_mutation():
    """Shifting the signal by one bar MUST change the decision digest."""
    df = toy(3000, seed=3)
    pos = signals.rsi2(df, {"lo": 10, "hi": 90, "ema": 200, "hold": 60})
    shifted = pos.shift(1).fillna(0.0)
    d1 = np.ascontiguousarray(pos.to_numpy()).tobytes()
    d2 = np.ascontiguousarray(shifted.to_numpy()).tobytes()
    assert d1 != d2
    st1 = run_arm(df, pos, FOLDS, "crypto", "BTCUSDT")
    st2 = run_arm(df, shifted, FOLDS, "crypto", "BTCUSDT")
    assert st1["trades"] != st2["trades"] or st1["expectancy_bps"] != st2["expectancy_bps"]


def test_day_force_flat_crypto():
    df = toy(3000, seed=4)  # spans >2 days at 1m
    pos = pd.Series(1.0, index=df.index)  # always long
    st = run_arm(df, pos, FOLDS, "crypto", "BTCUSDT")
    spans = pd.to_datetime(getattr(st, "ts_entry", None)) if False else None
    # trades count > 1 proves force-flat slicing at day boundaries
    assert st["trades"] >= 2


def test_clock_shadow_parity():
    df = toy(5000, seed=5)
    pos = pd.Series(0.0, index=df.index)
    pos.iloc[100:110] = [1.0, -1.0] * 5   # 10 fired, same stratum, mixed dirs
    cs = clock_shadow(pos, df["ts"])
    assert (cs != 0).sum() == (pos != 0).sum()          # schedule preserved
    assert not np.array_equal(cs.to_numpy(), pos.to_numpy())  # direction moved


def test_determinism():
    df = toy(3000, seed=6)
    pos = signals.fh_mom(df, {"k": 0.3})
    a = run_arm(df, pos, FOLDS, "crypto", "BTCUSDT")
    b = run_arm(df, pos, FOLDS, "crypto", "BTCUSDT")
    assert a["expectancy_bps"] == b["expectancy_bps"] and a["trades"] == b["trades"]


def test_spread_marking_difference_math():
    """INC-DT100-1 regression: synthetic-spread PnL = DIFFERENCE, not ratio."""
    df = toy(12, seed=9)
    vals = [0.010, 0.010, 0.010, 0.010, 0.012, 0.012, 0.010, 0.010, 0.010, 0.010, 0.010, 0.010]
    df.loc[:, "o"] = vals
    df.loc[:, "c"] = vals
    pos = pd.Series(0.0, index=df.index)
    pos.iloc[3] = 1.0   # held close3..close5
    pos.iloc[4] = 1.0
    pos.iloc[5] = 0.0   # flat decided close5 -> exit spread[6]=0.010
    st = run_arm(df, pos, FOLDS, "crypto", "BTCUSDT",
                 cost_multiplier=2.0, spread_marking=True)
    assert st["trades"] == 1
    # gross = (0.010 - 0.012) * 1e4 = -20 bps ; cost = 2 legs * 2 * (5+1) = 24
    assert abs(st["expectancy_bps"] - (-20.0 - 24.0)) < 1e-9
    # ratio marking would give (0.010/0.012-1)*1e4 = -1666.7 bps — pinned away


def test_signal_domain_all_families():
    df = toy(4000, seed=8)
    checks = {
        "orb": signals.orb(df, {"window_min": 30}),
        "squeeze": signals.squeeze(df, {"pct": 0.2, "lookback": 500, "range_win": 100, "hold": 60}),
        "rsi2": signals.rsi2(df, {"lo": 10, "hi": 90, "ema": 200, "hold": 60}),
        "weekend": signals.weekend(df, {"band": 1.0}),
        "pdhl_sweep": signals.pdhl_sweep(df, {"reclaim_frac": 0.001}),
        "delta_div": signals.delta_div(df, {"dwin": 240, "dz": 2.0, "pz": 1.0, "hold": 60}),
        "fh_mom": signals.fh_mom(df, {"k": 0.3}),
        "on_ret": signals.on_ret(df, {"band": 1.5}),
        "rv_regime": signals.rv_regime(df, {"hi": 0.8, "lo": 0.2}),
        "volauto": signals.volauto(df, {"volpct": 0.7, "band": 1.5, "hold": 60}),
        "vol_target_mom": signals.vol_target_mom(df, {"lookback": 600, "volcap": 0.9}),
        "fail_breakout": signals.fail_breakout(df, {"rwin": 60, "confirm": 15, "hold": 60}),
        "fvg": signals.fvg(df, {"fill_win": 60}),
        "vwap_mr": signals.vwap_mr(df, {"band": 2.0, "hold": 120}),
        "boll_fade": signals.boll_fade(df, {"win": 60, "k": 2.0, "hold": 60}),
        "asian_range": signals.asian_range(df, {"edge_frac": 0.1}),
    }
    for name, s in checks.items():
        assert set(np.unique(s.dropna().to_numpy())) <= {-1.0, 0.0, 1.0}, name
