"""ES1 hand-computed fixtures (plan §6 mandatory tests). Run: pytest."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "scripts"))
sys.dont_write_bytecode = True
import es1_engine as E  # noqa: E402


def make_panel(close, open_=None):
    n = len(close)
    open_ = open_ if open_ is not None else close
    ms = 1577836800000 + np.arange(n) * 4 * 3600 * 1000
    return pd.DataFrame({"bucket_ms": ms, "open": open_, "high": np.maximum(open_, close),
                         "low": np.minimum(open_, close), "close": close})


def test_next_bar_fill_and_fee_once():
    close = np.full(10, 100.0)
    close[5] = 110.0  # price jumps after the decision
    panel = make_panel(close)
    dec = np.zeros(10)
    dec[3] = 1.0  # decide at close of 3 -> filled at open of 4
    folds = np.zeros(10, dtype=int)
    res = E.simulate(dec, panel, folds, tier=1.0, funding_law="constant")
    # fill at open[4]=100 (flat price), earn close[4]/open[4]-1 = 0 ; bar5:
    # gap leg open[5]/close[4]-1 = 0 (flat opens), intrabar 110/100-1 = +10%
    assert res.fills == 2  # entry fill + fold-end force-flat
    assert res.entries == 1
    # accounting identity (fees/funding compound through equity multiplicatively)
    assert res.net == pytest.approx(res.gross - res.fees - res.funding, rel=1e-9)
    # sanity: one +10% intrabar on ~100k, minus two fees and ~3 fundings
    assert 9_700 < res.net < 10_000


def test_no_lookahead_mutation():
    rng = np.random.default_rng(7)
    close = 100 * np.exp(np.cumsum(rng.normal(0, 0.01, 400)))
    panel = make_panel(close)
    folds = np.zeros(400, dtype=int)
    base = np.zeros(400)
    base[100:] = 1.0
    r1 = E.simulate(base, panel, folds)
    mutated = close.copy()
    mutated[300] *= 1.7  # perturb the FUTURE only
    r2 = E.simulate(base, make_panel(mutated), folds)
    assert r1.equity[:300] == pytest.approx(r2.equity[:300], rel=1e-12)


def test_funding_sign_and_boundary_only():
    n = 24  # 4 days x 6 bars
    close = np.full(n, 100.0)
    panel = make_panel(close)
    hours = pd.to_datetime(panel["bucket_ms"], unit="ms", utc=True).dt.hour.to_numpy()
    assert hours[0] == 0  # first bar is a funding boundary
    dec = np.ones(n)
    folds = np.zeros(n, dtype=int)
    res = E.simulate(dec, panel, folds, tier=0.0, funding_law="constant")
    assert res.funding > 0  # a long PAYS positive funding
    # boundaries at hours {0,8,16}: bars 0,2,4,...; funding charged from bar1 onward
    # (bar0 has no held position) -> 11 boundary bars held at ~100k
    assert res.funding == pytest.approx(E.FUNDING_CONST * 100_000 * 11, rel=2e-3)


def test_scale_cap_and_zero_when_unknown():
    close = np.full(400, 100.0)
    panel = make_panel(close)
    folds = np.zeros(400, dtype=int)
    # sig_vol_managed itself must cap: tiny rvol -> scale capped at 1.0 (no leverage)
    rvol_tiny = np.full(400, 0.01)
    base = np.ones(400)
    dec = E.sig_vol_managed(base, rvol_tiny, 0.60)
    assert dec.max() <= 1.0 and np.all(dec[np.isfinite(dec)] == 1.0)
    # large rvol -> scaled down, and unknown rvol (nan) -> zero exposure
    rvol_big = np.full(400, 2.0)
    dec2 = E.sig_vol_managed(base, rvol_big, 0.60)
    assert dec2.max() == pytest.approx(0.30, rel=1e-9)
    rvol_nan = rvol_big.copy()
    rvol_nan[:250] = np.nan
    dec3 = E.sig_vol_managed(base, rvol_nan, 0.60)
    assert np.all(dec3[np.isnan(rvol_nan)] == 0.0)
    res = E.simulate(dec, panel, folds)
    assert res.entries == 1


def test_measured_funding_loader_and_law():
    # the real staged Vision funding series (machine-local) must load and price
    fr = E.load_funding_measured()
    assert len(fr) > 7000 and fr["ms"].is_monotonic_increasing
    assert (fr["rate"].abs() <= 0.05).all()  # clamp sanity (Binance cap 2%/8h... margin)
    rng = np.random.default_rng(5)
    close = 100 * np.exp(np.cumsum(rng.normal(0, 0.01, 300)))
    panel = make_panel(close)
    folds = np.zeros(300, dtype=int)
    dec = np.ones(300)
    rc = E.simulate(dec, panel, folds, tier=1.0, funding_law="constant")
    rm = E.simulate(dec, panel, folds, tier=1.0, funding_law="measured", funding_df=fr)
    assert rm.funding > 0  # long pays positive measured funding
    assert rm.net == pytest.approx(rm.gross - rm.fees - rm.funding, rel=1e-9)
    # measured law over 2020-2026 must charge ~7x more than the frozen constant
    assert rm.funding > 5 * rc.funding


def test_band_hysteresis_golden():
    close = np.array([100.0, 100.5, 101.2, 100.8, 100.4, 99.0, 98.9, 99.5, 100.6, 101.0])
    sig = E.sig_trend_lf(make_panel(close), band=0.01)
    # SMA200 undefined on a 10-bar series -> flat everywhere (warmup law)
    assert (sig == 0).all()


def test_trend_golden_synthetic_long_series():
    # flat 300 bars at 100 -> sma=100; close 101 (>+1%) -> long at the next bar
    close = np.full(300, 100.0)
    panel = make_panel(close)
    sig = E.sig_trend_lf(panel, band=0.01)
    assert sig[299] == 0.0  # r=0 is not > band -> stays flat (golden)
    close2 = np.concatenate([close[:-1], [102.0]])
    sig2 = E.sig_trend_lf(make_panel(close2), band=0.01)
    assert sig2[299] == 1.0  # 102/100-1 = 2% > 1% band -> long
    # drop below -1% -> exit
    close3 = np.concatenate([close[:-2], [98.8, 98.7]])
    sig3 = E.sig_trend_lf(make_panel(close3), band=0.01)
    assert sig3[299] == 0.0  # 98.7/100-1 = -1.3% < -1% -> flat


def test_fold_force_flat_and_identity():
    rng = np.random.default_rng(11)
    close = 100 * np.exp(np.cumsum(rng.normal(0, 0.01, 200)))
    panel = make_panel(close)
    folds = np.zeros(200, dtype=int)
    folds[150:] = 1  # two folds
    dec = np.ones(200)  # always want long
    res = E.simulate(dec, panel, folds)
    assert res.fills >= 4  # entries + force-flats + re-entries
    assert abs(sum(res.fold_net.values()) - res.net) < 1e-6 * max(1.0, abs(res.net))
    # fold boundary: no carry — each fold's first fill happens at its open


def test_tier_exactness():
    rng = np.random.default_rng(3)
    close = 100 * np.exp(np.cumsum(rng.normal(0, 0.02, 300)))
    panel = make_panel(close)
    dec = (np.arange(300) % 17 == 0).astype(float)
    folds = np.zeros(300, dtype=int)
    r10 = E.simulate(dec, panel, folds, tier=1.0)
    r15 = E.simulate(dec, panel, folds, tier=1.5)
    # tier multiplies FEES only; fees compound through equity (first-order 1.5x)
    assert r15.fees / r10.fees == pytest.approx(1.5, rel=0.02)
    # funding is rate x equity — NOT tier-scaled; higher fees shrink it slightly
    assert r15.funding == pytest.approx(r10.funding, rel=0.02)
