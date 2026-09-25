"""Synthetic smoke tests for build_bars internals (no downloaded bytes,
no outcomes): H1 grouping law, gap census micro-gap enumeration, DST
table visibility, and the reconcile-median machinery on constructed bars.
"""
import datetime as dt

import numpy as np
import pandas as pd
import pytest

import build_bars as B


def _bars(ts_list, pip=1e-4, px=1.0):
    rows = []
    for t in ts_list:
        o = px + (t.minute % 7) * pip
        rows.append({
            "ts": t, "b_o": o, "b_h": o + 4 * pip, "b_l": o - 4 * pip,
            "b_c": o + 2 * pip, "a_o": o + 2 * pip, "a_h": o + 6 * pip,
            "a_l": o - 2 * pip, "a_c": o + 4 * pip,
            "s_open": 2 * pip, "s_close": 2 * pip,
        })
    df = pd.DataFrame(rows)
    df["ts"] = pd.to_datetime(df["ts"], utc=True)
    return df.sort_values("ts").reset_index(drop=True)


def _hour_bars(day, h0, h1, pip=1e-4):
    """Valid 15m bar-open timestamps for hours [h0, h1) of a UTC day."""
    base = dt.datetime(day.year, day.month, day.day, tzinfo=dt.timezone.utc)
    return [base + dt.timedelta(minutes=15 * (h * 4 + q))
            for h in range(h0, h1) for q in range(4)]


def _to_epoch_s(df):
    return (df["ts"].dt.tz_convert("UTC").dt.tz_localize(None)
            .to_numpy().astype("datetime64[s]").astype("int64"))


def test_h1_grouping_needs_four_consecutive():
    day = dt.date(2024, 3, 6)
    full = _hour_bars(day, 1, 3)                       # two complete hours
    broken = [t for t in full if not (t.hour == 1 and t.minute == 45)]
    df = _bars(broken)
    ts_s = _to_epoch_s(df)
    in_hour = ts_s // 3600
    start, groups = 0, []
    for i in range(1, len(df) + 1):
        if i == len(df) or in_hour[i] != in_hour[start]:
            groups.append((start, i, in_hour[start]))
            start = i
    sizes = [g[1] - g[0] for g in groups]
    assert sizes == [3, 4]  # hour 1 lost a bar; hour 2 intact
    assert groups[0][2] * 3600 == int(dt.datetime(2024, 3, 6, 1,
                                                  tzinfo=dt.timezone.utc).timestamp())


def test_micro_gap_enumeration_counts_missing_slots():
    fri = dt.date(2024, 3, 8)
    ts = _hour_bars(fri, 0, 6) + _hour_bars(fri, 8, 10)  # hole 06:00-08:00
    df = _bars(ts)
    ts_s = _to_epoch_s(df)
    hour = df["ts"].dt.hour.to_numpy()
    g = B.gap_census(df, ts_s, hour)
    mg = g["micro_gaps"]
    assert mg["count"] == 8  # 2 hours x 4 quarter slots
    assert mg["by_hour_of_day"][6] == 4 and mg["by_hour_of_day"][7] == 4
    assert mg["entries_capped_500"][0]["hour"] == 6


def test_weekend_boundary_and_dst_table_shapes():
    fri = dt.date(2024, 11, 1)
    sun = dt.date(2024, 11, 3)   # US fall-back Sunday: opens 22:00 UTC
    mon = dt.date(2024, 11, 4)
    ts = _hour_bars(fri, 0, 21) + _hour_bars(sun, 22, 24) + _hour_bars(mon, 0, 6)
    df = _bars(ts)
    ts_s = _to_epoch_s(df)
    hour = df["ts"].dt.hour.to_numpy()
    g = B.gap_census(df, ts_s, hour)
    wb = g["weekend_boundaries"]
    assert wb["count"] == 1
    assert wb["entries_capped_80"][0]["next_open_dow"] == 6
    expected_gap_h = (dt.datetime(2024, 11, 3, 22, tzinfo=dt.timezone.utc)
                      - dt.datetime(2024, 11, 1, 20, 45, tzinfo=dt.timezone.utc)
                      ).total_seconds() / 3600
    assert wb["entries_capped_80"][0]["gap_hours"] == pytest.approx(expected_gap_h)
    # DST table covers the transition Sunday and reports observed hour 22
    row = [r for r in g["dst_shift_table"]
           if r["date"] == "2024-11-03" and r["transition"] == "US_fall"][0]
    assert row["in_panel"] and row["observed_first_sunday_bar_utc_hour"] == 22


def test_bucket_median_reconcile_machinery():
    """The reconcile comparison (median of persisted bars vs census p50)
    rounds identically on a constructed panel."""
    fri = dt.date(2024, 3, 8)
    ts = _hour_bars(fri, 12, 16)  # 16 bars in ny_overlap
    df = _bars(ts)
    pip = 1e-4
    s_open = df["s_open"].to_numpy() / pip
    hour = df["ts"].dt.hour.to_numpy()
    dow = df["ts"].dt.dayofweek.to_numpy()
    mk = B.session_bucket(hour, dow)["ny_overlap_12_16"]
    med = round(float(np.median(s_open[mk])), 3)
    census_p50 = B.q3(s_open[mk])["50"]
    assert med == census_p50
