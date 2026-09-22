"""H1 resample correctness on synthetic 15m grids; snap convention; census."""

from __future__ import annotations

import numpy as np
import pytest

from conftest import make_exec_grid
from jrv1.data import (
    HOUR,
    MIN15,
    Bars,
    CensusViolation,
    census_check,
    h1_resample,
    snap_close_ns,
)

BOUNDARY = 1_699_999_200_000_000_000  # 2023-11-14T22:00:00Z, clean hour + 15m boundary


def _bar(m, o, h, l, c, v=1.0):
    return (m, o, h, l, c, v)


def test_snap_convention():
    # clean boundary stays
    ts = np.array([BOUNDARY], dtype=np.int64)
    assert snap_close_ns(ts)[0] == BOUNDARY
    # stamped ~1ms early snaps UP to next boundary
    early = BOUNDARY + MIN15 - 999_936
    assert snap_close_ns(np.array([early], dtype=np.int64))[0] == BOUNDARY + MIN15
    # stamped ~1us early also snaps
    early2 = BOUNDARY + MIN15 - 1000
    assert snap_close_ns(np.array([early2], dtype=np.int64))[0] == BOUNDARY + MIN15
    # offset beyond 1ms tolerance -> hard fail
    bad = BOUNDARY + MIN15 - 5_000_000
    with pytest.raises(CensusViolation):
        snap_close_ns(np.array([bad], dtype=np.int64))


def test_h1_resample_complete_hours():
    # two complete hours: 4 bars each, minute offsets 0/15/30/45
    rows = []
    px = 100.0
    for m in (0, 15, 30, 45, 60, 75, 90, 105):
        px += 1.0
        rows.append(_bar(m, px, px + 1, px - 1, px, 2.0))
    bars = make_exec_grid(rows, start_ts=BOUNDARY)
    h1, census = h1_resample(bars)
    assert census["rows"] == 8
    assert census["complete_hours"] == 2
    assert census["gap_15m_interior"] == 0
    assert census["partial_hours"] == []
    assert len(h1.ts_close) == 2
    # H1 open = first open, close = last close, extremes, volume sum
    assert h1.ts_open[0] == BOUNDARY
    assert h1.ts_close[0] == BOUNDARY + HOUR
    assert h1.open[0] == pytest.approx(101.0)
    assert h1.close[0] == pytest.approx(104.0)
    assert h1.high[0] == pytest.approx(105.0)
    assert h1.low[0] == pytest.approx(100.0)
    assert h1.volume[0] == pytest.approx(8.0)
    assert h1.ts_close[1] == BOUNDARY + 2 * HOUR


def test_h1_partial_hour_reported_and_excluded():
    # hour 1 complete, hour 2 has only 3 bars (partial), hour 3 complete
    rows = []
    px = 100.0
    for m in (0, 15, 30, 45, 60, 75, 90, 105, 120, 135, 150):
        px += 1.0
        rows.append(_bar(m, px, px + 1, px - 1, px, 1.0))
    bars = make_exec_grid(rows, start_ts=BOUNDARY)
    h1, census = h1_resample(bars)
    assert census["complete_hours"] == 2
    assert census["partial_hours"] == [
        {"hour_start": "2023-11-15T00:00:00Z", "bars": 3}
    ]
    assert len(h1.ts_close) == 2  # partial hour excluded from regime bars


def test_interior_gap_is_fatal():
    # skip the 15m slot at minute 15 -> interior gap
    rows = [_bar(0, 100, 101, 99, 100), _bar(30, 100, 101, 99, 100)]
    bars = make_exec_grid(rows, start_ts=BOUNDARY)
    with pytest.raises(CensusViolation):
        h1_resample(bars)


def test_census_check_against_freeze_shape():
    rows = []
    px = 100.0
    for m in (0, 15, 30, 45):
        px += 1.0
        rows.append(_bar(m, px, px + 1, px - 1, px, 1.0))
    bars = make_exec_grid(rows, start_ts=BOUNDARY)
    _, census = h1_resample(bars)
    freeze_entry = {
        "rows": 4,
        "first_bar_close_utc": census["first_bar_close_utc"],
        "last_bar_close_utc": census["last_bar_close_utc"],
        "h1_census": {
            "complete_hours": 1,
            "gap_15m_interior": 0,
            "first_complete_close": census["first_complete_close"],
            "last_complete_close": census["last_complete_close"],
            "partial_hours": [],
        },
    }
    assert census_check(census, freeze_entry)["ok"] is True
    freeze_entry["h1_census"]["complete_hours"] = 2
    with pytest.raises(CensusViolation):
        census_check(census, freeze_entry)


def test_snap_preserves_hour_bucket():
    # a bar stamped 1ms before the :45 boundary still snaps into the same hour
    rows = []
    px = 100.0
    for m in (0, 15, 30, 45):
        px += 1.0
        rows.append(_bar(m, px, px + 1, px - 1, px, 1.0))
    bars = make_exec_grid(rows, start_ts=BOUNDARY)
    ts_raw = bars.ts_close.copy()
    ts_raw[-1] = ts_raw[-1] - 999_936  # stamped just before the :60 boundary
    snapped = snap_close_ns(ts_raw)
    assert snapped[-1] == BOUNDARY + 60 * 60 * 1_000_000_000
    # the bar's OPEN (= snapped - 15m) is at :45 -> same hour as the first bar
    assert (snapped[-1] - MIN15) // HOUR == (snapped[0] - MIN15) // HOUR
