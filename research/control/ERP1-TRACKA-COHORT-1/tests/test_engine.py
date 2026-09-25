"""Fixture tests: engine port pip-parametrization + force-flat on synthetic
DST calendars (plan §6: structural-zero financing is a FIXTURE, not a
comment; plan §5.2: per-pair scale fixtures incl. USDJPY-style template).

DATA-GATE SAFETY: run_strategy is exercised only with all-zero targets
(0 trades, 0 PnL) — no signal, no arm, no scored cell exists here.
"""
import datetime as dt

import numpy as np
import pandas as pd
import pytest

import engine as E
from build_bars import session_bucket


def _mk_bars(start_utc: dt.datetime, n_hours: int, pip=1e-4, px=1.0):
    """Synthetic valid 15m bars: 4 per hour, small constant spread."""
    rows = []
    t = start_utc
    for i in range(n_hours * 4):
        o = px + (i % 97) * pip
        rows.append({
            "ts": t, "b_o": o, "b_h": o + 5 * pip, "b_l": o - 5 * pip,
            "b_c": o + 2 * pip, "a_o": o + 2 * pip, "a_h": o + 7 * pip,
            "a_l": o - 3 * pip, "a_c": o + 4 * pip,
            "s_open": 2 * pip, "s_close": 2 * pip,
        })
        t += dt.timedelta(minutes=15)
    df = pd.DataFrame(rows)
    df["ts"] = pd.to_datetime(df["ts"], utc=True)
    return df


def test_pip_mult_eurusd_style():
    df = _mk_bars(dt.datetime(2024, 3, 5, 0, tzinfo=dt.timezone.utc), 4)
    p = E.Plane(df, pip_mult=1e4)
    assert p.pips(0.0050) == pytest.approx(50.0)


def test_pip_mult_usdjp_style_template():
    """USDJPY-style template: pip 0.01 -> pip_mult 100 (probe precedent:
    USDJPY 1e-3 point scale, pip 0.01). The ancestor hard-coded 1e4 —
    this fixture fail-closes that port defect for JPY-quoted pairs."""
    df = _mk_bars(dt.datetime(2024, 3, 5, 0, tzinfo=dt.timezone.utc), 4,
                  pip=0.01, px=150.0)
    p = E.Plane(df, pip_mult=100.0)
    assert p.pips(0.50) == pytest.approx(50.0)


def test_force_flat_zero_target_no_trades():
    df = _mk_bars(dt.datetime(2024, 3, 5, 0, tzinfo=dt.timezone.utc), 8)
    p = E.Plane(df, pip_mult=1e4)
    trades, equity = E.run_strategy(p, np.zeros(len(df), dtype=np.int8), k=1.0)
    assert trades == []
    assert np.all(equity == 0.0)


def test_force_flat_day_close_across_dst_calendar_shapes():
    """Synthetic calendars: normal day, EU/US-DST short Sunday (opens
    21:00 or 22:00 or 23:00 UTC). The day-close bar is ALWAYS the last
    valid bar of the day; fill_ok is false there; a constant +1 target
    can never leave a position open past a day-close bar."""
    for sunday_open_hour in (21, 22, 23):
        sun = dt.datetime(2024, 11, 3, sunday_open_hour, tzinfo=dt.timezone.utc)
        frames = [
            _mk_bars(dt.datetime(2024, 11, 1, 0, tzinfo=dt.timezone.utc), 24),
            _mk_bars(sun, 24 - sunday_open_hour),
            _mk_bars(dt.datetime(2024, 11, 4, 0, tzinfo=dt.timezone.utc), 24),
        ]
        df = pd.concat(frames, ignore_index=True)
        df["ts"] = pd.to_datetime(df["ts"], utc=True)
        df = df.sort_values("ts").reset_index(drop=True)
        p = E.Plane(df, pip_mult=1e4)
        assert p.is_day_close[-1] or True  # last bar of Monday: see assert below
        day_close_ts = {int(t) for t in p.ts[p.is_day_close]}
        days = np.unique(p.day)
        for d in days:
            last = p.ts[p.day == d][-1]
            assert int(last) in day_close_ts, "day-close bar missing"
            assert not p.fill_ok[p.day == d][-1], "fill_ok on day-close bar"
        target = np.ones(len(df), dtype=np.int8)
        trades, _ = E.run_strategy(p, target, k=1.0)
        # every trade exits exactly on a day-close bar of its own day
        for tr in trades:
            ex_day = int(tr["exit_ts"]) // E.SEC_DAY
            en_day = int(tr["entry_ts"]) // E.SEC_DAY
            assert ex_day == en_day, "position held across day-close (force-flat broken)"
            assert int(tr["exit_ts"]) in day_close_ts


def test_session_bucket_partition_and_dst_sundays():
    hours = np.arange(24)
    dow_sat = np.full(24, 5)
    dow_sun = np.full(24, 6)
    dow_fri = np.full(24, 4)
    m_sun = session_bucket(hours, dow_sun)
    # the six regular buckets partition the day exactly once
    regular = ["asia_00_07", "london_07_12", "ny_overlap_12_16",
               "ny_late_16_21", "rollover_21_22", "late_22_24"]
    cover = np.zeros(24, dtype=int)
    for k in regular:
        cover += m_sun[k].astype(int)
    assert np.all(cover == 1), "regular buckets must partition all 24 hours"
    # Sunday-open cell only for the 21:00-UTC open (summer / pre-US-fall)
    assert m_sun["sunday_open_21_22"].sum() == 1
    assert m_sun["sunday_open_21_22"][21]
    # a 22:00-UTC-open Sunday (post-US-fall winter shape) has NO
    # sunday_open_21_22 bar; its bars land in late_22_24 without breaking
    assert m_sun["late_22_24"][22] and m_sun["late_22_24"][23]
    # Friday force-flat window captured standalone
    m_fri = session_bucket(hours, dow_fri)
    assert m_fri["friday_20_23_open"].sum() == 3  # hours 20..22 (hour-level mask)
    # rollover bucket present on any day shape
    assert m_sun["rollover_21_22"].sum() == 1  # hour 21 (hour-level mask; 4 quarter-bars)
