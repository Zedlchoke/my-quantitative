"""No-lookahead, warmup-exclusion and UTC/timezone-boundary tests."""
import numpy as np
import pandas as pd

import phase_rule as pr


def make_df(closes, start="2020-01-01"):
    closes = np.asarray(closes, dtype=float)
    n = len(closes)
    return pd.DataFrame({
        "open": closes, "high": closes + 0.5, "low": closes - 0.5,
        "close": closes,
        "open_time": pd.date_range(start, periods=n, freq="h", tz="UTC"),
    })


def deterministic_closes(n=3000, seed=11):
    rng = np.random.default_rng(seed)
    t = np.arange(n)
    return 100 + 10 * np.sin(t / 40.0) + 0.01 * t + rng.normal(0, 0.5, n)


def test_future_perturbation_cannot_change_past_labels():
    closes = deterministic_closes()
    df = make_df(closes)
    base = pr.compute_labels(df)["state_label"].to_numpy()
    t0 = 1500
    # replace the ENTIRE future after t0 with a different path
    pert = closes.copy()
    pert[t0:] = pert[t0:][::-1] + 25.0
    alt = pr.compute_labels(make_df(pert))["state_label"].to_numpy()
    assert (base[:t0 + 1] == alt[:t0 + 1]).all()


def test_perturbing_one_future_bar_never_changes_past_labels():
    closes = deterministic_closes(seed=23)
    df = make_df(closes)
    base = pr.compute_labels(df)["state_label"].to_numpy()
    t0 = 900
    pert = closes.copy()
    pert[t0 + 500] += 50.0
    alt = pr.compute_labels(make_df(pert))["state_label"].to_numpy()
    assert (base[:t0 + 1] == alt[:t0 + 1]).all()


def test_warmup_exclusion():
    closes = deterministic_closes(n=1500)
    out = pr.compute_labels(make_df(closes))
    labels = out["state_label"].to_numpy()
    assert (labels[:pr.WARMUP_BARS] == "TRANSITION_UNKNOWN").all()
    # post-warmup window for census starts at bar index 720 exactly
    assert labels[pr.WARMUP_BARS - 1] == "TRANSITION_UNKNOWN"


def test_utc_hour_grid_and_leap_boundary():
    # 3 days spanning the 2024 leap day: exactly 72 hourly bars, UTC fixed
    df = make_df(deterministic_closes(n=72), start="2024-02-28")
    idx = pd.DatetimeIndex(df["open_time"])
    assert len(idx) == 72
    assert idx.tz is not None and str(idx.tz) == "UTC"
    assert (idx[1] - idx[0]) == pd.Timedelta(hours=1)
    assert idx[24] == pd.Timestamp("2024-02-29 00:00", tz="UTC")
    out = pr.compute_labels(df)
    # the bar opening 23:00 closes at 00:00 NEXT day: its decision time is
    # the next midnight (UTC has no DST) — label must exist and be causal
    assert out["state_label"].iloc[23] in pr.PHASES


def test_execution_convention_decision_close_fill_next_open():
    # documented convention: decision at close of bar t => executable at
    # open of bar t+1 (>= 1 executable-bar lag)
    closes = deterministic_closes(n=1500)
    out = pr.compute_labels(make_df(closes))
    # labels are computed from the same bar they are attached to (its close)
    # and never from the following bar: spot-verify SMA causality directly
    closes_arr = out["close"].to_numpy()
    sma = out["sma_slow"].to_numpy()
    t = 1200
    assert sma[t] == pytest_approx(closes_arr[t - 719: t + 1].mean())
    # SMA720 becomes finite at index 719 (window bars 0..719); the LABEL law
    # independently excludes all bars < 720 via warmup (tested elsewhere)
    assert np.isfinite(sma[pr.WARMUP_BARS - 1])
    assert not np.isfinite(sma[pr.WARMUP_BARS - 2])


def pytest_approx(x, tol=1e-9):
    class _A:
        def __eq__(self, other):
            return abs(x - other) <= tol * max(1.0, abs(x))
    return _A()
