"""Feature contract tests: causality, warmup, hand checks, semantic state."""

from __future__ import annotations

import numpy as np
import pytest

from conftest import make_bars
from jrv2.features import (
    BINS,
    FEATURE_ORDER,
    NUMERIC_FIELDS,
    WARMUP_REGIME_BARS,
    RegimeFeatures,
    binize,
    compute_bins,
    normalize_semantic_state,
    semantic_state,
    state_payload,
)
from jrv2 import indicators as ind


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
    n = 20
    close = np.full(n, 100.0)
    high = close + 0.5
    low = close - 0.5
    a = ind.atr(high, low, close, 14)
    assert np.isnan(a[:13]).all()
    assert a[13] == pytest.approx(1.0)
    assert a[14] == pytest.approx(1.0)
    high2 = high.copy()
    high2[15] = 101.5  # TR = 2.0
    a2 = ind.atr(high2, low, close, 14)
    assert a2[15] == pytest.approx((1.0 * 14 - 1.0 + 2.0) / 14)


def test_wilder_adx_hand_trend():
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


def test_features_warmup_and_order():
    bars = _series()
    f = RegimeFeatures(bars)
    assert f.T == len(bars.close)
    v = f.vector_at(WARMUP_REGIME_BARS)
    assert v is not None and len(v) == 16
    assert np.isnan(f.arrays["r72"][71])
    assert np.isfinite(f.arrays["r72"][72])


def test_no_lookahead_mutation():
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


def test_rolling_windows_strictly_trailing():
    bars = _series()
    f = RegimeFeatures(bars)
    t = 250
    close = bars.close
    w = close[t - 167 : t + 1]
    assert f.arrays["dd_168"][t] == pytest.approx(float(close[t]) / float(np.max(w)) - 1.0)
    # rv_pctile ranks against the trailing 168 PAST values (exclusive)
    rv = f.arrays["rv_pctile"][t]
    assert 0.0 <= rv <= 1.0


def test_clv_fail_closed_all_zero_range():
    n = 250
    close = np.full(n, 100.0)
    bars = make_bars(close, close, close, close, np.ones(n))
    f = RegimeFeatures(bars)
    assert f.vector_at(WARMUP_REGIME_BARS) is None  # NaN clv -> LOCAL_INVALID
    num = f.numerics_at(WARMUP_REGIME_BARS)
    assert num is None


def test_clv_drops_zero_range_bars():
    close = np.full(250, 100.0)
    high = close + 1.0
    low = close - 1.0
    # make half the last 24 bars zero-range (high==low==close)
    for i in range(226, 250, 2):
        high[i] = close[i]
        low[i] = close[i]
    bars = make_bars(close, high, low, close, np.linspace(1.0, 2.0, 250))
    f = RegimeFeatures(bars)
    v = f.vector_at(WARMUP_REGIME_BARS)
    assert v is not None  # fail-closed only when ALL 24 zero-range
    clv = v[FEATURE_ORDER.index("clv_24")]
    assert 0.0 <= clv <= 1.0


def test_semantic_state_named_fields():
    bars = _series()
    f = RegimeFeatures(bars)
    st = semantic_state("btcusdt", None, bars, WARMUP_REGIME_BARS, f, "UPTREND")
    assert st is not None
    assert set(st["bins"].keys()) == set(BINS.keys())
    assert set(st["numerics"].keys()) == set(NUMERIC_FIELDS.keys())
    assert st["prior_structure"] == "TREND_UP"
    assert st["prior_direction"] == "UP"
    payload = state_payload(st)
    # anonymization: no symbol / dates / price levels anywhere
    blob = repr(payload)
    for banned in ("btc", "BTC", "symbol", "2025", "2026", "price"):
        assert banned not in blob
    # prior null -> 'none'
    st0 = semantic_state("btcusdt", None, bars, WARMUP_REGIME_BARS + 1, f, None)
    assert st0["prior_structure"] == "none"
    assert st0["prior_direction"] == "none"


def test_prior_maps_frozen():
    from jrv2.features import PRIOR_DIRECTION_MAP, PRIOR_STRUCTURE_MAP

    assert PRIOR_STRUCTURE_MAP == {
        "UPTREND": "TREND_UP",
        "DOWNTREND": "TREND_DOWN",
        "ACCUMULATION": "RANGE",
        "DISTRIBUTION": "RANGE",
        "TRANSITION_UNKNOWN": "RANGE",
        None: "none",
    }
    assert PRIOR_DIRECTION_MAP == {
        "UPTREND": "UP",
        "DOWNTREND": "DOWN",
        "ACCUMULATION": "DOWN",
        "DISTRIBUTION": "UP",
        "TRANSITION_UNKNOWN": "NEUTRAL",
        None: "none",
    }


def test_bins_match_freeze_thresholds(fz):
    """Every bin in code equals the freeze's field/thresholds/labels exactly."""
    bins = fz.semantic_state_contract["bins"]
    for name, spec in bins.items():
        if name.startswith("prior_"):
            continue
        assert BINS[name][0] == spec["field"], name
        assert list(BINS[name][1]) == list(spec["thresholds"]), name
        assert list(BINS[name][2]) == list(spec["labels"]), name


def test_binize_boundary_convention_left_closed():
    # half-open [t_i, t_{i+1}): a value exactly ON a threshold belongs to the
    # HIGHER label (uniform convention, documented in features.py)
    labels = ("low", "medium", "high")
    assert binize(19.999, (20, 30), labels) == "low"
    assert binize(20.0, (20, 30), labels) == "medium"
    assert binize(29.999, (20, 30), labels) == "medium"
    assert binize(30.0, (20, 30), labels) == "high"
    # trend bins: exact boundaries resolve upward
    fast = BINS["fast_trend"]
    assert binize(-0.002, fast[1], fast[2]) == "weak_down"
    assert binize(-0.0003, fast[1], fast[2]) == "flat"
    assert binize(0.0003, fast[1], fast[2]) == "weak_up"
    assert binize(0.002, fast[1], fast[2]) == "strong_up"


def test_compute_bins_roundtrip():
    numerics = {
        "ema_slope_fast": 0.0005,   # weak_up
        "ema_slope_slow": 0.001,    # weak_up
        "adx14": 25.0,              # medium
        "rv_pctile": 0.80,          # high
        "dd_168": -0.10,            # mild
        "range_pos": 0.0,           # middle
        "clv_24": 0.5,              # neutral
        "vol_z": 0.0,               # normal
        "dist_ema": 0.5,            # above
    }
    bins = compute_bins(numerics)
    assert bins == {
        "fast_trend": "weak_up",
        "slow_trend": "weak_up",
        "trend_strength": "medium",
        "volatility_regime": "high",
        "drawdown_state": "mild",
        "range_location": "middle",
        "close_location": "neutral",
        "volume_state": "normal",
        "dist_to_ema": "above",
    }


def test_normalize_semantic_state_flat_and_nested():
    flat = {
        "fast_trend": "strong_up", "slow_trend": "weak_up",
        "trend_strength": "high", "volatility_regime": "normal",
        "drawdown_state": "near_high", "range_location": "near_high",
        "close_location": "strong", "volume_state": "normal",
        "dist_to_ema": "above",
        "short_return": 0.02, "medium_return": 0.11, "long_return": 0.28,
        "prior_structure": "TREND_UP", "prior_direction": "UP",
    }
    st = normalize_semantic_state(flat)
    assert st["bins"]["fast_trend"] == "strong_up"
    assert st["numerics"]["long_return"] == 0.28
    assert st["prior_structure"] == "TREND_UP"
    # nested passthrough
    st2 = normalize_semantic_state(st)
    assert st2 == st
