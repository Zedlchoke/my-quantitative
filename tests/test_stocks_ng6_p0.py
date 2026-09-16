"""STOCKS-NG6 P0 goldens (plans/PLAN_stocks_ng6.md §4 F5/F6/F8 + §5 construction).

Hand-computed fixtures on synthetic series — no network, no cache, no PnL:
  test_event_construction_golden   §5 anchor: exactly 2 events at hand-computed
                                   indices (252 and 310), warmup enforced at the
                                   253rd served session, per-condition binds.
  test_clock_fixture_golden        F5: decision t close / entry t+1 open /
                                   exit t+11 open (H=10).
  test_band_resolution_failclosed  F6: band boundaries inclusive per schedule;
                                   missing/non-finite ADV raises (never a default).
  test_fold_floor_failclosed       F8/Q-6: <30 events in any fold raises.
"""

from __future__ import annotations

import importlib.util
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pytest

WT = Path("/Users/hoangminhlong/my-quantitative/.worktrees/stocks-ng6/integration")
_spec = importlib.util.spec_from_file_location(
    "sng6_p0_run",
    WT / "research/control/stocks_ng6_run/p0/p0_census_run.py")
p0 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(p0)


def iso_dates(n: int, start: str = "2015-01-02") -> list[str]:
    d0 = date.fromisoformat(start)
    out, d = [], d0
    while len(out) < n:
        if d.weekday() < 5:  # served sessions only
            out.append(d.isoformat())
        d += timedelta(days=1)
    return out


def base_series(n: int = 320, price: float = 20.0, low: float = 19.5,
                high: float = 20.5, vol: float = 200_000.0):
    dates = iso_dates(n)
    return (dates,
            np.full(n, price), np.full(n, high), np.full(n, low),
            np.full(n, price), np.full(n, vol))


V0 = 200_000.0  # x $20 close = $4M/session — above the $2M bookability floor


def test_event_construction_golden():
    """Exactly 2 anchor events at hand-computed indices 252 and 310.

    Sessions 0..251: price 20, low 19.5, high 20.5, vol V0.
    i=252 (the 253rd served session): low 18.5 < 19.5 (BREAK), close 19.6 >
    18.5 (RECLAIM), range (19.6-18.5)/(19.8-18.5) = 0.8462 >= 0.5, dvol
    2xV0 x 19.6 = 1.96x the trailing-60 median (V0 x 20) -> EVENT, band C
    ($4M trailing-252 median).  Sessions 253..309: base geometry,
    prior-window min low = 18.5 -> no break.
    i=310: low 18.4 < 18.5 (BREAK), close 19.0 > 18.5 (RECLAIM), range
    (19.0-18.4)/(19.2-18.4) = 0.75, dvol 1.8xV0 x 19.0 = 1.71x median ->
    EVENT.
    i=311..319: prior-window min = 18.4 -> no break.
    """
    dates, o, h, l, c, v = base_series(320)
    l[252], c[252], h[252], v[252] = 18.5, 19.6, 19.8, 2 * V0
    l[310], c[310], h[310], v[310] = 18.4, 19.0, 19.2, int(1.8 * V0)
    events, drops = p0.compute_events(dates, o, h, l, c, v)
    assert [e["i"] for e in events] == [252, 310]
    # hand-computed properties of event A
    a = events[0]
    assert a["date"] == dates[252]
    assert a["prior_low"] == 19.5
    assert a["range_frac"] == pytest.approx((19.6 - 18.5) / (19.8 - 18.5), abs=1e-4)
    assert a["dvol_ratio"] == pytest.approx(2.0 * 19.6 / 20.0, abs=1e-3)
    assert a["bookable"] is True
    assert a["band"] == "C"  # trailing-252 median dvol $4M -> band C
    b = events[1]
    assert b["prior_low"] == 18.5 and b["band"] == "C"
    # warmup: no event before the 253rd served session, by construction
    assert all(e["i"] >= 252 for e in events)
    # a short series cannot produce events at all
    ev_short, _ = p0.compute_events(dates[:252], o[:252], h[:252], l[:252],
                                    c[:252], v[:252])
    assert ev_short == []


def test_event_condition_binds():
    """Each §5 condition must bind: drop counted, event refused."""
    dates, o, h, l, c, v = base_series(320)
    # (1) break without reclaim (close below the broken level)
    l2, c2, h2, v2 = l.copy(), c.copy(), h.copy(), v.copy()
    l2[252], c2[252], h2[252], v2[252] = 18.5, 18.0, 19.8, 2 * V0
    ev, d = p0.compute_events(dates, o, h2, l2, c2, v2)
    assert ev == [] and d["break_no_reclaim"] == 1
    # (2) reclaim but sub-half range close: lo 19.0, hi 20.4, close 19.6
    #     range = (19.6-19.0)/(20.4-19.0) = 0.4286 < 0.5
    l3, c3, h3 = l.copy(), c.copy(), h.copy()
    l3[252], c3[252], h3[252] = 19.0, 19.6, 20.4
    ev, d = p0.compute_events(dates, o, h3, l3, c3, v)
    assert ev == [] and d["range"] == 1
    # (3) participation miss: 1.2x trailing median
    v4 = v.copy()
    v4[252] = int(1.2 * V0)
    l4, c4, h4 = l.copy(), c.copy(), h.copy()
    l4[252], c4[252], h4[252] = 18.5, 19.6, 19.8
    ev, d = p0.compute_events(dates, o, h4, l4, c4, v4)
    assert ev == [] and d["dvol"] == 1
    # (4) bookability floor: $0.90 adjusted close and $1M trailing-60 median
    c5 = c.copy() * 0.045  # $0.90 closes everywhere; dvol $180k < $2M floor
    l5, h5 = l * 0.045, h * 0.045
    l5[252], c5[252], h5[252] = 18.5 * 0.045, 19.6 * 0.045, 19.8 * 0.045
    v5 = v.copy()
    v5[252] = 40 * V0  # 40x ratio so the participation condition passes
    ev, d = p0.compute_events(dates, o * 0.045, h5, l5, c5, v5)
    assert len(ev) == 1 and ev[0]["bookable"] is False
    assert d["floor_price"] == 1 and d["floor_dvol"] == 1
    assert ev[0]["band"] == "SUBFLOOR"


def test_clock_fixture_golden():
    """F5: decision at t close, entry t+1 open, exit t+11 open (H=10)."""
    n = 20
    dates = iso_dates(n)
    opens = np.array([10.0 + 0.1 * i for i in range(n)])
    t, t_entry, t_exit = p0.clock_legs(5)
    assert (t, t_entry, t_exit) == (5, 6, 16)
    # a book following the frozen clock: entry open[6], exit open[16]
    entry_px, exit_px = opens[t_entry], opens[t_exit]
    assert entry_px == pytest.approx(10.6)
    assert exit_px == pytest.approx(11.6)
    assert t_exit - t_entry == 10  # H = 10 holding sessions
    # horizon legs never touch the decision session's own bar
    assert t_entry > t


def test_band_resolution_failclosed():
    """F6 bands: inclusive boundaries per schedule; undefined input raises."""
    assert p0.resolve_band(50e6) == "A"
    assert p0.resolve_band(50e6 - 1) == "B"
    assert p0.resolve_band(10e6) == "B"
    assert p0.resolve_band(10e6 - 1) == "C"
    assert p0.resolve_band(2e6) == "C"
    assert p0.resolve_band(2e6 - 1) == "SUBFLOOR"
    for bad in (None, float("nan"), float("inf")):
        with pytest.raises(ValueError):
            p0.resolve_band(bad)


def test_fold_floor_failclosed():
    """F8/Q-6: any fold below 30 events fails closed; exactly 30 passes."""
    with pytest.raises(p0.FoldFloorError):
        p0.check_fold_floor({"F1": 40, "F2": 25, "F3": 60})
    with pytest.raises(p0.FoldFloorError):
        p0.check_fold_floor({"F1": 29, "F2": 30, "F3": 31})
    p0.check_fold_floor({"F1": 30, "F2": 31, "F3": 29 + 1})
    p0.check_fold_floor({"F1": 40, "F2": 30, "F3": 60})
