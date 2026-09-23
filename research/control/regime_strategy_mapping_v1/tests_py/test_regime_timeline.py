"""Smoke tests: regime-timeline rebuild determinism + V2 verification.

The rebuild path is the cycle's core input law (zero provider calls). These
tests re-derive the timeline for a small slice and assert the verification
constants + episode logic on synthetic streams. Full-cell rebuilds are run
by tools/ (they take ~3 s per cell) and their outputs land in runtime/.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from rsmv1.regime_timeline import (  # noqa: E402
    V2_EXPECTED,
    episodes,
)


def test_v2_expected_constants_frozen():
    assert V2_EXPECTED["BTC_H1"]["switches"] == 90
    assert V2_EXPECTED["BTC_H4"]["switches"] == 31
    assert V2_EXPECTED["SPY_D1"]["switches"] == 34
    assert V2_EXPECTED["BTC_H1"]["n_decisions"] == 8567
    assert V2_EXPECTED["BTC_H4"]["n_decisions"] == 1997
    assert V2_EXPECTED["SPY_D1"]["n_decisions"] == 2751


def test_episodes_synthetic():
    stream = ["A", "A", "B", "B", "B", "A", "C", "C"]
    eps = episodes(stream)
    assert [(e["label"], e["start"], e["end"], e["length"]) for e in eps] == [
        ("A", 0, 1, 2),
        ("B", 2, 4, 3),
        ("A", 5, 5, 1),
        ("C", 6, 7, 2),
    ]


def test_episodes_empty_and_single():
    assert episodes([]) == []
    assert episodes(["X"] * 5) == [
        {"label": "X", "start": 0, "end": 4, "length": 5}
    ]


def test_full_rebuild_all_cells_verifies():
    """The expensive check, still fast enough (~4 s total): every cell's
    rebuild must pass its V2 verification or raise RegimeTimelineMismatch."""
    from rsmv1.regime_timeline import rebuild_cell_timeline

    cycle_dir = Path(__file__).resolve().parents[1]
    for cell in ("BTC_H1", "BTC_H4", "SPY_D1"):
        ct = rebuild_cell_timeline(cycle_dir, cell)
        assert ct.stats["switches"] == V2_EXPECTED[cell]["switches"]
        assert ct.stats["n_decisions"] == V2_EXPECTED[cell]["n_decisions"]


def test_rebuild_is_deterministic():
    from rsmv1.regime_timeline import rebuild_cell_timeline

    cycle_dir = Path(__file__).resolve().parents[1]
    a = rebuild_cell_timeline(cycle_dir, "SPY_D1")
    b = rebuild_cell_timeline(cycle_dir, "SPY_D1")
    assert a.persisted == b.persisted
    assert a.effective == b.effective
