"""Formal fixtures for the generic PIT battery (F-2 harness proof).

Law: the harness MUST fail a RANGEFADE-class leak (same-panel future
statistics consumed at decision time) and MUST pass a strictly
closed-bar signal. These fixtures are the standing regression for every
candidate battery run in this cycle.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from pit_battery2 import (  # noqa: E402
    future_mutation_test, in_session_mask, non_vacuity_test, run_battery,
    truncation_test,
)


def _synth(n=2000, seed=7):
    rng = np.random.default_rng(seed)
    px = 1.0 + np.cumsum(rng.normal(0, 1e-4, n))
    return pd.DataFrame({
        "ts": pd.date_range("2024-01-01", periods=n, freq="1h", tz="UTC"),
        "b_o": px, "b_h": px + 1e-4, "b_l": px - 1e-4, "b_c": px,
        "a_o": px + 2e-4, "a_c": px + 2e-4,
        "s_open": 2e-4, "s_close": 2e-4, "v": 100.0,
    })


def clean_sig(d):
    t = np.zeros(len(d), dtype=int)
    t[1:] = np.where(d["b_c"].to_numpy()[1:] > d["b_c"].to_numpy()[:-1], 1, -1)
    return t


def leaky_sig(d):
    hi = d["b_h"].to_numpy().max()   # full-panel future statistic
    lo = d["b_l"].to_numpy().min()
    return np.where(d["b_c"].to_numpy() > (hi + lo) / 2, -1, 1)


def test_harness_catches_rangefade_class_leak():
    r = truncation_test(leaky_sig, _synth())
    assert r["status"] == "FAIL" and r["kill_class"] == "KILL_PIT_SEAM"


def test_harness_passes_closed_bar_signal():
    r = truncation_test(clean_sig, _synth())
    assert r["status"] == "PASS"


def test_future_mutation_clean_and_leaky():
    assert future_mutation_test(clean_sig, _synth())["status"] == "PASS"
    # leaky: full-panel mid depends on the future -> mutated future moves it
    assert future_mutation_test(leaky_sig, _synth())["status"] == "FAIL"


def test_non_vacuity_threshold():
    df = _synth()
    base = clean_sig(df)
    same = non_vacuity_test(base, base.copy())
    assert same["status"] == "FAIL" and same["kill_class"] == "KILL_VACUOUS_MUTATION"
    flip = non_vacuity_test(base, -base)
    assert flip["status"] == "PASS"


def test_run_battery_verdicts():
    good = run_battery(clean_sig, _synth(), {"flip": lambda d: -clean_sig(d)})
    bad = run_battery(leaky_sig, _synth(), {"flip": lambda d: -leaky_sig(d)})
    assert good["verdict"] == "PASS_PIT" and bad["verdict"] == "FAIL_PIT"


def test_in_session_mask_bounds():
    df = _synth(48)
    m = in_session_mask(df, (7, 18))
    assert m.sum() == 12 and not m[0] and m[7] and m[18] and not m[19]
