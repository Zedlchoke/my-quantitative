"""Census determinism, margin calculator, thin-phase -> FLAT law."""

import json
from pathlib import Path

import pytest

from psv1_spy.census import (
    episodes,
    fold_census,
    floor_margins,
    margin,
)
from psv1_spy.phase_rule import (
    ACCUMULATION,
    DISTRIBUTION,
    DOWNTREND,
    RuleParams,
    UNKNOWN,
    UPTREND,
    compute_labels,
    sensitivity_table,
)
from psv1_spy.snapshot import SNAPSHOT_PATH, load_sessions

P = RuleParams()

SNAPSHOT_EXISTS = Path(SNAPSHOT_PATH).exists()
requires_snapshot = pytest.mark.skipif(
    not SNAPSHOT_EXISTS, reason="frozen SPY snapshot not present"
)


# ------------------------------------------------------------ margin units
def test_margin_calculator_hand_fixtures():
    assert margin(23, 20) == {"value": 23, "floor": 20, "margin": 3, "pass": True}
    assert margin(20, 20)["pass"] is True
    assert margin(19, 20) == {"value": 19, "floor": 20, "margin": -1, "pass": False}
    assert margin(2, 3)["margin"] == -1 and margin(2, 3)["pass"] is False
    assert margin(100, 100)["pass"] is True and margin(100, 100)["margin"] == 0
    assert margin(99, 100)["pass"] is False


def test_episodes_run_splitting():
    assert episodes([0, 1, 1, 0, 0, 1, 0]) == [2, 1]
    assert episodes([]) == []
    assert episodes([1, 1, 1]) == [3]
    assert episodes([0, 0]) == []


def _synthetic_census():
    # 300 sessions, all UPTREND, one fold => 1 episode, 300 decisions
    labels = [UPTREND] * 300
    return fold_census(labels, [("FA", "ERA-X", 0, 299)])


def test_thin_phase_becomes_not_run_thin():
    cen = _synthetic_census()
    floors = floor_margins(cen)
    assert floors["phases"][UPTREND]["episodes_cell_total"]["value"] == 1
    assert floors["phases"][UPTREND]["floors_met"] is False
    assert (
        floors["phases"][UPTREND]["verdict_if_floors_failed"] == "NOT_RUN_THIN_PHASE"
    )
    for p in (ACCUMULATION, DISTRIBUTION, DOWNTREND):
        assert floors["phases"][p]["verdict_if_floors_failed"] == "NOT_RUN_THIN_PHASE"


def test_census_statistics_hand_fixture():
    # hand-checked census over a tiny stream: UP,UP,UNK,DOWN,DOWN,DOWN,UP,UNK,UNK
    labels = [UPTREND, UPTREND, UNKNOWN, DOWNTREND, DOWNTREND, DOWNTREND, UPTREND,
              UNKNOWN, UNKNOWN]
    cen = fold_census(labels, [("FA", "ERA-X", 0, 8)])
    ph = cen["per_fold"][0]["phases"]
    assert ph[UPTREND]["occupancy_sessions"] == 3
    assert ph[UPTREND]["episode_count_fold_local"] == 2  # [0..1] and [6]
    assert ph[DOWNTREND]["episode_count_fold_local"] == 1
    assert ph[DOWNTREND]["dwell"]["min"] == 3 and ph[DOWNTREND]["dwell"]["max"] == 3
    assert cen["per_fold"][0]["unknown"]["longest_run"] == 2
    assert cen["per_fold"][0]["transitions_total"] == 4  # UP->UNK, UNK->DOWN, DOWN->UP, UP->UNK
    tm = cen["per_fold"][0]["transition_matrix"]
    assert tm[UPTREND][UNKNOWN] == 2
    assert tm[UNKNOWN][DOWNTREND] == 1
    assert tm[DOWNTREND][UPTREND] == 1


@requires_snapshot
def test_census_determinism_and_committed_artifact_match():
    sessions = load_sessions()
    closes = [s.adjusted_close for s in sessions]
    labels = compute_labels(closes, P)
    warm = P.warmup
    post = labels[warm:]
    folds = [("F1", "ERA-S1", 0, 786), ("F2", "ERA-S2", 787, 1291),
             ("F3", "ERA-S3", 1292, 1794), ("F4", "ERA-S4", 1795, len(post) - 1)]
    cen1 = fold_census(post, folds)
    cen2 = fold_census(post, folds)
    b1 = json.dumps(cen1, sort_keys=True)
    b2 = json.dumps(cen2, sort_keys=True)
    assert b1 == b2  # determinism

    committed = json.loads(
        (Path(__file__).resolve().parents[1] / "census" / "census.json").read_text()
    )
    assert committed["census"] == cen1
    assert committed["floor_margins"] == floor_margins(cen1)
    assert (
        committed["sensitivity_table"]["notches"]
        == sensitivity_table(closes)
    )


@requires_snapshot
def test_committed_census_headlines():
    committed = json.loads(
        (Path(__file__).resolve().parents[1] / "census" / "census.json").read_text()
    )
    floors = committed["floor_margins"]["phases"]
    assert committed["post_warmup_sessions"] == 2724
    assert floors[UPTREND]["floors_met"] is True
    for p in (ACCUMULATION, DISTRIBUTION, DOWNTREND):
        assert floors[p]["floors_met"] is False
    gate = committed["calendar_defect_gate"]["gate_10_3a_weekday_rotation_replay"]
    assert gate["pass"] is True
