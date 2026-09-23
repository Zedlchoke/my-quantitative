"""A3 census unit tests — synthetic timelines only (no PnL, no rebuilds in
the fast tests; one integration test re-derives the real census and
cross-checks it against A1's preliminary evidence file).

Covers: episode segmentation (incl. fold-boundary membership), eligible
filtering, margins, thin-regime verdicts, transitions per fold, and the
no-pooling guard (a census is a pure function of exactly one cell).
"""

from __future__ import annotations

import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from rsmv1.census import (  # noqa: E402
    ELIGIBLE_MIN_BARS,
    FLOOR_DECISIONS_FOLD,
    FLOOR_EPISODES_FOLD,
    FLOOR_EPISODES_TOTAL,
    NO_FOLD,
    PASS,
    THIN,
    census_cell_core,
    fold_index,
    iso_to_ns,
    nearest_rank_stats,
    run_census,
    segment_episodes,
)
from rsmv1.regime_timeline import episodes as reference_episodes  # noqa: E402

CYCLE_DIR = Path(__file__).resolve().parents[1]

ACC, UP, DIST, DOWN = (
    "ACCUMULATION",
    "UPTREND",
    "DISTRIBUTION",
    "DOWNTREND",
)


def _mk_stream(labels: list[str]) -> tuple[list[int], list[str], list[bool]]:
    """ts = bar index; switched = label change vs previous bar."""
    ts = list(range(len(labels)))
    switched = [False] + [
        labels[i] != labels[i - 1] for i in range(1, len(labels))
    ]
    return ts, list(labels), switched


# ---------------------------------------------------------------- segmentation

def test_segment_episodes_basic():
    eps = segment_episodes(["A", "A", "B", "B", "B", "A", "C", "C"])
    assert [(e["label"], e["start"], e["end"], e["length"]) for e in eps] == [
        ("A", 0, 1, 2),
        ("B", 2, 4, 3),
        ("A", 5, 5, 1),
        ("C", 6, 7, 2),
    ]


def test_segment_episodes_edges_and_single():
    assert segment_episodes([]) == []
    assert segment_episodes(["X"] * 5) == [
        {"label": "X", "start": 0, "end": 4, "length": 5}
    ]


def test_segment_episodes_matches_reference_implementation():
    rng = random.Random(20260923)
    for _ in range(50):
        stream = [rng.choice([ACC, UP, DIST, DOWN]) for _ in range(rng.randint(1, 80))]
        assert segment_episodes(stream) == reference_episodes(stream)


# ---------------------------------------------------------------- fold index

def test_fold_index_inclusive_spans_and_no_fold():
    spans = [(0, 99), (100, 199)]
    assert fold_index(0, spans) == 0
    assert fold_index(99, spans) == 0  # inclusive end
    assert fold_index(100, spans) == 1
    assert fold_index(199, spans) == 1
    assert fold_index(-1, spans) == NO_FOLD
    assert fold_index(200, spans) == NO_FOLD


def test_iso_to_ns_matches_freeze_convention():
    assert iso_to_ns("2025-08-28T04:00:00Z") == iso_to_ns(
        "2025-08-28T04:00:00+00:00"
    )
    assert iso_to_ns("2015-10-07") == iso_to_ns("2015-10-07T00:00:00Z")


# ---------------------------------------------------------------- stats

def test_nearest_rank_stats_convention():
    # frozen census convention: sorted[k], k = n//4, n//2, 3n//4
    lengths = list(range(1, 24))  # n=23 -> idx 5, 11, 17
    st = nearest_rank_stats(lengths)
    assert st == {"min": 1, "p25": 6, "median": 12, "p75": 18, "max": 23}
    assert nearest_rank_stats([]) == {
        "min": 0, "p25": 0, "median": 0, "p75": 0, "max": 0
    }
    assert nearest_rank_stats([7]) == {
        "min": 7, "p25": 7, "median": 7, "p75": 7, "max": 7
    }


# ---------------------------------------------------------------- core census

def _four_fold_spans(width: int) -> list[tuple[int, int]]:
    return [(i * width, (i + 1) * width - 1) for i in range(4)]


def test_eligible_filtering_and_counts():
    # short (ineligible) ACC episode followed by an eligible one
    labels = [ACC] * 3 + [UP] * 2 + [ACC] * 8 + [UP] * 5
    ts, persisted, switched = _mk_stream(labels)
    core = census_cell_core(
        "TEST_CELL", ts, persisted, switched, [(0, len(ts) - 1)]
    )
    acc = core["per_regime"][ACC]
    assert acc["episodes_total"] == 2
    assert acc["eligible_episodes_total"] == 1
    assert acc["eligible_decisions_total"] == 8
    assert acc["market_time_bars"] == 11
    assert acc["episode_lengths"]["min"] == 3
    assert acc["episode_lengths"]["max"] == 8
    assert acc["eligible_episode_lengths"]["min"] == 8
    f = acc["per_fold"]["0"]
    assert f["episodes"] == 2
    assert f["eligible_episodes"] == 1
    assert f["eligible_decisions"] == 8
    assert f["floor_decisions_ok"] is (8 >= FLOOR_DECISIONS_FOLD)


def test_fold_membership_uses_start_bar_with_straddle():
    # ACC episode from bar 95 to 110 straddles folds 0/1 (spans 0..99, 100..199)
    labels = [UP] * 95 + [ACC] * 16 + [UP] * 88
    ts, persisted, switched = _mk_stream(labels)
    core = census_cell_core("TEST_CELL", ts, persisted, switched, _four_fold_spans(100)[:2] + [(200, 299), (300, 399)])
    acc = core["per_regime"][ACC]
    assert acc["episodes_total"] == 1
    rec = acc["episodes"][0]
    assert rec["fold"] == 0  # START bar (95) is in fold 0
    assert rec["straddles_fold_boundary"] is True
    # ALL 16 bars count to the start fold (frozen rule) ...
    assert acc["per_fold"]["0"]["eligible_decisions"] == 16
    assert acc["per_fold"]["1"]["eligible_decisions"] == 0
    # ... while the physical split is 5 bars fold 0 / 11 bars fold 1
    assert acc["per_fold"]["0"]["bars_in_own_fold"] == 5
    assert acc["per_fold"]["1"]["bars_in_own_fold"] == 11


def test_transitions_total_and_per_fold():
    # switches at bar 50 (fold 0) and bar 100 (fold 1); bar 200 is in no fold
    labels = [ACC] * 50 + [UP] * 50 + [DOWN] * 100 + [DIST]
    ts, persisted, switched = _mk_stream(labels)
    core = census_cell_core("TEST_CELL", ts, persisted, switched, _four_fold_spans(100)[:2])
    assert core["transitions_total"] == 3
    assert core["transitions_per_fold"]["0"] == 1  # bar 50
    assert core["transitions_per_fold"]["1"] == 1  # bar 100
    assert core["transitions_per_fold"]["no_fold"] == 1  # bar 200
    assert sum(core["transitions_per_fold"].values()) == core["transitions_total"]


def test_margins_and_verdict_pass():
    # every fold: 7 ACC episodes x 20 bars + 7 UP episodes x 20 bars
    fold_labels = []
    for _ in range(7):
        fold_labels += [ACC] * 20 + [UP] * 20
    labels = fold_labels * 4
    ts, persisted, switched = _mk_stream(labels)
    core = census_cell_core("TEST_CELL", ts, persisted, switched, _four_fold_spans(280))
    for label in (ACC, UP):
        r = core["per_regime"][label]
        assert r["episodes_total"] == 28 >= FLOOR_EPISODES_TOTAL
        assert all(
            r["per_fold"][str(f)]["episodes"] >= FLOOR_EPISODES_FOLD
            for f in range(4)
        )
        assert all(
            r["per_fold"][str(f)]["eligible_decisions"] >= FLOOR_DECISIONS_FOLD
            for f in range(4)
        )
        assert r["verdict"] == PASS
        assert r["margin_to_floor_min"] >= 1.0
        mc = r["margin_components"]
        assert mc["episodes_total_over_floor"] == round(28 / 20, 3)
        assert mc["min_fold_episodes_over_floor"] == round(7 / 3, 3)
        assert mc["min_fold_eligible_decisions_over_floor"] == round(140 / 100, 3)
    # regimes with zero episodes are thin
    assert core["per_regime"][DIST]["verdict"] == THIN
    assert core["per_regime"][DIST]["margin_to_floor_min"] == 0.0


def test_verdict_thin_total_episodes():
    # per-fold floors pass but total episodes < 20
    fold_labels = []
    for _ in range(3):  # only 3 episodes per regime per fold -> 12 total < 20
        fold_labels += [ACC] * 40 + [UP] * 40
    labels = fold_labels * 4
    ts, persisted, switched = _mk_stream(labels)
    core = census_cell_core("TEST_CELL", ts, persisted, switched, _four_fold_spans(240))
    for label in (ACC, UP):
        r = core["per_regime"][label]
        assert r["episodes_total"] == 12 < FLOOR_EPISODES_TOTAL
        assert r["verdict"] == THIN
        assert r["margin_to_floor_min"] < 1.0


def test_unknown_episodes_reported_not_floored():
    # a TRANSITION_UNKNOWN run is segmented and reported separately; it
    # never enters the four phase regimes and never touches their verdicts
    labels = [ACC] * 6 + ["TRANSITION_UNKNOWN"] * 4 + [UP] * 8
    ts, persisted, switched = _mk_stream(labels)
    core = census_cell_core("TEST_CELL", ts, persisted, switched, [(0, len(ts) - 1)])
    unk = core["unselectable"]["TRANSITION_UNKNOWN"]
    assert (unk["bars"], unk["episodes"]) == (4, 1)
    assert unk["share"] == round(4 / 18, 4)
    assert "TRANSITION_UNKNOWN" not in core["per_regime"]
    assert core["episodes_total_all_labels"] == 3
    acc = core["per_regime"][ACC]
    assert acc["episodes_total"] == 1 and acc["eligible_episodes_total"] == 1


# ---------------------------------------------------------------- no-pooling

def test_no_pooling_guard_census_is_pure_per_cell():
    labels_a = [ACC] * 30 + [UP] * 30
    labels_b = [DOWN] * 10 + [DIST] * 40
    ts_a, p_a, s_a = _mk_stream(labels_a)
    ts_b, p_b, s_b = _mk_stream(labels_b)
    spans = [(0, 59)]
    core_a = census_cell_core("CELL_A", ts_a, p_a, s_a, spans)
    core_b = census_cell_core("CELL_B", ts_b, p_b, s_b, spans)
    # results are keyed strictly by their own cell
    assert core_a["cell"] == "CELL_A"
    assert core_b["cell"] == "CELL_B"
    # perturbing cell A's timeline leaves cell B's census byte-identical
    core_a_perturbed = census_cell_core(
        "CELL_A", ts_a, [ACC] * 60, s_a, spans
    )
    core_b_again = census_cell_core("CELL_B", ts_b, p_b, s_b, spans)
    import json as _json

    assert _json.dumps(core_b, sort_keys=True) == _json.dumps(
        core_b_again, sort_keys=True
    )
    assert core_a_perturbed["per_regime"][UP]["episodes_total"] == 0  # merged away
    assert core_a["per_regime"][UP]["episodes_total"] == 1  # unchanged by A'


# ---------------------------------------------------------------- integration

def test_full_census_real_cells_matches_a1_preliminary_and_no_pooling():
    """Expensive (~10 s): re-derive the real census for all three cells and
    cross-check against A1's preliminary evidence. A1 headline: BTC_H1
    ACC/UP/DIST/DOWN episodes 23/28/5/34; BTC_H4 4/12/1/14; SPY 1/17/1/15;
    transitions 90/31/34."""
    bundle = run_census(CYCLE_DIR, out_dir=None)  # no artifact writes in tests
    assert set(bundle["cells"].keys()) == {"BTC_H1", "BTC_H4", "SPY_D1"}
    expected_eps = {
        "BTC_H1": [23, 28, 5, 34],
        "BTC_H4": [4, 12, 1, 14],
        "SPY_D1": [1, 17, 1, 15],
    }
    expected_sw = {"BTC_H1": 90, "BTC_H4": 31, "SPY_D1": 34}
    from rsmv1.census import PHASES  # noqa: E402

    for cell, c in bundle["cells"].items():
        got = [c["per_regime"][p]["episodes_total"] for p in PHASES]
        assert got == expected_eps[cell], (cell, got)
        assert c["transitions_total"] == expected_sw[cell]
        assert c["timeline_rebuild"]["verified_against_v2"] is True
        assert (
            c["timeline_rebuild"]["vs_a1_saved_runtime_rows"]["status"]
            == "MATCH"
        )
        cc = c["cross_check_vs_a1_preliminary"]
        assert cc["fields_compared"] > 0
        # any diff must be an explicit, explained record — never silent
        for d in cc["diffs"]:
            assert {"field", "a1_preliminary", "census", "note"} <= set(d)
