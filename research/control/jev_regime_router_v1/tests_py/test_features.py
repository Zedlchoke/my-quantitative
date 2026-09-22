"""Feature contract tests: causality, warmup, hand checks, anonymization."""

from __future__ import annotations

import json

import numpy as np
import pytest

from conftest import make_bars
from jrv1.features import (
    FEATURE_ORDER,
    WARMUP_REGIME_BARS,
    RegimeFeatures,
    build_states,
    state_payload,
)
from jrv1 import indicators as ind


def _series(n=320, seed=7):
    rng = np.random.default_rng(seed)
    rets = rng.normal(0.0005, 0.01, n)
    close = 100 * np.exp(np.cumsum(rets))
    high = close * (1 + np.abs(rng.normal(0, 0.004, n)))
    low = close * (1 - np.abs(rng.normal(0, 0.004, n)))
    open_ = low + (high - low) * rng.random(n)
    vol = np.abs(rng.normal(100, 20, n))
    return make_bars(close, high, low, open_, vol)


def test_ema_seed_and_recursion():
    x = np.array([100.0, 101.0, 102.0])
    e = ind.ema(x, 12)
    a = 2 / 13
    assert e[0] == 100.0
    assert e[1] == pytest.approx(100 + a * 1)
    assert e[2] == pytest.approx(e[1] + a * (102 - e[1]))


def test_wilder_atr_hand_check():
    # constant range bars: TR = 1 each -> ATR seed = 1 at index 13
    n = 20
    close = np.full(n, 100.0)
    high = close + 0.5
    low = close - 0.5
    a = ind.atr(high, low, close, 14)
    assert np.isnan(a[:13]).all()
    assert a[13] == pytest.approx(1.0)
    assert a[14] == pytest.approx(1.0)
    # a wider bar raises the smoothed ATR by (tr - atr)/14
    high2 = high.copy()
    high2[15] = 101.5  # TR = 2.0
    a2 = ind.atr(high2, low, close, 14)
    assert a2[15] == pytest.approx((1.0 * 14 - 1.0 + 2.0) / 14)


def test_wilder_adx_hand_trend():
    # monotonic uptrend: +DM carries, DX=100, ADX converges to 100
    n = 60
    close = np.arange(1, n + 1, dtype=float)
    high = close + 0.5
    low = close - 0.5
    a = ind.adx(high, low, close, 14)
    assert np.isnan(a[:27]).all()
    assert a[-1] > 90.0


def test_rsi_extremes():
    up = np.linspace(1, 100, 40)
    r = ind.rsi(up, 14)
    assert r[-1] == pytest.approx(100.0)
    dn = np.linspace(100, 1, 40)
    r2 = ind.rsi(dn, 14)
    assert r2[-1] == pytest.approx(0.0)


def test_bollinger_flat():
    x = np.full(30, 5.0)
    mid, up, lo = ind.bollinger(x, 20, 2.0)
    assert mid[-1] == 5.0
    assert up[-1] == 5.0
    assert lo[-1] == 5.0
    assert np.isnan(mid[18])


def test_features_warmup_and_order(fz):
    bars = _series()
    f = RegimeFeatures(bars)
    assert f.T == len(bars.close)
    v = f.vector_at(WARMUP_REGIME_BARS)
    assert v is not None and len(v) == 16
    assert np.isnan(f.arrays["r72"][71])
    assert np.isfinite(f.arrays["r72"][72])
    # states only exist from warmup
    states = build_states("btcusdt", fz, bars, None)
    assert len(states) == f.T - WARMUP_REGIME_BARS
    assert states[0]["bar_index"] == WARMUP_REGIME_BARS


def test_no_lookahead_mutation(fz):
    """Perturbing bars t+1..t+k never changes features at t (golden law)."""
    bars = _series()
    t = 260
    f1 = RegimeFeatures(bars).vector_at(t)
    close = bars.close.copy()
    high = bars.high.copy()
    low = bars.low.copy()
    open_ = bars.open.copy()
    vol = bars.volume.copy()
    close[t + 1 :] *= 1.5
    high[t + 1 :] += 7.0
    low[t + 1 :] -= 7.0
    vol[t + 1 :] *= 3.0
    bars2 = make_bars(close, high, low, open_, vol, start_ts=int(bars.ts_open[0]), step_ns=3600 * 10**9)
    f2 = RegimeFeatures(bars2).vector_at(t)
    assert f1 == pytest.approx(f2)


def test_rolling_windows_strictly_trailing(fz):
    """Windowed features depend only on their trailing windows.

    EMA/ATR/ADX are recursive from bar 0 (causal, but infinite memory), so
    they are exempt here; their causality is pinned by the no-lookahead test.
    """
    bars = _series()
    t = 300
    base = RegimeFeatures(bars)
    v1 = base.vector_at(t)
    # perturb the earliest bars (outside every trailing window at t)
    close = bars.close.copy()
    vol = bars.volume.copy()
    close[0] *= 1.3
    vol[0] *= 5.0
    bars2 = make_bars(close, bars.high.copy(), bars.low.copy(), bars.open.copy(), vol, start_ts=int(bars.ts_open[0]), step_ns=3600 * 10**9)
    v2 = RegimeFeatures(bars2).vector_at(t)
    windowed = [0, 1, 2, 3, 4, 10, 11, 12, 13, 14, 15]
    for i in windowed:
        assert v1[i] == pytest.approx(v2[i]), (FEATURE_ORDER[i], v1[i], v2[i])
    # rv_pctile is in [0,1] and ranks against PAST values only
    rvp = base.arrays["rv_pctile"]
    assert ((rvp[WARMUP_REGIME_BARS:] >= 0) & (rvp[WARMUP_REGIME_BARS:] <= 1)).all()


def test_rv_pctile_hand_check():
    """Rank of current rv24 among its trailing 168 past values / 168."""
    n = WARMUP_REGIME_BARS + 5
    close = np.concatenate([np.full(n - 1, 100.0), [101.0]])
    bars = make_bars(close)
    f = RegimeFeatures(bars)
    t = n - 1
    # past window is flat zero returns; current rv24 > 0 -> rank = 168/168
    past = np.zeros(168)
    cur = float(np.std(np.array([0.0] * 23 + [np.log(101 / 100)])))
    assert cur > 0
    assert f.arrays["rv_pctile"][t] == pytest.approx(np.count_nonzero(past < cur) / 168)


def test_clv_fail_closed():
    """All-zero-range window -> f16 NaN -> state LOCAL_INVALID, never sent."""
    n = 200
    close = np.full(n, 50.0)
    bars = make_bars(close)  # high=low=close: zero range everywhere
    f = RegimeFeatures(bars)
    assert np.isnan(f.arrays["clv_24"][199])
    assert f.vector_at(199) is None
    # partial: bars whose high==low are DROPPED from the mean (fail-closed
    # only when ALL 24 are zero-range)
    high = close + 1.0
    low = close - 1.0
    high[195:] = close[195:]  # last 5 bars: high==low==close -> zero range
    low[195:] = close[195:]
    bars2 = make_bars(close, high, low)
    f2 = RegimeFeatures(bars2)
    # window at 199: bars 176..199; bars 176..194 ranged (clv 0.5 each)
    assert f2.arrays["clv_24"][199] == pytest.approx(0.5)


def test_clv_hand_computation():
    close = np.array([10.0, 12.0])
    high = np.array([12.0, 12.0])
    low = np.array([9.0, 10.0])
    bars = make_bars(close, high, low)
    f = RegimeFeatures(bars)
    # (close-low)/(high-low) = 1/3 and 2/2 = 1.0 -> mean 2/3 at t=1 (window 24 needs
    # 24 bars though: with only 2 bars the feature is NaN)
    assert np.isnan(f.arrays["clv_24"][1])


def test_range_pos_zero_range_guard():
    close = np.full(30, 42.0)
    bars = make_bars(close)
    f = RegimeFeatures(bars)
    assert f.arrays["range_pos"][29] == 0.0  # flat window -> 0.0 by contract


def test_state_anonymization(fz):
    """Payload carries no symbol/date/price substrings; state_id opaque."""
    bars = _series(seed=11)
    states = build_states("btcusdt", fz, bars, prior_labels=None)
    st = states[10]
    payload = state_payload(st)
    text = json.dumps(payload)
    for forbidden in ("BTC", "btc", "SPY", "spy", "2023", "2025", "2026", "2024"):
        assert forbidden not in text
    # no absolute price leaks: the closes were ~100-ish scaled randoms
    for p in bars.close[::40]:
        assert repr(float(p)) not in text
    assert set(payload.keys()) == {"feature_vector", "prior_regime"}
    assert len(payload["feature_vector"]) == 16
    assert len(st["state_id"]) == 16
    int(st["state_id"], 16)


def test_prior_regime_shift(fz):
    """f17 = persisted state in force at t-1 (one-hot shifted by one bar)."""
    bars = _series(seed=3)
    T = len(bars.close)
    labels = [None] * T
    for i in range(200, T):
        labels[i] = "UPTREND"
    states = build_states("btcusdt", fz, bars, prior_labels=labels)
    # first state (t=192): prior = labels[191] = None
    assert states[0]["prior_regime"] is None
    # state at t=201: prior = labels[200] = UPTREND
    assert states[9]["prior_regime"] == "UPTREND"
    # state at t=200: prior = labels[199] = None
    assert states[8]["prior_regime"] is None


def test_local_invalid_states_not_sent(fz):
    bars = _series(seed=5)
    # make one late bar degenerate (zero-range tail) -> NaN clv only if ALL 24 zero;
    # instead force non-finite via a zero close (division) at the last bar
    close = bars.close.copy()
    close[-1] = 0.0
    bars2 = make_bars(close, bars.high.copy(), bars.low.copy(), bars.open.copy(), bars.volume.copy(), start_ts=int(bars.ts_open[0]), step_ns=3600 * 10**9)
    states = build_states("btcusdt", fz, bars2, None)
    inv = [s for s in states if s["local_invalid"]]
    assert inv, "expected at least one LOCAL_INVALID state"
    for s in inv:
        assert s["feature_vector"] is None
        with pytest.raises(ValueError):
            state_payload(s)
