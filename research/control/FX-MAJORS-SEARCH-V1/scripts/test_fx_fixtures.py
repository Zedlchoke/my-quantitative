"""FX-MAJORS fixtures: pip parametrization + JPY scale + PIT truncation."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import engine as E
import v2_lib as V


def make_h1(n_days=30, base=1.1000):
    rows = []
    t0 = pd.Timestamp("2022-01-03 00:00", tz="UTC")
    for d in range(n_days):
        for h in range(24):
            ts = t0 + pd.Timedelta(days=d, hours=h)
            mid = base + 0.0003 * np.sin(d * 3 + h) * (base / 1.1) + 0.00002 * h * (base / 1.1)
            sp = 0.00008 * (base / 1.1)
            rows.append((ts, mid, mid + 0.0004 * (base / 1.1), mid - 0.0004 * (base / 1.1),
                         mid + 0.0001 * (base / 1.1), mid + sp, mid + sp + 0.0004 * (base / 1.1),
                         mid + sp - 0.0004 * (base / 1.1), mid + sp + 0.0001 * (base / 1.1)))
    df = pd.DataFrame(rows, columns=["ts", "b_o", "b_h", "b_l", "b_c", "a_o", "a_h", "a_l", "a_c"])
    return V.H1Plane(df)


def test_pip_param_usdjpy():
    p = make_h1(3, base=150.0)  # JPY-scale prices
    tgt = np.zeros(len(p.ts), dtype=np.int8)
    tgt[1:50] = 1
    trades, _ = E.run_strategy(p, tgt, k=1.0, pip=0.01)
    t = trades[0]
    move = t["exit_px"] - t["entry_px"]
    expected_pips = move / 0.01
    # engine rounds stored pips to 2dp (byte-frozen from V1); at JPY pip size
    # that is 0.01-pip granularity — tolerance reflects the display rounding
    assert abs(t["pips"] - expected_pips) < 0.005


def test_pip_param_eurusd_backcompat():
    p = make_h1(3)
    tgt = np.zeros(len(p.ts), dtype=np.int8)
    tgt[1:50] = 1
    t = E.run_strategy(p, tgt, k=1.0, pip=1e-4)[0][0]
    move = t["exit_px"] - t["entry_px"]
    assert abs(t["pips"] - move / 1e-4) < 0.005


def test_pit_truncation_pair_families():
    for base, pip in ((1.27, 1e-4), (150.0, 0.01)):
        p = make_h1(40, base=base)
        cases = [("gap", V.f_gap, {"th": 5, "mode": "follow"}, pip),
                  ("pdhloc", V.f_pdhloc, {"buf_pips": 2, "opposite_exit": True}, pip),
                  ("roundnum", V.f_roundnum, {"grid_pips": 50, "prox_pips": 5}, pip)]
        T = len(p.ts) // 2
        fulls = {name: fn(p, **cfg, pip=pip) for name, fn, cfg, _ in cases}
        df = pd.DataFrame({
            "ts": pd.to_datetime(p.ts[:T], unit="s", utc=True),
            "b_o": p.b_o[:T], "b_h": p.b_h[:T], "b_l": p.b_l[:T], "b_c": p.b_c[:T],
            "a_o": p.a_o[:T], "a_c": p.a_c[:T]})
        pt = V.H1Plane(df)
        for name, fn, cfg, _ in cases:
            trunc = fn(pt, **cfg, pip=pip)
            assert np.array_equal(fulls[name][:T], trunc), f"PIT violation {name}@{base}"


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
