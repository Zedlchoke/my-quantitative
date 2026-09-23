"""Census golden tests (plan §14): determinism, hand-computed counts,
margin-to-floor calculator, thin-phase -> FLAT verdict."""

import numpy as np
import pandas as pd
import pytest

from research.control.phase_strategy_v1.lane_btc_h4.pipeline import config
from research.control.phase_strategy_v1.lane_btc_h4.pipeline.census import (
    era_fold_assignment, episodes, census_for_labels, dwell_stats)
from research.control.phase_strategy_v1.lane_btc_h4.pipeline.phase_rule import UNKNOWN

UP, DOWN = "UPTREND", "DOWNTREND"


def _assign_12():
    ms = np.arange(12, dtype="int64") * config.H4_MS
    a = era_fold_assignment(pd.Series(ms), int(ms[-1]) + config.H4_MS - 1, warmup=0)
    a["fold"] = ["F1"] * 6 + ["F2"] * 6
    a["era"] = a["fold"].map({"F1": "ERA-B1", "F2": "ERA-B2"})
    return a


def test_episodes_maximal_contiguous_runs():
    mask = np.array([True, True, False, True, True, True, False, False, True])
    assert episodes(mask) == [(0, 1), (3, 5), (8, 8)]


def test_census_hand_computed():
    labels = pd.Series([UP, UP, UP, UNKNOWN, UP, UP,
                        DOWN, DOWN, UNKNOWN, UNKNOWN, DOWN, DOWN])
    a = _assign_12()
    c = census_for_labels(labels, a)
    up_f1 = c["per_phase_era_fold"][f"{UP}|F1"]
    assert up_f1["episodes"] == 2            # runs (0-2) and (4-5)
    assert up_f1["occupancy_bars"] == 5
    assert up_f1["margin_episodes_fold"] == -1   # 2 vs floor 3
    assert up_f1["margin_decisions_fold"] == -95  # 5 vs floor 100
    assert up_f1["floor_met_fold"] is False
    down_f2 = c["per_phase_era_fold"][f"{DOWN}|F2"]
    assert down_f2["episodes"] == 2          # (6-7) and (10-11)
    assert down_f2["occupancy_bars"] == 4
    unk_f1 = c["per_phase_era_fold"][f"{UNKNOWN}|F1"]
    assert unk_f1["occupancy_bars"] == 1
    assert unk_f1["longest_unknown_run_in_fold"] == 1
    assert unk_f1["unknown_share_of_fold"] == pytest.approx(1 / 6)
    # thin verdict propagates: UP cell episodes = 2 < 20 -> NOT_RUN_THIN_PHASE
    assert c["per_phase_summary"][UP]["verdict"] == "NOT_RUN_THIN_PHASE"
    assert c["per_phase_summary"][UP]["margin_episodes_cell"] == -18


def test_census_determinism():
    labels = pd.Series([UP, UP, UP, UNKNOWN, UP, UP,
                        DOWN, DOWN, UNKNOWN, UNKNOWN, DOWN, DOWN])
    a = _assign_12()
    c1 = census_for_labels(labels, a)
    c2 = census_for_labels(labels, a)
    assert c1 == c2


def test_dwell_stats_hand_computed():
    assert dwell_stats([3, 2, 3])["min"] == 2
    assert dwell_stats([3, 2, 3])["median"] == 3.0
    assert dwell_stats([3, 2, 3])["max"] == 3
    assert dwell_stats([])["n"] == 0


def test_floor_constants_immutable():
    assert config.FLOOR_EPISODES_CELL == 20
    assert config.FLOOR_EPISODES_FOLD == 3
    assert config.FLOOR_DECISIONS_FOLD == 100


def test_era_fold_assignment_boundaries():
    # ERA-B1 ends 2021-04-30; bucket at 2021-05-01T00:00Z must be ERA-B2/F2
    ms_b1 = int(pd.Timestamp("2021-04-30T20:00:00Z").timestamp() * 1000)
    ms_b2 = int(pd.Timestamp("2021-05-01T00:00:00Z").timestamp() * 1000)
    ms = pd.Series([ms_b1, ms_b2])
    a = era_fold_assignment(ms, int(ms_b2) + config.H4_MS - 1, warmup=0)
    assert a["era"].iloc[0] == "ERA-B1" and a["fold"].iloc[0] == "F1"
    assert a["era"].iloc[1] == "ERA-B2" and a["fold"].iloc[1] == "F2"


def test_warmup_bars_excluded_from_census():
    ms = pd.Series(np.arange(10, dtype="int64") * config.H4_MS)
    a = era_fold_assignment(ms, int(ms.iloc[-1]), warmup=10)
    assert not a["post_warmup"].any()
    assert a["fold"].isna().all()
