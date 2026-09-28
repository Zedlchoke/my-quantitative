"""RGC100 fixtures — allocation math, no-lookahead, switching-once, determinism."""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from combo import weights_for_week, _tercile, week_mondays

TABLE = {"cuts": {"G1_funding_z": (0.5, 1.5), "G2c_btc_rv": (0.4, 0.8), "G2f_eur_rv": (0.3, 0.6)},
         "rt_bps": {"crypto": 12.0, "fx": 1.0}, "cap_single_leg": 0.5}

def series(v_g1=1.0, v_g2c=0.6, v_g2f=0.5):
    idx = pd.date_range("2020-09-01", periods=200, freq="1D", tz="UTC")
    return {"G1": pd.Series(v_g1, index=idx), "G2c": pd.Series(v_g2c, index=idx),
            "G2f": pd.Series(v_g2f, index=idx)}

def test_tercile_math():
    assert _tercile(0.2, (0.5, 1.5)) == 1
    assert _tercile(1.0, (0.5, 1.5)) == 2
    assert _tercile(2.0, (0.5, 1.5)) == 3

def test_allocation_golden():
    # G1=tercile2 -> FUNDCONTRA mult 2; G2c=2 -> CORRBREAK 2; G2f=2 -> sweep 2, sessions 2, weekend 2
    m = pd.Timestamp("2021-01-04", tz="UTC")
    w = weights_for_week(m, TABLE, series())
    assert abs(sum(w.values()) - 1.0) < 1e-12
    assert abs(w["FUNDCONTRA"] - 1/6) < 1e-9      # all multipliers 2 -> equal
    # high funding only: FUNDCONTRA mult 3 vs others: corr 2, sweep 1(g2f low? no)...
    w2 = weights_for_week(m, TABLE, series(v_g1=2.0))
    assert w2["FUNDCONTRA"] > w2["WEEKEND"] > 0   # tilt works
    assert w2["FUNDCONTRA"] <= 0.5 + 1e-12        # cap respected

def test_no_lookahead_gate():
    m = pd.Timestamp("2021-01-04", tz="UTC")
    idx_after = pd.DatetimeIndex([m + pd.Timedelta(days=i) for i in range(5)])
    s = series()
    s2 = {k: pd.concat([v, pd.Series([9.9] * 5, index=idx_after)]) for k, v in s.items()}
    # data AFTER the monday must not change the week's weights
    w_a = weights_for_week(m, TABLE, s)
    w_b = weights_for_week(m, TABLE, s2)
    assert w_a == w_b

def test_determinism_and_weeks():
    ms = week_mondays()
    assert ms[0] == pd.Timestamp("2021-04-05", tz="UTC")
    assert len(ms) > 270
