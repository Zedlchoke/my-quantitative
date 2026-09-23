"""Signal-event golden tests: one-event entry/exit, stop, min-hold no-op law,
fold force-flat, decision-bar -> next-open execution convention.

Synthetic geometry note: the Donchian entry needs 480 bars of rolling
history, so synthetics place the breakout at bar 500 (n=900).
"""
import numpy as np
import pandas as pd

import proposals as prop
from signal_path import run_event_engine, EXECUTION_LAG_BARS


def synth_df(n=900, breakout_at=500, jump=20.0, drop=None):
    closes = np.full(n, 100.0)
    closes[breakout_at:] = 100.0 + jump
    if drop is not None:
        closes[drop[0]:] = drop[1]
    return pd.DataFrame({
        "open": closes, "high": closes, "low": closes, "close": closes,
        "state_label": ["UPTREND"] * n,
    })


def folds(n, split=10**9):
    f = np.zeros(n, dtype=int)
    if split < n:
        f[split:] = 1
    return f


def test_one_entry_then_gate_off_exit():
    df = synth_df(n=900, breakout_at=500)
    df.loc[600:, "state_label"] = "DISTRIBUTION"   # gate off long after min-hold
    ev, _ = prop.signals_uptrend_breakout(df, folds(900))
    assert ev.entries == [500]
    assert ev.exits == [(600, "PHASE_OR_STRUCTURE")]
    assert ev.hold_bars == [100]
    assert ev.exit_reasons == {"PHASE_OR_STRUCTURE": 1}
    assert ev.unnecessary_close_reopen == 0


def test_stop_exit_override():
    df = synth_df(n=900, breakout_at=500, drop=(560, 50.0))
    ev, _ = prop.signals_uptrend_breakout(df, folds(900))
    assert ev.entries == [500]
    assert ev.exits == [(560, "STOP")]
    assert ev.hold_bars == [60]
    # re-entry must NOT occur without a fresh breakout: closes stay 50 < hi_prev
    assert len(ev.entries) == 1


def test_min_hold_absorbs_gate_flicker_no_op_law():
    n = 900
    df = synth_df(n=n, breakout_at=500)
    # gate flickers off/on at bars 510..519 (< min-hold 24 after entry 500):
    # the flicker is absorbed, position continuous, ZERO fills
    df.loc[510:519, "state_label"] = "TRANSITION_UNKNOWN"
    df.loc[520:, "state_label"] = "UPTREND"
    ev, _ = prop.signals_uptrend_breakout(df, folds(n))
    assert len(ev.entries) == 1 and ev.entries[0] == 500
    assert len(ev.exits) == 0
    assert ev.bars_long == n - 500  # continuous hold from entry to window end


def test_min_hold_boundary_exit():
    # gate off at exactly entry+min-hold: one exit decision at that bar,
    # no re-entry without a fresh breakout
    n = 900
    df = synth_df(n=n, breakout_at=500)
    df.loc[500 + prop.MIN_HOLD_BARS:, "state_label"] = "DOWNTREND"
    ev, _ = prop.signals_uptrend_breakout(df, folds(n))
    assert ev.exits[0][0] == 500 + prop.MIN_HOLD_BARS
    assert len(ev.entries) == 1
    assert ev.hold_bars == [prop.MIN_HOLD_BARS]


def test_acc_floor_provision_markup_ride():
    """ACC entry held through the ACC->UPTREND transition (by design), exited
    when the state leaves the hold gate {ACC, UP}. The 720-bar range window
    needs 720 bars of history, so the synthetic drops at bar 800."""
    n = 1500
    df = synth_df(n=n, breakout_at=800, jump=-20.0)  # closes 80 from bar 800
    df["state_label"] = "DISTRIBUTION"
    df.loc[800:849, "state_label"] = "ACCUMULATION"   # entry window
    df.loc[850:949, "state_label"] = "UPTREND"        # markup ride (no event)
    df.loc[950:, "state_label"] = "DISTRIBUTION"      # gate leaves {ACC,UP}
    fold_ids = np.zeros(n, dtype=int)
    ev, _ = prop.signals_acc_floor_provision(df, fold_ids)
    assert ev.entries == [800]      # lower quartile of the 30d range (100/80)
    assert ev.exits == [(950, "PHASE_OR_STRUCTURE")]
    assert ev.hold_bars == [150]
    assert ev.exit_reasons == {"PHASE_OR_STRUCTURE": 1}


def test_fold_end_force_flat():
    n = 900
    df = synth_df(n=n, breakout_at=500)
    fold_ids = np.zeros(n, dtype=int)
    fold_ids[600:] = 1
    ev, _ = prop.signals_uptrend_breakout(df, fold_ids)
    assert ev.exits[0] == (599, "FOLD_END_FORCE_FLAT")  # last bar of old fold
    assert ev.fold_end_forced_flats == 1
    assert ev.hold_bars[0] == 99


def test_execution_convention_next_open():
    assert EXECUTION_LAG_BARS == 1
    n = 900
    df = synth_df(n=n, breakout_at=500)
    ev, _ = prop.signals_uptrend_breakout(df, folds(n))
    for e in ev.entries:
        assert e + EXECUTION_LAG_BARS <= n  # executable bar exists


def test_short_mirror_breakdown():
    df = synth_df(n=900, breakout_at=500, jump=-20.0)
    df["state_label"] = "DOWNTREND"
    df.loc[600:, "state_label"] = "TRANSITION_UNKNOWN"
    ev, _ = prop.signals_downtrend_breakdown_cont(df, folds(900))
    assert ev.entries == [500]
    assert ev.exits == [(600, "PHASE_OR_STRUCTURE")]
    assert ev.bars_short > 0 and ev.bars_long == 0


def test_phase_shuffled_control_semantics_deterministic():
    """Control semantics frozen now: episode-block permutation within fold,
    seed 20260923 — permutation is reproducible (determinism only here; the
    control PnL comparison happens in the scored run, NOT in this lane)."""
    labels = ["UPTREND"] * 50 + ["ACCUMULATION"] * 30 + ["UPTREND"] * 20 + \
             ["DOWNTREND"] * 40
    blocks = _episode_blocks(labels)
    perm = _permute_blocks(labels, blocks, seed=20260923)
    again = _permute_blocks(labels, blocks, seed=20260923)
    assert perm == again                       # deterministic under frozen seed
    assert len(perm) == len(labels)            # length preserved
    assert set(perm) == set(labels)            # value set preserved
    assert any(a != b for a, b in zip(perm, labels))  # a real shuffle happened


def _episode_blocks(labels):
    blocks, start = [], 0
    for i in range(1, len(labels)):
        if labels[i] != labels[i - 1]:
            blocks.append((start, i))
            start = i
    blocks.append((start, len(labels)))
    return blocks


def _permute_blocks(labels, blocks, seed):
    import random
    rng = random.Random(seed)
    vals = [labels[s] for s, _ in blocks]
    lens = [e - s for s, e in blocks]
    rng.shuffle(vals)
    out = []
    for v, ln in zip(vals, lens):
        out.extend([v] * ln)
    return out
