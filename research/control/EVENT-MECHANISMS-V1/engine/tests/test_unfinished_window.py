"""E6(c) — unfinished-window guard + planted-future-bars invariance."""
import math
from datetime import datetime, date, timedelta

import pytest

from emv1 import clock
from emv1.guard import LookaheadRead, assert_readable, closed_index_range
from emv1.panel import NameSeries, dvmed60


def make_ns(d0="2024-01-01", d1="2024-12-31"):
    ns = NameSeries("TEST")
    d = date.fromisoformat(d0)
    while d <= date.fromisoformat(d1):
        if d.weekday() < 5:
            ds = d.isoformat()
            ns.dates.append(ds)
            ns.idx[ds] = len(ns.dates) - 1
            ns.open.append(10.0)
            ns.high.append(11.0)
            ns.low.append(9.0)
            ns.close.append(10.5)
            ns.vol.append(1_000_000.0)
            ns.dv.append(10_500_000.0)
            ns.fill_ok.append(True)
        d += timedelta(days=1)
    return ns


def test_guard_raises_on_future_bar_read():
    ns = make_ns()
    # decision at the open of 2024-06-10: bars closing after that are future
    decision = clock.session_open_instant(date(2024, 6, 10))
    future_i = ns.idx["2024-06-10"]  # this bar closes 16:00 > 09:30 decision
    with pytest.raises(LookaheadRead):
        assert_readable(ns, [future_i], decision)
    closed_i = ns.idx["2024-06-07"]  # Friday bar closed before Monday 09:30
    assert_readable(ns, [closed_i], decision)  # no raise
    assert closed_index_range(ns, decision) == closed_i


def test_dvmed60_invariant_to_planted_future_bars():
    """Feature read at decision time must be unchanged when future bars are
    planted with absurd values (no-lookahead proof at feature level)."""
    ns = make_ns()
    decision = clock.session_open_instant(date(2024, 6, 10))
    last_closed = closed_index_range(ns, decision)
    base = dvmed60(ns, last_closed)
    ns2 = make_ns()
    for i in range(last_closed + 1, len(ns2.dates)):
        ns2.close[i] = 1e12
        ns2.dv[i] = 1e18
    planted = dvmed60(ns2, last_closed)
    assert base == planted
    assert base == pytest.approx(10_500_000.0)


def test_dvmed60_fail_closed_on_short_history():
    ns = make_ns(d0="2024-06-03", d1="2024-07-10")  # < 30 sessions
    n = len(ns.dates)
    assert n < 30
    assert dvmed60(ns, n - 1) is None  # fail-closed, never fabricates
