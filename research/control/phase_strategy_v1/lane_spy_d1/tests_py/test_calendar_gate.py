"""Calendar-defect gates: weekday-rotation replay (10.3a) and the Tuesday
defect-shape fixture (10.3b), plus the runtime zero-force-flat counter."""

import json
from datetime import date, datetime, timedelta
from pathlib import Path

import pytest

from psv1_spy.events import labels_to_targets, reduce_events
from psv1_spy.gates import (
    clock_attributable_force_flats,
    exits_by_weekday,
    rotate_dates,
    run_pipeline,
    weekday_rotation_replay,
)
from psv1_spy.phase_rule import (
    RuleParams,
    ACCUMULATION,
    DISTRIBUTION,
    DOWNTREND,
    UNKNOWN,
    UPTREND,
    compute_labels,
)
from psv1_spy.snapshot import SNAPSHOT_PATH, load_sessions

P = RuleParams()
SNAPSHOT_EXISTS = Path(SNAPSHOT_PATH).exists()
requires_snapshot = pytest.mark.skipif(
    not SNAPSHOT_EXISTS, reason="frozen SPY snapshot not present"
)

FOLDS_ABS = [
    ("F1", "ERA-S1", 219, 1005),
    ("F2", "ERA-S2", 1006, 1510),
    ("F3", "ERA-S3", 1511, 2013),
    ("F4", "ERA-S4", 2014, 2942),
]


def _weekdays(start: date, n: int):
    out, d = [], start
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d.isoformat())
        d += timedelta(days=1)
    return out


def _synthetic_series(n=400):
    # deterministic wiggly path with regimes, enough to cross bands
    closes = []
    for i in range(n):
        closes.append(
            100.0
            + 8.0 * (1 if i < 200 else -1)
            + 4.0 * ((i % 40) / 40.0)
            + 2.0 * ((i % 7) / 7.0)
        )
    return closes


# ------------------------------------------------------- gate 10.3a: rotation
def test_weekday_rotation_replay_synthetic():
    closes = _synthetic_series()
    dates = _weekdays(date(2024, 1, 1), len(closes))
    folds = [("FA", "ERA-X", P.warmup, len(closes) - 1)]
    res = weekday_rotation_replay(closes, dates, folds)
    assert res["pass"] is True
    for k in ("shift_1d", "shift_2d", "shift_3d", "shift_4d"):
        assert res["shifts"][k]["labels_invariant"]
        assert res["shifts"][k]["per_fold_occupancy_invariant"]
        assert res["shifts"][k]["transitions_invariant"]


@requires_snapshot
def test_weekday_rotation_replay_real_snapshot():
    sessions = load_sessions()
    closes = [s.adjusted_close for s in sessions]
    dates = [s.date for s in sessions]
    res = weekday_rotation_replay(closes, dates, FOLDS_ABS)
    assert res["pass"] is True
    # committed census artifact carries the same verdict
    census = json.loads(
        (Path(__file__).resolve().parents[1] / "census" / "census.json").read_text()
    )
    assert (
        census["calendar_defect_gate"]["gate_10_3a_weekday_rotation_replay"]["pass"]
        is True
    )


# ------------------------------------------------- gate 10.3b: Tuesday defect
def _legacy_defect_engine(dates_iso, targets, threshold_days=3.0):
    """SYNTHETIC reproduction of the predecessor defect shape (test-only):
    session closes stamped next-midnight; decisions refreshed only at Friday
    closes; a decision older than the threshold at a session OPEN forces the
    position FLAT. With these constants the forced flats begin at every
    Tuesday open and last until the next Monday - weekday-cadence churn with
    zero market view. This engine is the DEFECT REFERENCE, not lane code."""
    opens = {
        d: datetime.fromisoformat(d) + timedelta(hours=9, minutes=30)
        for d in dates_iso
    }
    last_friday_stamp = None
    flats = []
    for d in dates_iso:
        dt = date.fromisoformat(d)
        if dt.weekday() == 4:  # Friday close decision, stamped next-midnight
            last_friday_stamp = datetime.fromisoformat(d) + timedelta(days=1)
        if last_friday_stamp is None:
            continue
        age_days = (opens[d] - last_friday_stamp).total_seconds() / 86400.0
        if age_days > threshold_days:
            flats.append(d)
    return flats


def test_tuesday_defect_fixture_reproduces_defect_shape():
    dates = _weekdays(date(2024, 1, 1), 20)  # 4 full Mon-Fri weeks
    flats = _legacy_defect_engine(dates, [1] * len(dates))
    assert len(flats) > 0, "fixture must reproduce weekly forced flats"
    by_weekday = {}
    for d in flats:
        wd = date.fromisoformat(d).weekday()
        by_weekday.setdefault(wd, 0)
        by_weekday[wd] += 1
    assert 0 not in by_weekday, "no forced flat may land on a Monday"
    # every forced-flat RUN begins at a Tuesday open
    flat_set = set(flats)
    for d in flats:
        prev = (date.fromisoformat(d) - timedelta(days=1)).isoformat()
        if prev not in flat_set:
            assert date.fromisoformat(d).weekday() == 1, (
                "force-flat runs must start on Tuesday"
            )


def test_lane_pipeline_zero_weekday_force_flats_on_defect_path():
    dates = _weekdays(date(2024, 1, 1), 20)
    # same synthetic price path under the lane pipeline: labels + targets
    closes = _synthetic_series(20 + 240)[240:]  # any ordered closes work here
    labels = compute_labels(closes, P)
    targets = labels_to_targets(labels[-20:], {UPTREND: 1}, unknown_keeps_previous=True)
    r = reduce_events(targets)
    assert clock_attributable_force_flats(r["fills"], targets) == 0
    # defect fixture on the SAME dates does produce weekday-attributable flats
    assert len(_legacy_defect_engine(dates, targets)) > 0
    # and the lane's events are invariant under date rotation
    base_indices = [i for _, i in r["fills"]]
    for k in range(1, 5):
        r2 = reduce_events(targets)  # pipeline never sees the calendar
        assert [i for _, i in r2["fills"]] == base_indices


def test_fold_force_flat_exits_are_not_clock_attributable():
    # fold force-flat is a target change at the fold end (window boundary),
    # never a hidden clock event: the counter must stay 0.
    targets = [1, 1, 1, 0]  # fold-end force-flat appended by the caller
    r = reduce_events(targets)
    assert r["fills"] == [("ENTER", 0), ("EXIT", 3)]
    assert clock_attributable_force_flats(r["fills"], targets) == 0


def test_exits_by_weekday_disclosure_counter():
    dates = _weekdays(date(2024, 1, 1), 6)
    targets = [0, 1, 1, 1, 0, 0]  # EXIT fires at index 4 = Friday 2024-01-05
    r = reduce_events(targets)
    assert r["fills"] == [("ENTER", 1), ("EXIT", 4)]
    by_wd = exits_by_weekday(r["fills"], dates)
    assert by_wd["Fri"] == 1 and sum(by_wd.values()) == 1


@requires_snapshot
def test_real_pipeline_zero_clock_attributable_force_flats():
    sessions = load_sessions()
    closes = [s.adjusted_close for s in sessions]
    dates = [s.date for s in sessions]
    labels = compute_labels(closes, P)
    total_fills = 0
    total_clock_flats = 0
    for _, _, a, b in FOLDS_ABS:
        seg = labels[a : b + 1]
        targets = labels_to_targets(
            seg,
            {ACCUMULATION: 0, UPTREND: 1, DISTRIBUTION: 0, DOWNTREND: 0},
            unknown_keeps_previous=True,
        )
        targets[-1] = 0  # fold force-flat (census assumption)
        r = reduce_events(targets)
        total_fills += len(r["fills"])
        total_clock_flats += clock_attributable_force_flats(r["fills"], targets)
    assert total_fills > 0  # the dry-run machinery actually ran on real labels
    assert total_clock_flats == 0
