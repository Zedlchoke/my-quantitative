"""DGS10 vintaged level series and the trailing-252-grid-day-median
nominal-yield-level state for the CTL-DGS10LEVEL arms.

As-of law (inherited verbatim from the V8 staged-vintaged manifest
semantics, which is how V8's committed DGS10 control consumed these
bytes): the value in effect at day ``d`` is the NUMERIC row with the
greatest ``realtime_start <= d``.  Each grid day's level is BOUND at its
own day and never re-pulled later (AX2-C1 inherited).

The state (frozen by both proposals' CTL-DGS10LEVEL configs):

    window  = the 252 grid days ending at and including D(e) (the grid
              extended backward before S0 with the same weekday-
              intersection law, so warmup never drops an anchor event);
    sign    = +1 (long funded currency vs USD) iff level(D(e)) is below
              the window median, else -1 (ties -> -1).
"""

from __future__ import annotations

from datetime import date

WINDOW_GRID_DAYS = 252


class Dgs10StateError(Exception):
    """Fail-closed DGS10 state error."""


class Dgs10LevelSeries:
    """DGS10 levels bound at their own grid days."""

    def __init__(self, rows: list[dict], extended_grid: list[date]):
        # numeric rows only; '.' rows never bind a value
        numeric = [r for r in rows if r["value"] is not None]
        if not numeric:
            raise Dgs10StateError("DGS10 archive carries no numeric rows")
        numeric.sort(key=lambda r: r["rs"])
        self._starts = [r["rs"] for r in numeric]
        self._values = [r["value"] for r in numeric]
        self.grid = list(extended_grid)
        self._index = {d: i for i, d in enumerate(self.grid)}
        self._levels: dict[date, float] = {}
        j = 0
        current = None
        for d in self.grid:
            while j < len(self._starts) and self._starts[j] <= d:
                current = self._values[j]
                j += 1
            if current is not None:
                self._levels[d] = current

    def level(self, day: date) -> float | None:
        """The DGS10 level in force at ``day`` (None before coverage)."""
        return self._levels.get(day)

    def state_sign(self, day: date) -> int | None:
        """+1 iff level(day) < median of the 252-grid-day window ending
        at and including ``day``; -1 otherwise; None when the window is
        not fully covered (fail-closed)."""
        i = self._index.get(day)
        if i is None:
            raise Dgs10StateError(f"{day} is not a grid day")
        if i + 1 < WINDOW_GRID_DAYS:
            return None
        window = [self._levels.get(g) for g in
                  self.grid[i + 1 - WINDOW_GRID_DAYS:i + 1]]
        if any(v is None for v in window):
            return None
        return self.compare(level=window[-1], window=window)

    @staticmethod
    def compare(level: float, window: list[float]) -> int:
        """The frozen comparison: below-median -> +1, else -1."""
        s = sorted(window)
        mid = len(s) // 2
        med = s[mid] if len(s) % 2 else 0.5 * (s[mid - 1] + s[mid])
        return 1 if level < med else -1


def extended_weekday_grid(pair_calendars: list[list[date]],
                          end: date, n_days: int) -> list[date]:
    """The common weekday-intersection grid ending at ``end`` with at
    least ``n_days`` entries (walked backward across the pinned spot
    calendars, same law as ``common_weekday_grid``)."""
    sets = [set(c) for c in pair_calendars]
    out: list[date] = []
    d = end
    while d >= date(2008, 1, 1) and len(out) < n_days:
        if d.weekday() < 5 and all(d in s for s in sets):
            out.append(d)
        d = date.fromordinal(d.toordinal() - 1)
    if len(out) < n_days:
        raise Dgs10StateError(
            f"extended grid too short: {len(out)} < {n_days}")
    out.reverse()
    return out
