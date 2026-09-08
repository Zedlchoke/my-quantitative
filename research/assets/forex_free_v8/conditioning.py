"""FOREX-FREE-V8 vintaged conditioning: staged-series loading and as-of
reconstruction under the frozen AX2 contract (p0_axis2_output_contract_v1.json).

Binding rules implemented here (verbatim semantics, no discretion):

* AX2-C1  AS-OF PULLS ONLY -- at a decision date ``d`` the conditioning value
  of an observation is the staged binding row with the LATEST
  ``realtime_start <= d`` (staged_vintaged_manifest.json: "as-of
  reconstruction: value in effect at decision D = row with realtime_start
  <= D, latest such row").  Current-vintage pulls do not exist in this
  module: there is no code path that reads a value without a decision date.
* AX2-C2  SINGLE-SNAPSHOT TRANSFORM -- the slope D(t) = T10YIE(t) - T5YIE(t)
  is computed inside ONE as-of snapshot (both legs read at the same decision
  date ``d``).  No splicing of vintages anywhere.
* AX2-C4  DECISION CLOCK -- the decision that can consume a vintaged value is
  the first daily 16:00 America/New_York clock strictly after the value's
  available_time (= first-binding vintage's realtime_start; a DATE read as
  that day's 00:00, so the same day's 16:00 clock is strictly after it --
  P0 mutation contract: "the T-1 obs must enter exactly at T's decision
  clock").  A vintage arriving k periods late shifts the consumed decision
  exactly k periods (mutation property, tested).
* AX2-C7  PROVENANCE -- the staged binding rows carry (obs date,
  realtime_start, realtime_end, value); this module preserves them and the
  family runner records the staged manifest sha in run identity.

Non-numeric staged values (FRED ".") are never conditioning values: an
observation whose as-of value is "." contributes no binding and no value;
the walk falls back to the latest earlier observation that did bind (the
carried value), fail-closed and deterministic.

No PnL anywhere in this module.
"""
from __future__ import annotations

import bisect
import json
import math
from collections import OrderedDict
from datetime import date

__all__ = [
    "DataBlocked",
    "parse_date",
    "load_staged_series",
    "first_binding_rt",
    "as_of_value",
    "build_grid",
    "AsOfReconstructor",
    "zscore",
]


class DataBlocked(RuntimeError):
    """Raised when the staged conditioning bytes are unusable (fail closed)."""


def parse_date(s: str) -> date:
    y, m, d = str(s).split("-")
    return date(int(y), int(m), int(d))


def load_staged_series(path: str) -> tuple[dict, list]:
    """Load one staged vintaged series file (staged_vintaged format).

    Returns ``(rows_by_obs, all_obs_dates)``:
      rows_by_obs   {obs_date: [(realtime_start, value), ...]} with NUMERIC
                    values only, each list sorted ascending by realtime_start
                    (non-numeric FRED values "." are never conditioning
                    values);
      all_obs_dates every staged observation date regardless of value (the
                    P2 census grid is "staged obs dates" -- holiday rows
                    listed with "." are still census clocks).

    A file that is missing, malformed, empty or all-non-numeric fails
    closed (DataBlocked) -- never a silent empty series.
    """
    try:
        with open(path) as f:
            raw = json.load(f)
    except OSError as exc:
        raise DataBlocked(f"STAGED_SERIES_MISSING: {path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise DataBlocked(f"STAGED_SERIES_MALFORMED: {path}: {exc}") from exc
    if not isinstance(raw, list) or not raw:
        raise DataBlocked(f"STAGED_SERIES_MALFORMED: {path}")
    by_obs: dict[date, list[tuple[date, float]]] = {}
    all_dates = set()
    for row in raw:
        try:
            obs = parse_date(row["date"])
            rt = parse_date(row["realtime_start"])
        except (KeyError, TypeError, ValueError) as exc:
            raise DataBlocked(f"STAGED_ROW_MALFORMED: {path}: {row!r}") from exc
        all_dates.add(obs)
        v = row.get("value")
        if isinstance(v, bool) or v is None:
            continue
        try:
            fv = float(v)
        except (TypeError, ValueError):
            continue  # FRED "." (holiday / not-published) -- never a value
        if not math.isfinite(fv):
            continue
        by_obs.setdefault(obs, []).append((rt, fv))
    if not all_dates:
        raise DataBlocked(f"STAGED_SERIES_EMPTY: {path}")
    for obs in by_obs:
        by_obs[obs].sort(key=lambda p: p[0])
    return by_obs, sorted(all_dates)


def first_binding_rt(rows: list[tuple[date, float]]) -> date:
    """available_time of an observation = its first-binding realtime_start."""
    return rows[0][0]


def as_of_value(rows: list[tuple[date, float]], d: date) -> float | None:
    """AX2-C1: value in effect at decision date ``d`` = the row with the
    latest realtime_start <= d.  None when the observation is not yet bound
    at ``d``."""
    best = None
    for rt, v in rows:  # ascending realtime_start
        if rt <= d:
            best = v
        else:
            break
    return best


def build_grid(series_all_dates: "OrderedDict[str, list]",
               s0_start: date, s0_end: date) -> list[date]:
    """The S0 decision grid: the intersection of the staged observation-date
    calendars of every consumed series (ALL staged obs dates, value-or-not),
    restricted to S0, ascending (P2 census: "grid = staged obs dates",
    n_clocks_S0 = 1907)."""
    grids = []
    for name in series_all_dates:
        grids.append({obs for obs in series_all_dates[name]
                      if s0_start <= obs <= s0_end})
    common = set.intersection(*grids) if grids else set()
    return sorted(common)


class AsOfReconstructor:
    """Sequential as-of walk state for one set of series on one fixed grid.

    For each series we precompute, over its NUMERIC observations only:
      bc(obs) = first grid clock strictly after its available_time
                (= first grid date >= first_binding_rt -- the 16:00-NY clock
                of that day is strictly after that day's 00:00, AX2-C4).
    A clock is a BINDING clock when at least one observation binds there.
    ``value_at(series, d)`` returns the as-of-d value of the latest
    observation whose binding clock is <= d (the "current" observation).
    """

    def __init__(self, grid: list[date],
                 series: "OrderedDict[str, dict[date, list]]"):
        if not grid:
            raise DataBlocked("EMPTY_GRID")
        self.grid = grid
        self.series_names = tuple(series.keys())
        self._cand_bc: dict[str, list[date]] = {}       # bc per obs, sorted obs
        self._cand_obs: dict[str, list[date]] = {}
        self._rows: dict[str, dict] = {}
        self._binding_at_clock: dict[date, int] = {}
        for name, rows_by_obs in series.items():
            pairs = []
            for obs, rows in rows_by_obs.items():
                rt0 = first_binding_rt(rows)
                # first grid clock >= rt0 (strictly-after semantics at DAY
                # precision: that day's 16:00 clock is strictly after the
                # day's 00:00 available_time -- AX2-C4 / P0 mutation rule)
                i = bisect.bisect_left(self.grid, rt0)
                if i >= len(self.grid):
                    continue  # binds beyond the grid -- never consumed
                pairs.append((self.grid[i], obs))
            pairs.sort()
            self._cand_bc[name] = [p[0] for p in pairs]
            self._cand_obs[name] = [p[1] for p in pairs]
            self._rows[name] = rows_by_obs
            for bc, _obs in pairs:
                self._binding_at_clock[bc] = \
                    self._binding_at_clock.get(bc, 0) + 1
        # prefix count of binding clocks strictly before each grid index
        self._prefix: list[int] = []
        c = 0
        for d in self.grid:
            self._prefix.append(c)
            if self._binding_at_clock.get(d, 0) > 0:
                c += 1
        self._total_binding_clocks = c

    @property
    def total_binding_clocks(self) -> int:
        return self._total_binding_clocks

    def binding_clocks_before(self, d: date) -> int:
        """Number of binding clocks strictly before grid clock ``d``."""
        i = bisect.bisect_left(self.grid, d)
        if i >= len(self.grid) or self.grid[i] != d:
            raise DataBlocked(f"CLOCK_NOT_ON_GRID: {d}")
        return self._prefix[i]

    def is_binding_clock(self, d: date) -> bool:
        return self._binding_at_clock.get(d, 0) > 0

    def current_obs(self, name: str, d: date) -> date | None:
        """Latest observation whose binding clock is <= d (None if none)."""
        bcs = self._cand_bc[name]
        i = bisect.bisect_right(bcs, d)
        if i == 0:
            return None
        return self._cand_obs[name][i - 1]

    def value_at(self, name: str, d: date) -> float | None:
        """As-of-d value of the series' current observation (AX2-C1); None
        when no observation has bound yet."""
        obs = self.current_obs(name, d)
        if obs is None:
            return None
        return as_of_value(self._rows[name][obs], d)

    def slope_at(self, d: date, leg_a: str, leg_b: str) -> float | None:
        """AX2-C2 single-snapshot transform: both legs read at the SAME
        as-of date d, inside one snapshot.  None if either leg is missing."""
        va = self.value_at(leg_a, d)
        vb = self.value_at(leg_b, d)
        if va is None or vb is None:
            return None
        return va - vb


def zscore(window: list[float], x: float) -> float | None:
    """z = (x - mean(window)) / population_std(window) (ddof=0; the frozen
    convention -- determinism is pinned by a hand-computed fixture test).
    None when the window is empty or its std is 0 (no dispersion -- never
    a fabricated signal)."""
    n = len(window)
    if n == 0:
        return None
    mu = math.fsum(window) / n
    var = math.fsum((v - mu) ** 2 for v in window) / n
    if var <= 0.0:
        return None
    return (x - mu) / math.sqrt(var)
