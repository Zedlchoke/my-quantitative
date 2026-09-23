"""Ancestry shadow-construction goldens — hand-computed fixtures.

A7-H1 remediation: run_imbalance is reconstructible from closes alone
(sign of 1-bar close return, rolled mean). Estimator = Pearson on the
common finite grid (information content of signals, never returns).
"""
import numpy as np

import ancestry as anc


def test_run_imbalance_shadow_golden_hand_computed():
    # uptrend: ret1 = +1 each bar => sign = +1 => rolling(3).sum()/3 = +1
    up = np.array([100.0, 101.0, 102.0, 103.0, 104.0])
    got = anc.run_imbalance_shadow(up, window=3)
    assert np.isnan(got[:3]).all()      # ret1[0] NaN + rolling warmup
    assert np.allclose(got[3:], 1.0)

    # downtrend: sign = -1 => rolling mean -1
    dn = np.array([104.0, 103.0, 102.0, 101.0, 100.0])
    got = anc.run_imbalance_shadow(dn, window=3)
    assert np.allclose(got[3:], -1.0)

    # alternating: signs +1,-1,+1,-1 => rolling(2).sum()/2 = 0
    alt = np.array([100.0, 101.0, 100.0, 101.0, 100.0])
    got = anc.run_imbalance_shadow(alt, window=2)
    assert np.isnan(got[:2]).all()
    assert np.allclose(got[2:], 0.0)


def test_run_imbalance_shadow_default_window_matches_lane_convention():
    # default window is 24 hourly bars = the lane convention used for the
    # other shadows (rev24 horizon, close-displace, amihud rolling)
    up = np.arange(100.0, 130.0)  # 29 up bars
    got = anc.run_imbalance_shadow(up)  # default window=24
    assert np.isnan(got[:24]).all()
    assert np.allclose(got[24:], 1.0)


def test_signal_rho_estimator_on_known_series():
    a = np.array([0.0, 0.0, 1.0, 1.0, 1.0, 1.0])
    b = np.array([1.0, 1.0, 1.0, 1.0, 1.0, 1.0])  # zero variance => nan
    assert np.isnan(anc.signal_rho(a, b))
    c = np.array([0.0, 0.0, 0.0, 0.0, 1.0, 1.0])
    r = anc.signal_rho(a, c)
    assert 0.0 < r <= 1.0
    # NaN handling: common finite grid only
    a2 = np.array([np.nan, 0.0, 1.0, 1.0, 1.0, 1.0])
    r2 = anc.signal_rho(a2, c)
    assert np.isfinite(r2)
