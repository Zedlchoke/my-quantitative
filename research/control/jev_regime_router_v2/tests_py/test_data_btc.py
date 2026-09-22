"""Data laws: snap convention, H1/H4 resample + census on synthetic grids,
SPY identity from the v2 data_local copy."""

from __future__ import annotations

import datetime as dt

import numpy as np
import pytest

from conftest import make_bars
from jrv2.data import (
    DAY,
    H4,
    HOUR,
    MIN15,
    Bars,
    CensusViolation,
    DataBlocked,
    h1_resample,
    h4_resample,
    load_spy,
    snap_close_ns,
    spy_local_path,
)


def _exec_grid_15m(opens_ns, closes, volumes=None):
    n = len(opens_ns)
    o = np.asarray(closes, dtype=np.float64)
    v = np.ones(n) if volumes is None else np.asarray(volumes, dtype=np.float64)
    return Bars(
        ts_open=np.asarray(opens_ns, dtype=np.int64),
        ts_close=np.asarray(opens_ns, dtype=np.int64) + MIN15,
        open=o,
        high=o + 1.0,
        low=o - 1.0,
        close=o,
        volume=v,
    )


def _day_start(y, mo, d, h=0, mi=0):
    return int(dt.datetime(y, mo, d, h, mi, tzinfo=dt.timezone.utc).timestamp() * 10**9)


def test_snap_close_up_to_boundary():
    M15 = MIN15
    early = _day_start(2026, 1, 2, 0, 45) - 999_936  # 00:44:59.999000964
    on_boundary = _day_start(2026, 1, 2, 0, 45)
    snapped = snap_close_ns(np.array([early, on_boundary], dtype=np.int64))
    assert snapped[0] == _day_start(2026, 1, 2, 0, 45)  # snapped UP
    assert snapped[1] == on_boundary  # already on boundary
    # beyond the 1ms tolerance is fatal
    bad = _day_start(2026, 1, 2, 0, 45) - 2_000_000  # >1ms before the boundary
    with pytest.raises(CensusViolation, match="snap convention"):
        snap_close_ns(np.array([bad], dtype=np.int64))


def test_h1_resample_synthetic_grid():
    """A clean 10-hour 15m grid -> 10 complete hours; a truncated hour is partial."""
    base = _day_start(2026, 1, 2)
    opens = [base + i * MIN15 for i in range(10 * 4)]
    bars = _exec_grid_15m(opens, [100.0 + i for i in range(40)])
    h1, census = h1_resample(bars)
    assert census["complete"] == 10
    assert census["interior_gaps"] == 0
    assert census["partial"] == []
    assert len(h1.ts_close) == 10
    assert h1.ts_close[0] == base + HOUR
    # aggregation: close of hour = close of its last 15m bar
    assert float(h1.close[0]) == 103.0
    assert float(h1.high[0]) == 104.0
    assert float(h1.volume[0]) == 4.0


def test_h4_resample_synthetic_grid():
    """16 aligned 15m bars per H4 bucket (UTC 00/04/08/12/16/20)."""
    base = _day_start(2026, 1, 2)
    opens = [base + i * MIN15 for i in range(3 * 16)]
    closes = [100.0 + i for i in range(3 * 16)]
    bars = _exec_grid_15m(opens, closes)
    h4, census = h4_resample(bars)
    assert census["complete"] == 3
    assert census["interior_gaps"] == 0
    assert len(h4.ts_close) == 3
    # bucket closes land on UTC 04:00 / 08:00 / 12:00
    for k in range(3):
        assert h4.ts_close[k] == base + (k + 1) * H4
    assert float(h4.close[0]) == 115.0  # last 15m close of bucket 0
    assert float(h4.open[0]) == 100.0
    assert float(h4.high[0]) == 116.0
    assert float(h4.volume[0]) == 16.0


def test_h4_partial_bucket_not_complete():
    """A trailing bucket with only 5 bars (capture edge, gapless grid) is
    partial and excluded from the regime bars."""
    base = _day_start(2026, 1, 2)
    # 16 bars complete the 00:00-04:00 bucket; 5 more (gapless) trail in 04:00
    opens = [base + i * MIN15 for i in range(21)]
    bars = _exec_grid_15m(opens, [100.0] * 21)
    h4, census = h4_resample(bars)
    assert census["complete"] == 1
    assert census["partial"] == [{"bucket_start": "2026-01-02T04:00:00Z", "bars": 5}]
    assert census["interior_gaps"] == 0
    assert len(h4.ts_close) == 1


def test_h4_interior_gap_is_fatal():
    base = _day_start(2026, 1, 2)
    opens = [base + i * MIN15 for i in range(21) if i != 10]  # bar idx 10 missing
    bars = _exec_grid_15m(opens, [100.0] * 20)
    with pytest.raises(CensusViolation, match="15m gaps"):
        h4_resample(bars)


def test_h4_bucket_alignment_utc_4h_boundaries():
    """Buckets are wall-clock 4h (00/04/08/12/16/20) even when data starts mid-bucket."""
    base = _day_start(2026, 1, 2, 1, 0)  # starts 01:00 inside the 00:00 bucket
    # 12 bars complete the partial 00:00 bucket; 16 + 16 fill 04:00 and 08:00
    opens = [base + i * MIN15 for i in range(44)]
    bars = _exec_grid_15m(opens, [100.0] * 44)
    h4, census = h4_resample(bars)
    assert census["complete"] == 2
    assert census["partial"] == [{"bucket_start": "2026-01-02T00:00:00Z", "bars": 12}]
    # the partial 00:00 bucket is excluded; first complete bucket closes 08:00
    assert h4.ts_close[0] == _day_start(2026, 1, 2, 8, 0)
    assert h4.ts_close[1] == _day_start(2026, 1, 2, 12, 0)


def test_btc_real_data_census_matches_freeze(fz):
    """THE census: BTC parquet re-run equals the freeze (H1 8759 / H4 2189,
    partial buckets exact)."""
    from jrv2.data import load_btcusdt

    exec_bars, h1, h4, census = load_btcusdt(fz, verify_census=True)
    assert census["rows"] == 35039
    assert census["h1"]["complete"] == 8759
    assert census["h4"]["complete"] == 2189
    assert census["h1"]["partial"] == [
        {"bucket_start": "2025-08-20T02:00:00Z", "bars": 1},
        {"bucket_start": "2026-08-20T02:00:00Z", "bars": 2},
    ]
    assert census["h4"]["partial"] == [
        {"bucket_start": "2025-08-20T00:00:00Z", "bars": 5},
        {"bucket_start": "2026-08-20T00:00:00Z", "bars": 10},
    ]
    # H4 bars are exactly the H1-hours-aligned wall-clock buckets
    assert int(h4.ts_close[0]) % H4 == 0
    assert int(h1.ts_close[0]) % HOUR == 0


def test_spy_loads_from_v2_data_local_copy(fz):
    """SPY loads from the V2 data_local copy of the frozen snapshot (same
    bytes as the freeze digest); the V1 worktree path is never opened."""
    bars, dates, checks = load_spy(fz)
    assert checks["ok"] is True
    assert checks["checks"]["records"] == 2943
    assert checks["checks"]["first_session"] == "2015-01-02"
    assert checks["checks"]["last_session"] == "2026-09-16"
    assert spy_local_path(fz).exists()
    assert "data_local" in str(spy_local_path(fz))
    assert "jev_regime_router_v1" not in str(spy_local_path(fz))


def test_load_cell_abstraction(fz):
    from jrv2.data import load_cell

    exec_bars, h1, period = load_cell(fz, "BTC_H1")
    assert period == HOUR
    assert len(h1.ts_close) == 8759
    exec_bars, h4, period = load_cell(fz, "BTC_H4")
    assert period == H4
    assert len(h4.ts_close) == 2189
    exec_bars, spy_bars, period = load_cell(fz, "SPY_D1")
    assert period == DAY
    assert len(spy_bars.ts_close) == 2943
