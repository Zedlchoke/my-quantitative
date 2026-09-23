"""Census tests: determinism, margin-to-floor calculator, thin -> FLAT."""
import json

import numpy as np
import pandas as pd

import census as cen


def _synthetic_labels(n=5000, seed=3):
    rng = np.random.default_rng(seed)
    # blocks of phases with realistic-but-short lengths so every phase has
    # many episodes per fold
    phases = ["ACCUMULATION", "UPTREND", "DISTRIBUTION", "DOWNTREND"]
    out = []
    while len(out) < n:
        p = rng.choice(phases)
        out.extend([p] * int(rng.integers(24, 60)))
    return out[:n]


def test_margin_to_floor_calculator():
    m = cen.margin_to_floor(25, 20)
    assert m == {"value": 25.0, "floor": 20.0, "margin": 5.0, "pass": True}
    m = cen.margin_to_floor(19, 20)
    assert m["pass"] is False and m["margin"] == -1.0
    m = cen.margin_to_floor(20, 20)
    assert m["pass"] is True and m["margin"] == 0.0  # floor is >= (met exactly)


def test_census_determinism():
    labels = _synthetic_labels()
    opens = pd.date_range("2021-01-01", periods=len(labels), freq="h", tz="UTC")
    bounds = [
        (opens[0], opens[len(labels) // 2]),
        (opens[len(labels) // 2], opens[-1] + pd.Timedelta(hours=1)),
    ]
    a = cen.census_cell(labels, opens, bounds, cen.FLOORS if hasattr(cen, "FLOORS") else {
        "episodes_per_phase_per_cell_total": 20,
        "episodes_per_phase_per_fold": 3,
        "eligible_decisions_per_phase_per_fold": 100,
    })
    b = cen.census_cell(labels, opens, bounds, {
        "episodes_per_phase_per_cell_total": 20,
        "episodes_per_phase_per_fold": 3,
        "eligible_decisions_per_phase_per_fold": 100,
    })
    assert json.dumps(a, sort_keys=True, default=str) == json.dumps(
        b, sort_keys=True, default=str)


def test_census_partitions_and_identity():
    labels = _synthetic_labels(3000)
    opens = pd.date_range("2021-01-01", periods=len(labels), freq="h", tz="UTC")
    half = len(labels) // 2
    bounds = [(opens[0], opens[half]),
              (opens[half], opens[-1] + pd.Timedelta(hours=1))]
    c = cen.census_cell(labels, opens, bounds, {
        "episodes_per_phase_per_cell_total": 20,
        "episodes_per_phase_per_fold": 3,
        "eligible_decisions_per_phase_per_fold": 100,
    })
    total = sum(v["decisions_total"] for v in c["per_phase_cell_totals"].values())
    assert total == len(labels)  # decision counts partition the window exactly
    for fold, fd in c["per_fold"].items():
        bars = sum(fd[p]["bars"] for p in fd if isinstance(fd[p], dict)
                   and "bars" in fd[p] and p in
                   ["ACCUMULATION", "UPTREND", "DISTRIBUTION", "DOWNTREND",
                    "TRANSITION_UNKNOWN"])
        assert bars == fd["bars"]


def test_thin_phase_detection_and_flat_slot():
    labels = _synthetic_labels(6000)
    # make TRANSITION_UNKNOWN ultra-rare: exactly one short run
    labels[10:34] = ["TRANSITION_UNKNOWN"] * 24
    opens = pd.date_range("2021-01-01", periods=len(labels), freq="h", tz="UTC")
    third = len(labels) // 2
    bounds = [(opens[0], opens[third]),
              (opens[third], opens[-1] + pd.Timedelta(hours=1))]
    floors = {"episodes_per_phase_per_cell_total": 20,
              "episodes_per_phase_per_fold": 3,
              "eligible_decisions_per_phase_per_fold": 100}
    c = cen.census_cell(labels, opens, bounds, floors)
    assert "TRANSITION_UNKNOWN" in c["thin_phases"]
    assert "UPTREND" not in c["thin_phases"]
    assert "ACCUMULATION" not in c["thin_phases"]
    # slot law: thin => FLAT
    assert cen.slot_for_phase("TRANSITION_UNKNOWN", c["thin_phases"]) == \
        "FLAT (NOT_RUN_THIN_PHASE)"
    assert cen.slot_for_phase("UPTREND", c["thin_phases"]) is None
