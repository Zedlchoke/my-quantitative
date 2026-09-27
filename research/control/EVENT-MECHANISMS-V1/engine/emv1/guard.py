"""Unfinished-window guard (E6c): windowed features may only read CLOSED bars.

A bar is closed at instant T iff its session close instant (16:00 ET of the
bar date) is <= T. Every windowed feature in this engine routes its reads
through `assert_readable`, which raises LookaheadRead if a bar not yet closed
at the decision instant is touched. The G4 test plants future bars and
asserts feature invariance.
"""
from __future__ import annotations

from datetime import date, datetime
from typing import Iterable

from . import clock
from .panel import NameSeries


class LookaheadRead(AssertionError):
    pass


def assert_readable(ns: NameSeries, indices: Iterable[int], decision_instant: datetime) -> None:
    """Raise LookaheadRead if any index's bar close is after decision_instant."""
    for i in indices:
        if i < 0 or i >= len(ns.dates):
            raise LookaheadRead(f"{ns.ticker}: index {i} outside panel")
        d = date.fromisoformat(ns.dates[i])
        if clock.session_close_instant(d) > decision_instant:
            raise LookaheadRead(
                f"{ns.ticker}: bar {ns.dates[i]} closes after decision instant "
                f"{decision_instant.isoformat()} (unfinished-window read)"
            )


def closed_index_range(ns: NameSeries, decision_instant: datetime) -> int:
    """Highest bar index fully closed at decision_instant (-1 if none)."""
    lo, hi, ans = 0, len(ns) - 1, -1
    while lo <= hi:
        mid = (lo + hi) // 2
        d = date.fromisoformat(ns.dates[mid])
        if clock.session_close_instant(d) <= decision_instant:
            ans = mid
            lo = mid + 1
        else:
            hi = mid - 1
    return ans
