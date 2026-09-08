"""SYNTHETIC_TEST_ONLY H1 fixtures for the family1 evidence tests.

Every bar below is constructed explicitly (no market data, no network, no
real-data PnL).  Geometry conventions, all hand-checkable:

* Base price P = 1.1000 (EUR/USD-like 4-decimal FX scale).
* A Tokyo session of date D with envelope (lo, hi) is 9 identical-inside bars
  stamped 00:00..08:00 UTC (Tokyo 09:00-17:00 JST wall): open = close =
  (lo+hi)/2, high = hi, low = lo  =>  range = hi - lo exactly,
  T_H = hi, T_L = lo, M = (hi+lo)/2 exactly.
* A "calm" afternoon bar at 0m UTC: open = close = M, high = M+0.0002,
  low = M-0.0002 (strictly inside every envelope used here: calm highs can
  never fire an anchor break because M+0.0002 < T_H whenever range > 0.0004,
  and can never fire a control break because calm high - M = +0.0002 > 0 ...
  calm bars DO breach M upward -- scenarios that must not fire the control
  arm set explicit afternoon bars instead).
* The 16:00 America/New_York flat bar of a day is stamped 20:00Z in EDT
  weeks and 21:00Z in EST weeks (documented DST mapping).

Day scenarios are given as explicit per-hour bar tables (hour -> OHLC tuple)
that override the calm default, so every golden price is visible in
goldens_family1.py.
"""
from __future__ import annotations

import datetime as _dt

BASE_P = 1.1000
TICK = 0.0001

# --- envelope helpers (range literals are derived in goldens_family1.py) ------- #
def envelope(range_pips: float, base: float = BASE_P) -> tuple[float, float]:
    """Symmetric Tokyo envelope: (lo, hi) = base -/+ range/2 (rounded to 10
    decimals so the fixtures carry the clean hand-written literals, e.g.
    1.0985 rather than 1.0985000000000001)."""
    half = range_pips / 2.0
    return (round(base - half, 10), round(base + half, 10))


def tokyo_bars(day: _dt.date, lo: float, hi: float,
               first_hour: int = 0, last_hour: int = 6) -> list[dict]:
    """Envelope bars for UTC hours first_hour..last_hour (default 00..06).

    Hours 07/08 UTC (Tokyo session tail AND London-morning head on BST days)
    are emitted by :func:`afternoon_bars` so scenario overrides can shape
    them; each UTC hour is emitted exactly once per day."""
    mid = (lo + hi) / 2.0
    return [
        {"datetime": f"{day.isoformat()} {h:02d}:00:00",
         "open": mid, "high": hi, "low": lo, "close": mid}
        for h in range(first_hour, last_hour + 1)
    ]


def calm_bar(day: _dt.date, hour: int, mid: float) -> dict:
    return {"datetime": f"{day.isoformat()} {hour:02d}:00:00",
            "open": mid, "high": mid + 2 * TICK, "low": mid - 2 * TICK,
            "close": mid}


def bar(day: _dt.date, hour: int, ohlc: tuple[float, float, float, float]) -> dict:
    o, h, l, c = ohlc
    return {"datetime": f"{day.isoformat()} {hour:02d}:00:00",
            "open": o, "high": h, "low": l, "close": c}


def afternoon_bars(day: _dt.date, lo: float, hi: float,
                   overrides: dict[int, tuple[float, float, float, float]] | None = None,
                   first_hour: int = 7, last_hour: int = 20) -> list[dict]:
    """Hours first_hour..last_hour inclusive (default 07..20: the London
    morning window on BST days starts at 07:00Z); calm default, explicit
    overrides.  Calm bars must stay strictly inside the Tokyo envelope so a
    session's range is decided by the envelope bars alone."""
    mid = (lo + hi) / 2.0
    overrides = overrides or {}
    return [
        (bar(day, h, overrides[h]) if h in overrides else calm_bar(day, h, mid))
        for h in range(first_hour, last_hour + 1)
    ]


# --- day specs ------------------------------------------------------------------ #
class DaySpec:
    """One synthetic trading day: Tokyo envelope + explicit hour overrides."""

    def __init__(self, day: _dt.date, lo: float, hi: float,
                 overrides: dict[int, tuple[float, float, float, float]] | None = None,
                 last_hour: int = 20):
        self.day = day
        self.lo = lo
        self.hi = hi
        self.overrides = overrides or {}
        self.last_hour = last_hour

    def rows(self) -> list[dict]:
        return (tokyo_bars(self.day, self.lo, self.hi)
                + afternoon_bars(self.day, self.lo, self.hi, self.overrides,
                                 last_hour=self.last_hour))


def weekday_dates(last_day: _dt.date, calendar_days: int) -> list[_dt.date]:
    """The Mon-Fri dates in the ``calendar_days`` days ending at ``last_day``."""
    first = last_day - _dt.timedelta(days=calendar_days - 1)
    return [first + _dt.timedelta(days=i) for i in range(calendar_days)
            if (first + _dt.timedelta(days=i)).weekday() < 5]


def default_world(last_day: _dt.date, calendar_days: int = 42,
                  default_range: float = 0.0050) -> list[DaySpec]:
    """A run of default days (Tokyo range 0.0050, calm afternoons) ending at
    ``last_day``.  Default days are never anchor-compressed (0.0050 is not
    < 0.75 * 0.0050) and calm afternoons never break, so only explicitly
    spec'd decision days can trade."""
    lo, hi = envelope(default_range)
    return [DaySpec(d, lo, hi) for d in weekday_dates(last_day, calendar_days)]


def build_rows(day_specs: list[DaySpec]) -> list[dict]:
    rows: list[dict] = []
    for spec in sorted(day_specs, key=lambda s: s.day):
        rows.extend(spec.rows())
    return rows
