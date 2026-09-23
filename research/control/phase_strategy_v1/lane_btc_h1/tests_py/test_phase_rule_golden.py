"""Phase-rule golden tests: named outputs, UNKNOWN law, tie rules, warmup,
state machine, and the hand-computed Wilder ADX fixture (period 3)."""
import numpy as np
import pandas as pd
import pytest

import phase_rule as pr


def test_frozen_params_match_freeze_file():
    freeze = pr.load_freeze("phase_rule_freeze.json")
    p = freeze["parameters_frozen"]
    assert p["adx_period"] == pr.ADX_PERIOD == 14
    assert p["adx_trend_threshold"] == pr.ADX_TREND_THRESHOLD == 20.0
    assert p["adx_margin"] == pr.ADX_MARGIN == 2.0
    assert p["sma_slow_bars"] == pr.SMA_SLOW_BARS == 720
    assert p["warmup_bars"] == pr.WARMUP_BARS == 720
    assert p["transition_buffer_bars"] == pr.TRANSITION_BUFFER_BARS == 24
    assert freeze["outputs"] == pr.PHASES


def test_hand_computed_wilder_adx_period3_pure_uptrend():
    """Hand computation (shown in full): H=[10..17], L=H-1, C=H, period 3.
    Every bar: TR=1, +DM=1, -DM=0 (up move exceeds down move; down move
    negative => 0). Wilder seed sm_TR=sm+DM=3, sm-DM=0 => DI+=100, DI-=0,
    DX=100. ADX seeds to 100 and stays 100."""
    h = np.arange(10, 18, dtype=float)
    l = h - 1.0
    c = h.copy()
    adx, dip, dim = pr.adx_di(h, l, c, period=3)
    assert np.allclose(dip[3:], 100.0)
    assert np.allclose(dim[3:], 0.0)
    assert np.allclose(adx[5:], 100.0)


def test_raw_label_law_total_partition():
    n = 10
    close = np.full(n, 100.0)
    sma = np.full(n, 100.0)
    idx = np.arange(n)

    def labels_for(adx, dip, dim):
        return pr.raw_labels(close, np.full(n, adx), np.full(n, dip),
                             np.full(n, dim), sma, warmup_bars=4)

    assert labels_for(30.0, 25.0, 5.0)[4:] == ["UPTREND"] * 6   # trend, DI+ >= DI-
    assert labels_for(30.0, 5.0, 25.0)[4:] == ["DOWNTREND"] * 6
    assert labels_for(10.0, 25.0, 5.0)[4:] == ["DISTRIBUTION"] * 6  # range, close>=sma
    lo_close = close.copy(); lo_close[:] = 90.0
    got = pr.raw_labels(lo_close, np.full(n, 10.0), np.full(n, 25.0),
                        np.full(n, 5.0), sma, warmup_bars=4)
    assert got[4:] == ["ACCUMULATION"] * 6
    # margin band (18,22) exclusive
    assert labels_for(21.9, 25.0, 5.0)[4:] == ["TRANSITION_UNKNOWN"] * 6
    assert labels_for(18.1, 25.0, 5.0)[4:] == ["TRANSITION_UNKNOWN"] * 6
    assert labels_for(18.0, 25.0, 5.0)[4:] == ["DISTRIBUTION"] * 6  # boundary: range side
    assert labels_for(22.0, 25.0, 5.0)[4:] == ["UPTREND"] * 6   # boundary: trend side
    # warmup => UNKNOWN regardless
    assert labels_for(30.0, 25.0, 5.0)[:4] == ["TRANSITION_UNKNOWN"] * 4
    assert idx is not None


def test_tie_rules():
    n = 6
    close = np.full(n, 100.0)
    sma = np.full(n, 100.0)
    # DI+ == DI- exactly with ADX >= hi resolves UPTREND (frozen >=)
    got = pr.raw_labels(close, np.full(n, 30.0), np.full(n, 20.0),
                        np.full(n, 20.0), sma, warmup_bars=2)
    assert got[2:] == ["UPTREND"] * 4
    # close == SMA exactly with ADX <= lo resolves DISTRIBUTION (frozen >=)
    got = pr.raw_labels(close, np.full(n, 10.0), np.full(n, 20.0),
                        np.full(n, 20.0), sma, warmup_bars=2)
    assert got[2:] == ["DISTRIBUTION"] * 4


def test_state_machine_buffer_adoption():
    # A persists, B blips for 23 bars (NOT adopted), then real 24-bar C run
    raw = ["A"] * 50 + ["B"] * 23 + ["A"] * 5 + ["C"] * 24 + ["A"] * 10
    st = pr.state_labels(raw, buffer_bars=24)
    assert set(st[:50]) == {"A"}
    assert set(st[50:73]) == {"A"}            # 23-bar blip absorbed
    assert set(st[73:78]) == {"A"}
    assert set(st[78:101]) == {"A"}           # bars 78..100 not yet adopted
    assert st[101] == "C"                     # adopted on 24th consecutive bar
    assert st[102] == "C"                     # 1 bar of A cannot flip back
    assert set(st[102:]) == {"C"}
    # UNKNOWN obeys the identical persistence law
    raw2 = ["A"] * 50 + ["TRANSITION_UNKNOWN"] * 24 + ["A"] * 5
    st2 = pr.state_labels(raw2, buffer_bars=24)
    assert st2[50 + 23] == "TRANSITION_UNKNOWN"
    assert st2[50 + 24] == "TRANSITION_UNKNOWN"  # 2 bars of A cannot flip back
    assert st2[50 + 25] == "TRANSITION_UNKNOWN"
    assert set(st2[74:]) == {"TRANSITION_UNKNOWN"}


def test_state_min_dwell_by_construction():
    rng = np.random.default_rng(7)
    raw = list(rng.choice(["A", "B", "C"], size=2000))
    st = pr.state_labels(raw, buffer_bars=24)
    runs = cen_runs(st)
    assert all(r >= 24 for r in runs)


def cen_runs(seq):
    runs, cur = [], 1
    for a, b in zip(seq[:-1], seq[1:]):
        if a == b:
            cur += 1
        else:
            runs.append(cur)
            cur = 1
    runs.append(cur)
    return runs


def test_compute_labels_end_to_end_synthetic_trend():
    """Synthetic path: flat 800 bars at 100, then a sustained uptrend.
    Post-warmup labels must be named phases; warmup all UNKNOWN."""
    n = 1600
    close = np.concatenate([np.full(800, 100.0), np.linspace(100, 200, 800)])
    df = pd.DataFrame({
        "open": close, "high": close + 0.5, "low": close - 0.5, "close": close,
    }, index=pd.date_range("2020-01-01", periods=n, freq="h", tz="UTC"))
    out = pr.compute_labels(df.reset_index(drop=True))
    assert out["state_label"][:720].nunique() == 1
    assert out["state_label"].iloc[0] == "TRANSITION_UNKNOWN"
    late = out["state_label"].iloc[1200:]
    assert set(late) <= set(pr.PHASES)
    assert late.iloc[-1] == "UPTREND"  # sustained markup with rising SMA anchor
