"""PSV1 scored-engine fixture tests (hand-computed; plan §14)."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import accounting as acc  # noqa: E402
from books import (  # noqa: E402
    _episode_blocks, _ks_2samp, _permute_labels_by_episode_blocks,
    _target_to_fills, baseline_sparse_risk_off,
)


def test_cost_once_and_trade_net_hand_computed():
    o = np.array([100.0, 110.0, 120.0])
    c = np.array([105.0, 120.0, 130.0])
    # entry at open[1], exit at close[2] (position holds bar 2)
    fills = [(1, 1.0, False), (2, 0.0, True)]
    r = acc.run_accounting(o, c, fills, np.zeros(3, dtype=int), 6.0)
    c_fee = 6.0 / 1e4
    expected_net = (100000.0 * (1 - c_fee) * (120.0 / 110.0) * (130.0 / 120.0)
                    * (1 - c_fee) - 100000.0)
    assert r["net"] == pytest.approx(expected_net, rel=1e-12)
    assert r["gross"] == pytest.approx(
        100000.0 * (1 - c_fee) * ((120.0 / 110.0 - 1) + (120.0 / 110.0) * (130.0 / 120.0 - 1)),
        rel=1e-9)
    assert r["trades"] == 1
    assert r["funding"] == 0.0
    # identity: net = gross - fees
    assert r["net"] == pytest.approx(r["gross"] - r["fees"], rel=1e-9)


def test_tier_scales_full_stack_closed_form():
    o = np.array([100.0, 110.0, 120.0])
    c = np.array([105.0, 120.0, 130.0])
    fold = np.zeros(3, dtype=int)
    fills = [(1, 1.0, False), (2, 0.0, True)]  # enter open t1, exit close t2
    for tier in (1.0, 1.5, 2.0):
        r = acc.run_accounting(o, c, fills, fold, 6.0, tier=tier)
        cf = 6.0 * tier / 1e4
        expected = (100000.0 * (1 - cf) * (120.0 / 110.0) * (130.0 / 120.0)
                    * (1 - cf) - 100000.0)
        assert r["net"] == pytest.approx(expected, rel=1e-12)


def test_funding_scales_exactly_with_single_charge():
    o = np.array([100.0, 110.0, 120.0])
    c = np.array([105.0, 120.0, 130.0])
    fold = np.zeros(3, dtype=int)
    mask = np.array([False, True, False])  # exactly one funding event
    fills = [(1, 1.0, False), (2, 0.0, True)]
    r1 = acc.run_accounting(o, c, fills, fold, 0.0, tier=1.0, funding_mask=mask,
                            funding_rate=1.377e-5)
    r2 = acc.run_accounting(o, c, fills, fold, 0.0, tier=2.0, funding_mask=mask,
                            funding_rate=1.377e-5)
    assert r1["fees"] == 0.0 and r2["fees"] == 0.0
    assert r2["funding"] == pytest.approx(2 * r1["funding"], rel=1e-12)
    assert r1["funding"] < 0  # long pays positive funding


def test_gap_accrues_to_incoming_position():
    o = np.array([100.0, 121.0, 100.0])
    c = np.array([110.0, 110.0, 100.0])
    fills = [(0, 1.0, False), (2, 0.0, True)]
    fold = np.zeros(3, dtype=int)
    r = acc.run_accounting(o, c, fills, fold, 0.0)
    assert r["net"] == pytest.approx(0.0, abs=1e-6)


def test_same_bar_exit_entry_netted():
    o = np.array([100.0, 110.0])
    c = np.array([105.0, 120.0])
    fills = [(1, 1.0, False), (1, 0.0, True)]  # nets to flat: no trade, no cost
    r = acc.run_accounting(o, c, fills, np.zeros(2, dtype=int), 6.0)
    assert r["net"] == 0.0
    assert r["fees"] == 0.0
    assert r["raw_fill_events"] == 2


def test_fold_force_flat_and_fold_decomposition():
    o = np.array([100.0, 110.0, 120.0, 130.0])
    c = np.array([105.0, 115.0, 125.0, 135.0])
    fold = np.array([0, 0, 1, 1])
    fills = [(0, 1.0, False), (1, 0.0, True), (2, 1.0, False), (3, 0.0, True)]
    r = acc.run_accounting(o, c, fills, fold, 6.0)
    assert sum(r["per_fold_net"].values()) == pytest.approx(r["net"], rel=1e-9)
    assert r["trades"] == 2


def test_target_to_fills_fold_law():
    decision = np.array([1.0, 1.0, 1.0, 0.0])
    fold = np.array([0, 0, 1, 1])
    fills = _target_to_fills(decision, fold)
    # fold0 = [t0,t1]: a t0 decision would hold only on fold0's LAST bar ->
    # force-flat leaves NO fold0 trade (during[1] flattened to 0).
    # t1 decision -> long from open t2; fold1 ends t3 -> flat at close t3.
    assert fills == [(2, 1.0, False), (3, 0.0, True)]


def test_sparse_risk_off_thresholds():
    close = np.array([100.0 * (1 + 0.01 * i) for i in range(50)] + [60.0] * 5 + [95.0] * 5)
    cell = {"close": close, "fold_ids": np.zeros(len(close), dtype=int)}
    fills = baseline_sparse_risk_off(cell, out_dd=0.30, in_dd=0.10, min_hold=5)
    assert any(s == 1.0 for b, s, _ in fills if b < 50)               # long during rise
    assert any(s == 0.0 and b >= 50 for b, s, _ in fills)             # exits after crash


def test_ks_identical_and_disjoint():
    a = np.linspace(0, 1, 100)
    assert _ks_2samp(a, a) == pytest.approx(0.0)
    assert _ks_2samp(a, a + 10.0) == pytest.approx(1.0)


def _synthetic_cell():
    rng = np.random.default_rng(7)
    n = 400
    words = np.array(["ACCUMULATION", "UPTREND", "DOWNTREND", "TRANSITION_UNKNOWN"])
    blocks = rng.integers(0, 4, n // 10)
    labels = np.repeat(words[blocks], 10)[:n].astype(str)
    fold = np.zeros(n, dtype=int)
    fold[n // 2:] = 1
    cell = {"labels_df": {"state_label": labels}, "fold_ids": fold,
            "close": np.linspace(1, 2, n)}
    return cell, labels


def test_episode_block_permutation_preserves_structure():
    cell, labels = _synthetic_cell()
    rng = np.random.default_rng(20260923)
    out = _permute_labels_by_episode_blocks(cell, rng)
    assert sorted(out.tolist()) == sorted(labels.tolist())  # occupancy preserved
    blocks_b = _episode_blocks(labels, cell["fold_ids"])
    runs_a = _episode_blocks(out, cell["fold_ids"])
    # permutation reorders whole episode blocks; adjacent same-label blocks
    # in the new order MERGE by construction — run count can only shrink,
    # never grow, and total span per fold is preserved.
    assert len(runs_a) <= len(blocks_b)
    for f in (0, 1):
        span_a = sum(ln for ff, s, ln, lb in runs_a if ff == f)
        span_b = sum(ln for ff, s, ln, lb in blocks_b if ff == f)
        assert span_a == span_b
    rng2 = np.random.default_rng(20260923)
    out2 = _permute_labels_by_episode_blocks(cell, rng2)
    assert out.tolist() == out2.tolist()  # deterministic under seed
