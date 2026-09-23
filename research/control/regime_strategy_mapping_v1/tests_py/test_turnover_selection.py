"""Unit tests: turnover-law router + nested selection law (synthetic only).

No real data, no PnL — these prove the frozen laws on hand-built series.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from rsmv1.data import Bars  # noqa: E402
from rsmv1.selection import (  # noqa: E402
    SpecialistCandidate,
    select_for_fold,
)
from rsmv1.strategies import FLAT, MR_LONG, TREND_LONG, TREND_SHORT  # noqa: E402
from rsmv1.turnover import (  # noqa: E402
    BUFFER_REGIME_BARS,
    TargetRouter,
    buffered_labels,
    direction_of,
    position_switches,
    reversal_count,
    v2_jev_only_trade_cap,
)

H1 = 3_600_000_000_000


def _bars(n: int, start_ns: int = 0, step_ns: int = 900_000_000_000) -> Bars:
    ts_o = np.array([start_ns + i * step_ns for i in range(n)], dtype=np.int64)
    ts_c = ts_o + step_ns - 1
    rng = np.random.default_rng(7)
    close = 100.0 + np.cumsum(rng.normal(0, 0.5, n))
    o = close + rng.normal(0, 0.1, n)
    return Bars(
        ts_open=ts_o,
        ts_close=ts_c,
        open=o,
        high=np.maximum(o, close) + 0.2,
        low=np.minimum(o, close) - 0.2,
        close=close,
        volume=np.ones(n),
    )


# ---------------------------------------------------------------- turnover


def test_direction_of():
    assert direction_of(TREND_LONG) == 1
    assert direction_of(MR_LONG) == 1
    assert direction_of(TREND_SHORT) == -1
    assert direction_of(FLAT) == 0
    assert direction_of(None) == 0


def test_buffered_labels_delays_by_k():
    ts = [i * H1 for i in range(6)]
    lab = ["A", "A", "B", "B", "A", "A"]
    t2, l2 = buffered_labels(ts, lab, 1)
    # label known at ts[i] applies from ts[i+1]: ts[1:] carries lab[:5]
    assert l2 == ["A", "A", "B", "B", "A"]
    assert t2 == ts[1:]
    t0, l0 = buffered_labels(ts, lab, 0)
    assert (t0, l0) == (ts, lab)
    assert BUFFER_REGIME_BARS == 1


def test_router_noop_same_direction():
    """Label change mapping ACC->MR_LONG then UP->TREND_LONG (both long):
    the emitted string must NOT change -> no engine reconciliation -> no
    fill (the engine only reconciles when the string changes)."""
    n_reg = 8
    regime_ts = [i * H1 for i in range(n_reg)]
    persisted = ["ACCUMULATION"] * 3 + ["UPTREND"] * 5
    mapping = {
        "ACCUMULATION": MR_LONG,
        "UPTREND": TREND_LONG,
        "DISTRIBUTION": FLAT,
        "DOWNTREND": TREND_SHORT,
        "TRANSITION_UNKNOWN": FLAT,
    }
    exec_bars = _bars(8 * 4, start_ns=0, step_ns=H1 // 4)
    router = TargetRouter(mapping, regime_ts, persisted, H1)
    targets = router.build(exec_bars)
    invested = [t for t in targets if t in (MR_LONG, TREND_LONG)]
    assert invested, "router must emit a long target somewhere"
    # no string transition MR_LONG->TREND_LONG may appear back-to-back as a
    # change while direction stays +1: check no adjacent pair differs with
    # both directions equal +1
    for i in range(1, len(targets)):
        a, b = targets[i - 1], targets[i]
        if a is not None and b is not None:
            assert not (
                direction_of(a) == 1 and direction_of(b) == 1 and a != b
            ), f"no-op law violated at {i}: {a} -> {b}"
    assert router.report.noop_target_updates >= 1


def test_router_direction_change_emits_change():
    regime_ts = [i * H1 for i in range(6)]
    persisted = ["UPTREND"] * 3 + ["DOWNTREND"] * 3
    mapping = {
        "UPTREND": TREND_LONG,
        "DOWNTREND": TREND_SHORT,
        "ACCUMULATION": FLAT,
        "DISTRIBUTION": FLAT,
        "TRANSITION_UNKNOWN": FLAT,
    }
    exec_bars = _bars(6 * 4, start_ns=0, step_ns=H1 // 4)
    router = TargetRouter(mapping, regime_ts, persisted, H1)
    targets = router.build(exec_bars)
    kinds = {t for t in targets if t is not None}
    assert TREND_LONG in kinds and TREND_SHORT in kinds


def test_position_switch_counters():
    trades = [
        {"direction": 1},
        {"direction": 1},
        {"direction": -1},
        {"direction": 1},
    ]
    assert position_switches(trades) == 4
    assert reversal_count(trades) == 2


def test_v2_caps_frozen():
    assert v2_jev_only_trade_cap("BTC_H1") == 978
    assert v2_jev_only_trade_cap("BTC_H4") == 1060
    assert v2_jev_only_trade_cap("SPY_D1") == 343


# ---------------------------------------------------------------- selection


def _cand(sid, net, folds, cls="LONG_CAPABLE"):
    return SpecialistCandidate(sid, cls, net, folds)


def test_fold1_defaults_flat():
    # fid 0 == the law's fold 1 (empty inner) -> FLAT
    out = select_for_fold("UPTREND", 0, [_cand("S1", 100.0, {1: 100.0})], 0, 0, 0)
    assert out.selected == "FLAT" and out.reason == "fold1_empty_inner_default"


def test_fold2_proceeds_to_inner_law():
    # A7-R2 N1: fid 1 (the law's fold 2) HAS inner fold 0 — must NOT hit the
    # empty-inner default; with floors met and one candidate it selects it
    out = select_for_fold("UPTREND", 1, [_cand("S1", 100.0, {0: 100.0})], 10, 500, 1)
    assert out.selected == "S1" and out.reason == "single_eligible_specialist"


def test_inner_floor_failure_selects_flat():
    out = select_for_fold("DISTRIBUTION", 3, [_cand("S1", 100.0, {2: 100.0})], 3, 90, 2)
    assert out.selected == "FLAT" and out.reason == "inner_floor_failure"


def test_single_eligible_taken_when_floor_ok():
    out = select_for_fold("ACCUMULATION", 3, [_cand("S1", -50.0, {2: -50.0})], 8, 400, 2)
    assert out.selected == "S1" and out.reason == "single_eligible_specialist"


def test_higher_net_stable_two_inner_folds():
    a = _cand("S1", 100.0, {2: 60.0, 3: 40.0})
    b = _cand("S2", 50.0, {2: 30.0, 3: 20.0})
    out = select_for_fold("UPTREND", 4, [b, a], 10, 600, 2)
    assert out.selected == "S1" and out.reason == "inner_net_higher_stable"


def test_unstable_selects_flat():
    a = _cand("S1", 100.0, {2: -50.0, 3: 150.0})
    b = _cand("S2", 50.0, {2: 40.0, 3: 10.0})
    # S1 higher pooled but LOSES fold 2: with <=2 inner folds must win all
    out = select_for_fold("UPTREND", 4, [b, a], 10, 600, 2)
    assert out.selected == "FLAT" and out.reason == "inner_evidence_unstable"


def test_majority_rule_with_three_inner_folds():
    a = _cand("S1", 100.0, {2: -50.0, 3: 100.0, 4: 50.0})
    b = _cand("S2", 90.0, {2: 40.0, 3: 20.0, 4: 30.0})
    out = select_for_fold("UPTREND", 5, [b, a], 10, 600, 3)
    # S1 wins 2/3 folds and is higher pooled -> selected
    assert out.selected == "S1"


def test_exact_tie_tiebreak_flat_beats_short_beats_long():
    a = _cand("S_SHORT", 100.0, {2: 100.0}, cls="BTC_ONLY_SHORT")
    b = _cand("S_LONG", 100.0, {2: 100.0}, cls="LONG_CAPABLE")
    out = select_for_fold("DOWNTREND", 2, [b, a], 10, 600, 1)
    assert out.selected == "S_SHORT" and out.reason == "exact_tie_tiebreak"


def test_no_eligible_specialist_flat():
    out = select_for_fold("DISTRIBUTION", 3, [_cand("FLAT", 0.0, {})], 10, 600, 2)
    assert out.selected == "FLAT"
