"""FOREX-FREE-V9 conditioning: staged CPI legs, availability instants and the
frozen surprise/momentum primitives (frozen specs: research/control/
forex_free_v9_run/d1/a5-open/proposal-1.json + proposal-2.json; p3 freeze
p3_invariants_freeze_v9.json; p0 census p0_census_v9.json).

Binding rules implemented here (verbatim frozen mechanics, no discretion):

* LEGS (mission frozen mechanics) --
    GB  ONS D7BT CPI INDEX 00 ALL ITEMS 2015=100, monthly (official table;
        staged at data_raw/forex_free_v9_cpi/GB/ons_d7bt_cpi_allitems.csv)
    CA  StatCan 18100004 Canada all-items NSA 2002=100, monthly (official
        tidy table; staged .../CA/canada_allitems_nsa_2002_100_monthly.csv)
    AU  FRED vintaged AUSCPIALLQINMEI, quarterly obs at quarter-first-months
    NZ  FRED vintaged NZLCPIALLQINMEI, quarterly obs at quarter-first-months
    US  FRED vintaged CPIAUCSL, monthly
  AU/NZ/US read ONLY through the staged vintaged archives; GB/CA read the
  official tables (single self-consistent base per table, so the y/y log
  step never straddles a base change).

* AVAILABILITY --
    GB/CA  pinned announcement calendars refined over the mid-next-month
           placeholder class: GB release dates from the pinned GB_cal
           (sha256 aad19697...), CA release dates from the pinned CA_v3
           calendar (sha256 0f1a9328...).  A print month without a calendar
           entry falls back to the placeholder instant = the 15th of the
           following month.  CA reference month = the month preceding the
           release month (StatCan releases month M during M+1).
    AU/NZ/US  FRED first-binding realtime_start of the observation
           (vintaged; no release calendar is consumed for these legs).
  The +7d sham-calendar neighbour shifts EVERY availability instant by
  exactly 7 calendar days (pinned dates and FRED realtime_starts alike).

* AX2-C4 DECISION CLOCK -- a print's value is consumable at the first daily
  16:00 America/New_York grid clock strictly after its availability instant
  (the instant is a DATE read as that day's 00:00, so the same day's 16:00
  clock is strictly after it).  A print arriving k periods late shifts the
  consumed decision exactly k periods (mutation property, tested).

* Y/Y LOG STEP (pi), as-bound + rebase-safe (AX2-C1/C3) --
  pi(print) is computed EXACTLY ONCE, at the print's own availability
  instant d, from the single as-of snapshot curve at d:
      pi = log(curve_d[p] / curve_d[p - 12 months])
  For the vintaged legs curve_d[x] is the staged row of obs x with the
  latest realtime_start <= d; because one vintage publication is a single
  self-consistent base, the step never straddles a rebase (the AU rebase
  vintage 2018-10-09 inside S0 is handled structurally by the
  single-snapshot computation -- AX2-C3 rebase-safety by construction).
  The frozen value then enters the as-bound history and is NEVER
  recomputed when later vintages revise the curve.

* SURPRISE (FXFV9-A5-P1, percentage points) --
  surprise(leg, print) = (pi(print) - trailing-OLS-trend value) * 100
  with the trend the OLS linear fit of pi over the trailing 24 calendar
  months of prints (24 obs monthly legs, 8 obs quarterly legs) evaluated at
  the latest print's period.  The state is piecewise constant between
  prints: the trend is recomputed only when a new print binds.

* AX2-C2 SINGLE SNAPSHOT -- both legs of any differential/gap read under
  one as-of state per decision clock; no vintage mixing within a decision.

No PnL anywhere in this module.
"""
from __future__ import annotations

import bisect
import json
import math
import os
from collections import OrderedDict
from datetime import date

__all__ = [
    "DataBlocked",
    "parse_date",
    "parse_month",
    "add_months",
    "load_fred_vintaged",
    "load_ons_d7bt",
    "load_statcan_csv",
    "load_gb_calendar",
    "load_ca_calendar",
    "placeholder_release",
    "curve_value",
    "first_binding_rt",
    "ols_fitted_last",
    "EconomyLeg",
    "build_economy_legs",
    "binding_events",
    "walk_pi_states",
    "walk_surprise_states",
    "FRED_VINTAGED_FILES",
    "OFFICIAL_FILES",
    "TREND_WINDOW_BY_FREQ",
]

MONTH_NAMES = {  # ONS "YYYY MMM" display months (deterministic, no locale)
    "JAN": 1, "FEB": 2, "MAR": 3, "APR": 4, "MAY": 5, "JUN": 6,
    "JUL": 7, "AUG": 8, "SEP": 9, "OCT": 10, "NOV": 11, "DEC": 12,
}
_TITLE_TO_NUM = {  # full month titles ("January"...) -> 1..12
    "january": 1, "february": 2, "march": 3, "april": 4, "may": 5,
    "june": 6, "july": 7, "august": 8, "september": 9, "october": 10,
    "november": 11, "december": 12,
}

# staged files (relative to the CPI staging root data_raw/forex_free_v9_cpi)
FRED_VINTAGED_FILES = OrderedDict((
    ("AU", "fred_vintaged/AUSCPIALLQINMEI.json"),
    ("NZ", "fred_vintaged/NZLCPIALLQINMEI.json"),
    ("US", "US/fred_cpiaucsl_rt.json"),
))
OFFICIAL_FILES = OrderedDict((
    ("GB", "GB/ons_d7bt_cpi_allitems.csv"),
    ("CA", "CA/canada_allitems_nsa_2002_100_monthly.csv"),
))
# pinned announcement calendars (committed control bytes; sha256-pinned by
# the exec driver -- p2_conditioning_clocks_v9.json pins)
GB_CAL_RELPATH = os.path.join("research", "control", "forex_free_v5_run",
                              "gb_ons_cpi_release_dates.json")
CA_CAL_RELPATH = os.path.join("research", "control", "forex_free_v6_run",
                              "ca_statcan_cpi_release_dates_v3.json")

TREND_WINDOW_BY_FREQ = {"monthly": 24, "quarterly": 8}
PLACEHOLDER_DAY = 15      # mid-next-month placeholder class
FREQ_BY_ECONOMY = {"GB": "monthly", "CA": "monthly", "AU": "quarterly",
                   "NZ": "quarterly", "US": "monthly"}


class DataBlocked(RuntimeError):
    """Raised when the staged conditioning bytes are unusable (fail closed)."""


def parse_date(s: str) -> date:
    y, m, d = str(s).split("-")
    return date(int(y), int(m), int(d))


def parse_month(s: str) -> date:
    """First day of a monthly period.  Accepts "YYYY-MM" (StatCan tidy) and
    "YYYY MMM" (ONS display, e.g. "1988 JAN")."""
    s = str(s).strip()
    if "-" in s:
        y, m = s.split("-")[:2]
        return date(int(y), int(m), 1)
    parts = s.split()
    if len(parts) != 2 or parts[1].upper() not in MONTH_NAMES:
        raise ValueError(f"unparseable month period: {s!r}")
    return date(int(parts[0]), MONTH_NAMES[parts[1].upper()], 1)


def add_months(d: date, k: int) -> date:
    """First-of-month shift by k months (d must be a first-of-month)."""
    y, m = d.year, d.month - 1 + k
    y += m // 12
    m = m % 12 + 1
    if d.day != 1:
        raise DataBlocked(f"add_months requires first-of-month: {d}")
    return date(y, m, 1)


# ------------------------------------------------------------------ loaders #
def load_fred_vintaged(path: str) -> dict:
    """Load one staged FRED vintaged archive.  Accepts BOTH staged formats:
    the ALFRED nested form {"observations": [...]} and the flat row list.
    Returns {obs_date: [(realtime_start, value), ...]} with NUMERIC values
    only, each list sorted ascending by realtime_start (FRED "." rows are
    never conditioning values).  Missing/malformed/empty fails closed."""
    try:
        with open(path) as f:
            raw = json.load(f)
    except OSError as exc:
        raise DataBlocked(f"STAGED_SERIES_MISSING: {path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise DataBlocked(f"STAGED_SERIES_MALFORMED: {path}: {exc}") from exc
    if isinstance(raw, dict):
        raw = raw.get("observations")
    if not isinstance(raw, list) or not raw:
        raise DataBlocked(f"STAGED_SERIES_MALFORMED: {path}")
    by_obs: dict[date, list[tuple[date, float]]] = {}
    for row in raw:
        try:
            obs = parse_date(row["date"])
            rt = parse_date(row["realtime_start"])
        except (KeyError, TypeError, ValueError) as exc:
            raise DataBlocked(f"STAGED_ROW_MALFORMED: {path}: {row!r}") from exc
        v = row.get("value")
        if isinstance(v, bool) or v is None:
            continue
        try:
            fv = float(v)
        except (TypeError, ValueError):
            continue          # FRED "." -- never a conditioning value
        if not math.isfinite(fv):
            continue
        by_obs.setdefault(obs, []).append((rt, fv))
    if not by_obs:
        raise DataBlocked(f"STAGED_SERIES_EMPTY: {path}")
    for obs in by_obs:
        by_obs[obs].sort(key=lambda p: p[0])
    return by_obs


def load_ons_d7bt(path: str) -> dict:
    """ONS D7BT monthly table: CSV with a metadata header, annual rows
    ("1988","49.6") skipped, monthly rows ("1988 JAN","48.4") kept.
    Returns {month_first: value} (single self-consistent base)."""
    try:
        with open(path) as f:
            lines = f.read().splitlines()
    except OSError as exc:
        raise DataBlocked(f"OFFICIAL_TABLE_MISSING: {path}: {exc}") from exc
    table: dict[date, float] = {}
    for ln in lines:
        if not ln.strip():
            continue
        cells = _csv_cells(ln)
        if len(cells) < 2 or "-" in cells[0]:
            continue
        head = cells[0].strip().strip('"')
        if len(head.split()) == 1:      # annual row (or metadata) -- skipped
            continue
        try:
            period = parse_month(head)
        except ValueError:
            continue                    # metadata header line
        try:
            v = float(cells[1])
        except ValueError as exc:
            raise DataBlocked(f"OFFICIAL_ROW_MALFORMED: {path}: {ln!r}") \
                from exc
        if not math.isfinite(v):
            raise DataBlocked(f"OFFICIAL_ROW_NONFINITE: {path}: {ln!r}")
        table[period] = v
    if not table:
        raise DataBlocked(f"OFFICIAL_TABLE_EMPTY: {path}")
    return table


def _csv_cells(line: str) -> list:
    """Comma-separated cells of one CSV line (surrounding quotes stripped;
    the staged tables carry no embedded separators)."""
    return [c.strip().strip('"') for c in line.split(",")]


def load_statcan_csv(path: str) -> dict:
    """StatCan tidy table: header "ref_month,index_2002_100", rows
    "YYYY-MM,value".  Returns {month_first: value}."""
    try:
        with open(path) as f:
            lines = f.read().splitlines()
    except OSError as exc:
        raise DataBlocked(f"OFFICIAL_TABLE_MISSING: {path}: {exc}") from exc
    table: dict[date, float] = {}
    for ln in lines[1:]:
        if not ln.strip():
            continue
        cells = _csv_cells(ln)
        if len(cells) < 2:
            continue
        try:
            period = parse_month(cells[0])
        except ValueError:
            continue                    # header or comment
        try:
            v = float(cells[1])
        except ValueError as exc:
            raise DataBlocked(f"OFFICIAL_ROW_MALFORMED: {path}: {ln!r}") \
                from exc
        if not math.isfinite(v):
            raise DataBlocked(f"OFFICIAL_ROW_NONFINITE: {path}: {ln!r}")
        table[period] = v
    if not table:
        raise DataBlocked(f"OFFICIAL_TABLE_EMPTY: {path}")
    return table


def load_gb_calendar(path: str) -> dict:
    """Pinned GB announcement calendar (GB_cal, sha256 aad19697...):
    entries {reference_period: "january2018", release_date_display:
    "13 February 2018", ...}.  Returns {print_month_first: release_date}."""
    try:
        with open(path) as f:
            entries = json.load(f)
    except OSError as exc:
        raise DataBlocked(f"CALENDAR_MISSING: {path}: {exc}") from exc
    if not isinstance(entries, list):
        raise DataBlocked(f"CALENDAR_MALFORMED: {path}")
    out: dict[date, date] = {}
    for e in entries:
        ref = str(e.get("reference_period", ""))
        disp = str(e.get("release_date_display", ""))
        i = 0
        while i < len(ref) and ref[i].isalpha():
            i += 1
        try:
            period = date(int(ref[i:]), _TITLE_TO_NUM[ref[:i].lower()], 1)
            dd, mm, yy = disp.split()
            release = date(int(yy), _TITLE_TO_NUM[mm.lower()], int(dd))
        except (KeyError, ValueError) as exc:
            raise DataBlocked(f"CALENDAR_ROW_MALFORMED: {path}: {e!r}") \
                from exc
        out[period] = release
    return out


def load_ca_calendar(path: str) -> dict:
    """Pinned CA announcement calendar (CA_v3, sha256 0f1a9328...): entries
    {release_date: "2018-03-23", cpi_products: [...18100004...], ...}.
    The reference month of a release is the month PRECEDING the release
    month (StatCan publishes month M during M+1).  Returns
    {print_month_first: release_date}."""
    try:
        with open(path) as f:
            entries = json.load(f)
    except OSError as exc:
        raise DataBlocked(f"CALENDAR_MISSING: {path}: {exc}") from exc
    if not isinstance(entries, list):
        raise DataBlocked(f"CALENDAR_MALFORMED: {path}")
    out: dict[date, date] = {}
    for e in entries:
        try:
            release = parse_date(e["release_date"])
        except (KeyError, TypeError, ValueError) as exc:
            raise DataBlocked(f"CALENDAR_ROW_MALFORMED: {path}: {e!r}") \
                from exc
        ref = add_months(release.replace(day=1), -1)
        # one CPI release per reference month; keep the earliest in a clash
        if ref not in out or release < out[ref]:
            out[ref] = release
    return out


def placeholder_release(period: date) -> date:
    """Mid-next-month placeholder instant of a monthly print."""
    return add_months(period, 1).replace(day=PLACEHOLDER_DAY)


# ------------------------------------------------------- as-of curve reads #
def first_binding_rt(rows: list) -> date:
    """available_time of an observation = its first-binding realtime_start."""
    return rows[0][0]


def curve_value(rows: list, d: date) -> float | None:
    """AX2-C1: value in effect at date ``d`` = the row with the latest
    realtime_start <= d.  None when the observation is not yet bound at d."""
    best = None
    for rt, v in rows:                  # ascending realtime_start
        if rt <= d:
            best = v
        else:
            break
    return best


def ols_fitted_last(values: list) -> float:
    """OLS linear fit over ``values`` (regressor = print ordinal 0..w-1),
    evaluated at the LAST ordinal.  The fitted value at the last print's
    period is invariant to affine reparametrizations of the regressor, so
    the frozen 'trend value at the latest print's period' is exactly this.
    Deterministic via math.fsum (hand-computed fixture test pins it)."""
    w = len(values)
    if w < 2:
        raise DataBlocked("OLS_WINDOW_TOO_SHORT")
    x_bar = (w - 1) / 2.0
    y_bar = math.fsum(values) / w
    sxx = math.fsum((i - x_bar) ** 2 for i in range(w))
    sxy = math.fsum((i - x_bar) * (v - y_bar) for i, v in enumerate(values))
    b = sxy / sxx
    return y_bar + b * ((w - 1) - x_bar)


# ------------------------------------------------------------- economy legs #
class EconomyLeg:
    """One economy's CPI leg: prints, availability instants, as-bound y/y.

    channel 'official'  : single self-consistent monthly table; pi(print)
                          = log(table[p]/table[p-12m]) (no rebase possible
                          within one table).
    channel 'fred'      : staged vintaged archive; pi(print) is computed at
                          the print's availability instant d from the single
                          as-of snapshot curve at d (rebase-safe by
                          construction), then frozen (AX2-C1 as-bound).
    """

    def __init__(self, economy: str, channel: str, freq: str,
                 table: dict | None = None, rows_by_obs: dict | None = None,
                 calendar: dict | None = None):
        if channel not in ("official", "fred"):
            raise DataBlocked(f"BAD_CHANNEL: {channel}")
        if freq not in TREND_WINDOW_BY_FREQ:
            raise DataBlocked(f"BAD_FREQ: {freq}")
        self.economy = economy
        self.channel = channel
        self.freq = freq
        self.table = table
        self.rows_by_obs = rows_by_obs
        self.calendar = calendar or {}
        if channel == "official":
            self.prints = sorted(table)
        else:
            self.prints = sorted(rows_by_obs)

    def availability(self, print_period: date, shift_days: int = 0) -> date:
        """The frozen availability instant (a DATE at 00:00 local) of a
        print, optionally shifted +shift_days calendar days (the +7d sham)."""
        a = self._availability_unshifted(print_period)
        if shift_days:
            a = date.fromordinal(a.toordinal() + shift_days)
        return a

    def _availability_unshifted(self, print_period: date) -> date:
        if self.channel == "official":
            inst = self.calendar.get(print_period)
            if inst is not None:
                return inst
            return placeholder_release(print_period)
        rows = self.rows_by_obs.get(print_period)
        if not rows:
            raise DataBlocked(
                f"{self.economy}: print {print_period} has no staged rows")
        return first_binding_rt(rows)

    def pi(self, print_period: date, snapshot_date: date) -> float | None:
        """The y/y log step of a print, computed INSIDE the single snapshot
        ``snapshot_date`` (the print's own availability instant -- as-bound,
        never recomputed).  None (carried, fail-closed) when either leg of
        the step is not bound inside the snapshot."""
        prev = add_months(print_period, -12)   # y/y: 12 months back
        if self.channel == "official":
            a = self.table.get(print_period)
            b = self.table.get(prev)
        else:
            a = curve_value(self.rows_by_obs.get(print_period, ()),
                            snapshot_date)
            b = curve_value(self.rows_by_obs.get(prev, ()), snapshot_date)
        if a is None or b is None or a <= 0.0 or b <= 0.0:
            return None
        return math.log(a / b)

    def trend_window(self) -> int:
        return TREND_WINDOW_BY_FREQ[self.freq]


def build_economy_legs(cpi_dir: str, gb_calendar_path: str,
                       ca_calendar_path: str) -> "OrderedDict[str, EconomyLeg]":
    """Load the five frozen legs (order GB, CA, AU, NZ, US)."""
    legs: "OrderedDict[str, EconomyLeg]" = OrderedDict()
    legs["GB"] = EconomyLeg("GB", "official", "monthly",
                            table=load_ons_d7bt(
                                os.path.join(cpi_dir, OFFICIAL_FILES["GB"])),
                            calendar=load_gb_calendar(gb_calendar_path))
    legs["CA"] = EconomyLeg("CA", "official", "monthly",
                            table=load_statcan_csv(
                                os.path.join(cpi_dir, OFFICIAL_FILES["CA"])),
                            calendar=load_ca_calendar(ca_calendar_path))
    for econ in ("AU", "NZ", "US"):
        legs[econ] = EconomyLeg(
            econ, "fred", FREQ_BY_ECONOMY[econ],
            rows_by_obs=load_fred_vintaged(
                os.path.join(cpi_dir, FRED_VINTAGED_FILES[econ])))
    return legs


# ------------------------------------------------- binding events + walks #
def binding_events(legs, grid: list, shift_days: int = 0) -> dict:
    """{economy: [(binding_clock, print_period, snapshot_date), ...]} with
    binding_clock = first grid clock >= availability instant (AX2-C4: that
    day's 16:00-NY clock is strictly after the day's 00:00 instant), sorted
    by (clock, print period).  Prints whose availability lies beyond the
    grid never bind (never consumed)."""
    events: dict[str, list] = {}
    for econ, leg in legs.items():
        pairs = []
        for p in leg.prints:
            a = leg.availability(p, shift_days)
            i = bisect.bisect_left(grid, a)
            if i >= len(grid):
                continue                    # binds beyond the grid
            pairs.append((grid[i], p, a))
        pairs.sort(key=lambda t: (t[0], t[1]))
        events[econ] = pairs
    return events


def walk_pi_states(legs, grid: list, shift_days: int = 0) -> dict:
    """{economy: {clock: pi}}: the as-bound y/y state per economy per grid
    clock.  Each print's pi is computed once at its own availability
    snapshot and frozen; the state is piecewise constant between binding
    clocks (the quarterly-to-monthly forward-fill is this piecewise
    constancy -- no interpolation anywhere)."""
    events = binding_events(legs, grid, shift_days)
    states: dict[str, dict] = {}
    for econ, leg in legs.items():
        by_clock: dict[date, float | None] = {}
        current: float | None = None
        ev = events[econ]
        k = 0
        for d in grid:
            while k < len(ev) and ev[k][0] == d:
                pi = leg.pi(ev[k][1], ev[k][2])
                if pi is not None:
                    current = pi        # as-bound: frozen once computed
                k += 1
            by_clock[d] = current
        states[econ] = by_clock
    return states


def walk_surprise_states(legs, grid: list, shift_days: int = 0) -> dict:
    """{economy: {clock: surprise_pp}}: the FXFV9-A5-P1 surprise state.
    At each print's binding clock the print's pi is appended to the
    as-bound history and, once the frozen trend window is full, the surprise
    is recomputed ONLY there (piecewise constant between prints):
        surprise = (pi - ols_fitted_last(history[-window:])) * 100
    (percentage points).  A print whose pi is undefined contributes no
    binding and no value (the carried state persists, fail-closed)."""
    events = binding_events(legs, grid, shift_days)
    states: dict[str, dict] = {}
    for econ, leg in legs.items():
        w = leg.trend_window()
        history: list[float] = []
        by_clock: dict[date, float | None] = {}
        current: float | None = None
        ev = events[econ]
        k = 0
        for d in grid:
            while k < len(ev) and ev[k][0] == d:
                pi = leg.pi(ev[k][1], ev[k][2])
                if pi is not None:
                    history.append(pi)
                    if len(history) >= w:
                        trend = ols_fitted_last(history[-w:])
                        current = (pi - trend) * 100.0
                k += 1
            by_clock[d] = current
        states[econ] = by_clock
    return states
