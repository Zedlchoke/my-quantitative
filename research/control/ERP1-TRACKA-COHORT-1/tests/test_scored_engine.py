"""Hand-fixture tests for the scored engine — ERP1-TRACKA-COHORT-1.

Required fixtures (dispatch): cost charged exactly once per side,
force-flat at the day close, no-lookahead one-bar-lag mutation, fold
boundary. The fill law under test is scripts/engine.run_strategy (the
ancestry port) driven on tracka_lib.SignalPlane — exactly the scored
path (scored_lib.run_cell).
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))

import scored_lib as S  # noqa: E402
import tracka_lib as T  # noqa: E402

D0, D1, D2 = "2021-01-04", "2021-01-05", "2021-01-06"
PIP = 1e4


def make_frame(days=(D0, D1, D2), hours=20, p0=1.0000, step=0.0,
               spread=0.0002):
    rows = []
    px = p0
    for d in days:
        for h in range(hours):
            bo = round(px, 6)
            bc = round(px + step, 6)
            rows.append({
                "ts": pd.Timestamp(f"{d}T{h:02d}:00:00Z"),
                "b_o": bo, "b_h": round(max(bo, bc) + 0.0001, 6),
                "b_l": round(min(bo, bc) - 0.0001, 6), "b_c": bc,
                "a_o": round(bo + spread, 6),
                "a_c": round(bc + spread, 6),
            })
            px = bc + step
    return pd.DataFrame(rows)


def bar_ts(day, hour):
    return int(pd.Timestamp(f"{day}T{hour:02d}:00:00Z").timestamp())


def idx(day, hour):
    di = {D0: 0, D1: 1, D2: 2}[day]
    return di * hours_n + hour


hours_n = 20


# ------------------------------------------------- 1. cost exactly once ----

def test_cost_charged_exactly_once_per_side():
    df = make_frame()
    # hand-set the two fill bars: entry fill bar (D0 h06), exit fill bar
    # (D0 h07). b_o=bid open; s_o = a_o - b_o.
    df.loc[idx(D0, 6), ["b_o", "a_o"]] = [1.1000, 1.1002]   # s_o = 2 pips
    df.loc[idx(D0, 7), ["b_o", "a_o"]] = [1.1010, 1.1012]   # s_o = 2 pips
    p = T.SignalPlane(df, pip_mult=PIP)
    tgt = np.zeros(len(df), dtype=np.int8)
    tgt[idx(D0, 5)] = 1                      # signal bar -> fill at h06
    trades, _ = S.run_cell(p, tgt, 1.0, warmup_end_idx=0)
    assert len(trades) == 1
    t = trades[0]
    # buy at bid+k*s = 1.1000+0.0002 ; sell at ask-k*s = 1.1012-0.0002
    assert t["entry_px"] == pytest.approx(1.1002, abs=1e-9)
    assert t["exit_px"] == pytest.approx(1.1010, abs=1e-9)
    assert t["pips"] == pytest.approx(8.0, abs=1e-6)
    # k-linearity: pnl(k) = pnl(0) - k*(s_entry+s_exit)*pip_mult
    # pnl(0) = a_o(exit) - b_o(entry) = 12 pips; s_e+s_x = 4 pips
    trades15, _ = S.run_cell(p, tgt, 1.5, warmup_end_idx=0)
    assert trades15[0]["pips"] == pytest.approx(6.0, abs=1e-6)
    dec = S.decompose(p, trades, 1.0)
    assert dec["net_pips"] == pytest.approx(8.0, abs=1e-6)
    assert dec["cost_pips"] == pytest.approx(4.0, abs=1e-6)
    assert dec["gross_pips"] == pytest.approx(12.0, abs=1e-6)  # k=0 book


# ----------------------------------------------------- 2. force-flat law ----

def test_force_flat_at_day_close_no_overnight():
    df = make_frame()
    p = T.SignalPlane(df, pip_mult=PIP)
    tgt = np.zeros(len(df), dtype=np.int8)
    tgt[idx(D0, 5):idx(D1, 6) + 1] = 1       # long through the day boundary
    k = 1.0
    trades, _ = S.run_cell(p, tgt, k, warmup_end_idx=0)
    assert len(trades) == 2, "day-close must split the holding into 2 trips"
    t0, t1 = trades
    # trip 1: entry fill at D0 h06, force-flat at the day-close bar (h19)
    assert t0["entry_ts"] == bar_ts(D0, 6)
    assert t0["exit_ts"] == bar_ts(D0, 19)
    dc = idx(D0, 19)
    assert t0["exit_px"] == pytest.approx(
        float(p.a_c[dc] - k * p.s_c[dc]), abs=1e-9)   # close-spread exit
    # trip 2: re-enter the first fillable bar of D1 (00:00 open)
    assert t1["entry_ts"] == bar_ts(D1, 0)
    assert t1["entry_ts"] // 86400 > t0["exit_ts"] // 86400
    # no position survives past the day-close bar: exit day == entry day
    for t in trades:
        assert t["entry_ts"] // 86400 == t["exit_ts"] // 86400


# ------------------------------- 3. no-lookahead one-bar-lag mutation ----

def test_no_lookahead_one_bar_lag():
    df = make_frame()
    p = T.SignalPlane(df, pip_mult=PIP)
    tgt = np.zeros(len(df), dtype=np.int8)
    tgt[idx(D0, 5)] = 1
    trades, _ = S.run_cell(p, tgt, 1.0, warmup_end_idx=0)
    assert len(trades) == 1
    # (a) the fill is at the NEXT bar's open, never at the signal bar
    assert trades[0]["entry_ts"] == bar_ts(D0, 6)
    # (b) mutating the SIGNAL bar's own prices cannot move the fill price
    df2 = df.copy()
    df2.loc[idx(D0, 5), ["b_o", "b_h", "b_l", "b_c", "a_o", "a_c"]] = \
        [9.0, 9.5, 8.5, 9.2, 9.6, 9.7]
    p2 = T.SignalPlane(df2, pip_mult=PIP)
    trades2, _ = S.run_cell(p2, tgt, 1.0, warmup_end_idx=0)
    assert trades2[0]["entry_px"] == trades[0]["entry_px"]
    # (c) mutating the FILL bar's high/low (open kept) cannot move it either
    df3 = df.copy()
    df3.loc[idx(D0, 6), "b_h"] = 5.0
    df3.loc[idx(D0, 6), "b_l"] = 0.5
    p3 = T.SignalPlane(df3, pip_mult=PIP)
    trades3, _ = S.run_cell(p3, tgt, 1.0, warmup_end_idx=0)
    assert trades3[0]["entry_px"] == trades[0]["entry_px"]
    # (d) moving the signal one bar later moves the fill one bar later
    tgt4 = np.zeros(len(df), dtype=np.int8)
    tgt4[idx(D0, 6)] = 1
    trades4, _ = S.run_cell(p, tgt4, 1.0, warmup_end_idx=0)
    assert trades4[0]["entry_ts"] == bar_ts(D0, 7)


# ------------------------------------------------------- 4. fold boundary ----

def test_fold_boundary_no_straddle():
    df = make_frame()
    p = T.SignalPlane(df, pip_mult=PIP)
    tgt = np.zeros(len(df), dtype=np.int8)
    tgt[idx(D0, 5):idx(D1, 6) + 1] = 1
    k = 1.0
    trades, _ = S.run_cell(p, tgt, k, warmup_end_idx=0)
    fold_table = [("FA", D0, D0), ("FB", D1, D2)]   # boundary at the day seam
    gm = S.gate_metrics(p, trades, k, fold_table=fold_table)
    assert gm["fold_straddles"] == 0, "day-close force-flat must keep every \
trade inside its fold (force-flat at fold boundaries is structural)"
    assert gm["per_fold_trades"]["FA"] == 1
    assert gm["per_fold_trades"]["FB"] == 1
    assert gm["per_fold_net_pips"]["FA"] == pytest.approx(
        trades[0]["pips"], abs=1e-9)
    assert gm["per_fold_net_pips"]["FB"] == pytest.approx(
        trades[1]["pips"], abs=1e-9)


# --------------------------------- 5. placebo stream determinism/parity ----

def test_placebo_stream_deterministic_and_parity():
    df = make_frame()
    p = T.SignalPlane(df, pip_mult=PIP)
    a = S.placebo_target_full_panel(p, r=1.0, hold_bars=2, seed=20260925)
    b = S.placebo_target_full_panel(p, r=1.0, hold_bars=2, seed=20260925)
    assert np.array_equal(a["tgt"], b["tgt"])
    # day parity: +1 on even traded-day index, -1 on odd
    days = p.traded_days()
    di = {int(d): j for j, d in enumerate(days)}
    nz = np.nonzero(a["tgt"] != 0)[0]
    seen = {}
    for i in nz:
        d = int(p.day[i])
        seen.setdefault(d, a["tgt"][i])
    for d, v in seen.items():
        assert v == (1 if di[d] % 2 == 0 else -1)
