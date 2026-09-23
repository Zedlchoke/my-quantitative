"""V2 fixtures: H1-plane masks + PIT truncation invariance for new families."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import engine as E
import v2_lib as V


def make_h1(n_days=30):
    rows = []
    t0 = pd.Timestamp("2022-01-03 00:00", tz="UTC")
    for d in range(n_days):
        for h in range(24):
            ts = t0 + pd.Timedelta(days=d, hours=h)
            mid = 1.1000 + 0.0003 * np.sin(d * 3 + h) + 0.00002 * h
            sp = 0.00008
            rows.append((ts, mid, mid + 0.0004, mid - 0.0004, mid + 0.0001,
                         mid + sp, mid + sp + 0.0004, mid + sp - 0.0004,
                         mid + sp + 0.0001))
    df = pd.DataFrame(rows, columns=["ts", "b_o", "b_h", "b_l", "b_c",
                                     "a_o", "a_h", "a_l", "a_c"])
    return V.H1Plane(df)


def test_h1_masks():
    p = make_h1(5)
    assert p.skip[p.hour >= 20].all()
    assert not p.fill_ok[p.hour >= 19].any()
    assert p.is_day_close[p.hour == 19].all()
    assert not p.fill_ok[0]


def test_force_flat_before_rollover_h1():
    p = make_h1(6)
    tgt = np.ones(len(p.ts), dtype=np.int8)
    trades, _ = E.run_strategy(p, tgt, k=1.0)
    assert len(trades) == 6  # one round trip per day
    for t in trades:
        di = p.ts.searchsorted(t["entry_ts"]); de = p.ts.searchsorted(t["exit_ts"])
        assert p.day[di] == p.day[de]
        assert p.hour[de] <= 19  # closed at/before the 20:00 boundary


def test_pit_truncation_v2_families():
    p = make_h1(40)
    cases = [
        ("gap", V.f_gap, {"th": 5, "mode": "follow"}),
        ("pdhloc", V.f_pdhloc, {"buf": 0.0, "opposite_exit": True}),
        ("h1tsmom", V.f_h1tsmom, {"K": 24}),
        ("stoch", V.f_stoch, {"N": 24, "th_hi": 80, "th_lo": 20}),
        ("hourrev", V.f_hourrev, {"win_days": 5, "invert": True}),
    ]
    for name, fn, cfg in cases:
        full = fn(p, **cfg)
        T = len(p.ts) // 2
        df = pd.DataFrame({
            "ts": pd.to_datetime(p.ts[:T], unit="s", utc=True),
            "b_o": p.b_o[:T], "b_h": p.b_h[:T], "b_l": p.b_l[:T], "b_c": p.b_c[:T],
            "a_o": p.a_o[:T], "a_c": p.a_c[:T],
        })
        pt = V.H1Plane(df)
        trunc = fn(pt, **cfg)
        assert np.array_equal(full[:T], trunc), f"PIT violation in {name}"


def test_cost_only_random_negative_h1():
    p = make_h1(30)
    rng = np.random.default_rng(7)
    tgt = rng.integers(-1, 2, size=len(p.ts)).astype(np.int8)
    trades, _ = E.run_strategy(p, tgt, k=1.0)
    m = E.metrics(trades, np.zeros(len(p.ts)))
    assert m["net_pips"] < 0 and m["trades"] > 10


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
