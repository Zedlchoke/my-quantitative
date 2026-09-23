"""H4 derivation golden tests (plan §14, L2-specific): completeness law,
partial-bucket exclusion, alignment, aggregation values."""

import numpy as np
import pandas as pd
import pytest

from research.control.phase_strategy_v1.lane_btc_h4.pipeline import config
from research.control.phase_strategy_v1.lane_btc_h4.pipeline.h4derive import (
    assign_bucket, derive_h4, integrity_report, _gap_stats)

H1 = config.H1_MS
H4 = config.H4_MS
T0 = 1577836800000  # 2020-01-01T00:00:00Z


def _bar(open_ms, o, h, l, c, v):
    return {"open_time_ms": open_ms, "close_time_ms": open_ms + H1 - 1,
            "open": o, "high": h, "low": l, "close": c, "volume": v,
            "quote_volume": v * c, "count": 10,
            "taker_buy_volume": v / 2, "taker_buy_quote_volume": v * c / 2}


def test_bucket_alignment_floor_law():
    ts = pd.Series([T0, T0 + 3 * H1, T0 + 4 * H1, T0 + 7 * H1, T0 + 8 * H1 - 1])
    b = assign_bucket(ts)
    assert b.tolist() == [T0, T0, T0 + 4 * H1, T0 + 4 * H1, T0 + 4 * H1]


def test_completeness_law_and_aggregation_values():
    rows = [
        # complete bucket 00:00 (slots 0..3) — hand-computed aggregation
        _bar(T0 + 0 * H1, 100, 110, 95, 105, 1.0),
        _bar(T0 + 1 * H1, 105, 120, 100, 118, 2.0),
        _bar(T0 + 2 * H1, 118, 119, 90, 95, 3.0),
        _bar(T0 + 3 * H1, 95, 130, 94, 127, 4.0),
        # bucket 04:00 with only 3 bars -> PARTIAL, excluded
        _bar(T0 + 4 * H1, 127, 128, 120, 122, 5.0),
        _bar(T0 + 5 * H1, 122, 126, 121, 125, 6.0),
        _bar(T0 + 6 * H1, 125, 129, 124, 128, 7.0),
        # bucket 08:00 with slots 1,2,3 only (open 09:00) -> excluded
        _bar(T0 + 9 * H1, 128, 131, 127, 130, 8.0),
        _bar(T0 + 10 * H1, 130, 132, 129, 131, 9.0),
        _bar(T0 + 11 * H1, 131, 133, 130, 132, 10.0),
    ]
    df1h = pd.DataFrame(rows)
    h4, report = derive_h4(df1h)
    assert report["n_partial_buckets_excluded"] == 2
    assert report["n_misaligned_excluded"] == 0
    assert len(h4) == 1
    row = h4.iloc[0]
    assert row["bucket_ms"] == T0
    assert row["open"] == 100.0          # slot-0 open
    assert row["high"] == 130.0          # max high
    assert row["low"] == 90.0            # min low
    assert row["close"] == 127.0         # slot-3 close
    assert row["volume"] == 10.0         # sum
    assert row["count"] == 40            # sum


def test_data_end_and_gap_stats():
    times = np.array([T0, T0 + H1, T0 + 2 * H1, T0 + 6 * H1, T0 + 7 * H1])
    missing, longest = _gap_stats(times, H1, T0 + 7 * H1)
    assert (missing, longest) == (3, 3)  # slots 3,4,5 missing, one run of 3h


def test_integrity_blocked_on_excess_gaps():
    # calendar 0..200h, only every 10th bar present -> fraction 0.1 > 0.0005
    times = np.arange(T0, T0 + 200 * H1, 10 * H1, dtype="int64")
    df1h = pd.DataFrame([_bar(int(t), 1, 2, 0.5, 1.5, 1.0) for t in times])
    h4, _ = derive_h4(df1h)
    rep = integrity_report(df1h, h4, int(times[-1]))
    assert rep["verdict"] == "BLOCKED"


def test_integrity_passes_on_contiguous_series():
    times = np.arange(T0, T0 + 50 * H1, H1, dtype="int64")
    df1h = pd.DataFrame([_bar(int(t), 1.0 + (t == T0), 2.0, 0.5, 1.5, 1.0) for t in times])
    h4, _ = derive_h4(df1h)
    rep = integrity_report(df1h, h4, int(times[-1]))
    assert rep["verdict"] == "PASS"
    assert rep["zero_volume_bars"]["h1"] == 0
