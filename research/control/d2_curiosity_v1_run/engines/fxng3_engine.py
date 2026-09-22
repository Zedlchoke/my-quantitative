"""fxng3_engine.py — FXNG3-A4-P1 verbatim-construction engine (cycle D2-CURIOSITY-V1).

NON_GOVERNING_DIAGNOSTIC lane. REPLAY_NOT_PROSPECTIVE. This module builds
per-position rows ONLY; it structurally REFUSES to compute aggregate
PnL/expectancy (``score_cells`` raises REFUSES_PRELAUNCH unless the
orchestrator sets ``ALLOW_SCORE = True`` at GO time — this lane never sets
it and there is no aggregate implementation in this lane at all).

FROZEN LAW (verbatim, no neighbours, no parameter search, no rescue):
  three_cell_contract.json cell FXNG3-A4-P1
  cost_contract.json FXNG3-A4-P1 (flat 1.5 bps/side ladder x{1.0,1.5,2.0};
      tier 2.0 PRIMARY; once per fill; 72x2 ceiling 432.0 bps arithmetic)
  sources/fxng3_a4_p1_identity.json (construction + missing_data_law + folds)
  BOUND data: ../data/fxng3/fred_vintaged_repull/CANCPIALLMINMEI_derived_events.json
              ../data/fxng3/twelvedata_repull/USDCAD_1day_repull.json

Construction (identity extract, verbatim):
  Events: the 72 CA first-print RESTRICTED revision events (R = I_v2/I_v1 - 1,
  both values strictly inside their own realtime windows, no later vintage
  ever read; bulk re-referencing excluded upstream). The engine recomputes
  R from the bound v1/v2 values and fail-closed requires exact float
  equality with the stored bound ratio.
  Direction: sign(R): R < 0 -> LONG USDCAD (+1); R > 0 -> SHORT (-1);
  exact zero -> no position (counted). 1 unit per fired event.
  Clock: D(e) = first COMMON-GRID day STRICTLY after EOD(v2.realtime_start)
  (date-only availability; a 16:00-NY decision can never see a v2 bounded
  EOD the same date). Decision at D close; entry fill at the NEXT grid
  bar's open after D (STRICT_NEXT_BAR); hold H = 5 grid days; exit fill at
  bar i+H open, where i is the entry bar (held cells i..i+H-1; the exit
  fill bar is NOT a held cell).
  Costs: 1.5 bps/side x tier {1.0, 1.5, 2.0}; tier 2.0 PRIMARY = 3.0
  bps/fill, charged once per fill, 2 fills per position = 6.0 bps round
  trip per unit notional; 72 positions x 2 fills x 3.0 bps = 432.0 bps
  ceiling arithmetic preserved. No funding/carry modeled (disclosed in the
  cost contract); no slippage model beyond the flat ladder (UNMEASURED).
  Folds: F1 2018-04..2020-06, F2 2020-07..2022-10, F3 2022-11..2025-04,
  FORCE_FLAT at boundaries. Implemented reading (disclosed): a position
  never spans a fold boundary; the normal exit is bar i+H open; if i+H
  lies beyond the decision fold's LAST grid day, the position exits at the
  fold's last grid bar open (FORCE_FLAT_FOLD_BOUNDARY) — per the source
  force_flat_law "positions never span a fold boundary; forced exit at the
  fold's last grid day" (ng1 run_contract folds block via the identity
  extract fold_boundaries.force_flat_law) and the dispatch reading
  "exit at the last grid bar of the decision's fold" (NOT the first bar of
  the next fold). Sub-case: if the entry bar IS the fold's last grid bar
  there is no room for even one held cell before the boundary — the entry
  is a DROPPED_TAIL_ENTRY, counted, no position, no costs (per the
  identity exit_rule "post-window (tail) entries dropped and counted";
  the fold force-flat law was inherited Stage-A law never exercised for
  this family in source — identity fold_boundaries.caveat — so this
  sub-case has no source precedent and fails closed, never degenerate).
  Missing-data: fail-closed everywhere — missing grid bar for entry/exit
  -> the trade is UNMEASURED (counted, never imputed); missing decision
  day -> NO_DECISION_DAY (counted); duplicate (economy, obs-month) events
  raise and nothing is built; stored-vs-recomputed ratio mismatch raises.
  Netting: overlapping same-pair exposure cells net sign-of-sum, NEVER 0
  (sum > 0 -> +1 else -1 per the identity tie_breaking_law transcription
  of the ng1 cell law); net collisions counted. Exposed as the derived
  ``schedule_cells`` artifact of build_positions (the D2 novelty book was
  the exposure-schedule artifact; this lane's rows are per-position).

Grid law disclosure (ambiguity #1, disclosed not hidden): the frozen law
pins the decision grid at the 1,842-day four-pair COMMON grid (2018-04-04
..2025-04-30; GBPUSD the binding leg). The pinned four-pair spot bytes are
not staged in this lane; the lane's BOUND spot input is the USDCAD-only
repull, whose weekday calendar is the 1,846-day own calendar (by-year
exact vs the committed census; 38 new-surface weekend provider rows
excluded by the frozen grid law). The engine therefore builds the grid as
"the bound USDCAD calendar intersected to weekdays in S0" per the dispatch
sentence, carries the frozen 1842/1846 census constants, and
``construction_check`` reports the +4-day delta (2019: +1, 2025: +3) with
the no-effect demonstration: every bound event's v2 year (2018/2022/2024)
has IDENTICAL by-year counts in both censuses, so D(e)/entry/exit DATES —
and therefore every per-position row — are provably identical under either
grid. Hold-indexing disclosure (ambiguity #2): the D2 novelty book
anchored exposure cells at D (first anchor exposure day 2018-10-10 == D);
this lane's position artifact anchors the 5 held cells at the entry bar
i = D+1 per the dispatch sentence "entry fill at the NEXT grid bar's open
after D; hold H=5 grid days; exit fill at bar i+H open". Under the
alternative D-anchored reading every exit fill would be one grid bar
earlier (D+5 instead of D+6 open).

PUBLIC API SURFACE (fixed, documented, introspection-enforced by the
golden tests — any other public module attribute is a violation):

PUBLIC_API = (
    "ALLOW_SCORE",
    "BLOCKED_DATA",
    "CELL_ID",
    "COMMON_GRID_BY_YEAR",
    "COMMON_GRID_DAYS",
    "COST_BPS_PER_SIDE",
    "COST_CEILING_BPS",
    "COST_TIERS",
    "DECISION_ROW_COLUMNS",
    "FOLDS",
    "FOLD_FORCE_FLAT",
    "H_GRID_DAYS",
    "OWN_GRID_BY_YEAR",
    "OWN_GRID_DAYS",
    "POSITION_ROW_COLUMNS",
    "PRIMARY_TIER",
    "PUBLIC_API",
    "REFUSES_PRELAUNCH",
    "S0_END",
    "S0_START",
    "S1_ACCESS_DENIED",
    "UNIVERSE",
    "build_benchmark",
    "build_grid",
    "build_positions",
    "construction_check",
    "load_bars",
    "load_events",
    "score_cells",
)

There are NO tuning knobs: every construction constant below is a frozen
verbatim constant from the cited contracts/identity/binding (grid window,
H, tier ladder, fold months, census counts). ``FOLDS`` and ``COST_TIERS``
are immutable (mappingproxy). Builder signatures are exactly
``build_positions(events, grid, bars)`` / ``build_benchmark(position_set)``.
"""

import bisect as _bisect
import datetime as _dt
import hashlib as _hashlib
import json as _json
import math as _math
from pathlib import Path as _Path
from types import MappingProxyType as _MappingProxyType

import cells_registry as _cells_registry

# Exactly-three enforcement: the engine cannot even be imported unless the
# shared registry is exactly {SFNG2-A4-P1, FXNG3-A4-P1, CNG2-A5-P1}.
_cells_registry.assert_registry_intact()
_cells_registry.validate_cell_id("FXNG3-A4-P1")

__all__ = (
    "ALLOW_SCORE",
    "BLOCKED_DATA",
    "CELL_ID",
    "COMMON_GRID_BY_YEAR",
    "COMMON_GRID_DAYS",
    "COST_BPS_PER_SIDE",
    "COST_CEILING_BPS",
    "COST_TIERS",
    "DECISION_ROW_COLUMNS",
    "FOLDS",
    "FOLD_FORCE_FLAT",
    "H_GRID_DAYS",
    "OWN_GRID_BY_YEAR",
    "OWN_GRID_DAYS",
    "POSITION_ROW_COLUMNS",
    "PRIMARY_TIER",
    "PUBLIC_API",
    "REFUSES_PRELAUNCH",
    "S0_END",
    "S0_START",
    "S1_ACCESS_DENIED",
    "UNIVERSE",
    "build_benchmark",
    "build_grid",
    "build_positions",
    "construction_check",
    "load_bars",
    "load_events",
    "score_cells",
)


# --------------------------------------------------------------------------
# Frozen identity constants (three_cell_contract.json cell FXNG3-A4-P1)
# --------------------------------------------------------------------------

CELL_ID = "FXNG3-A4-P1"
UNIVERSE = ("USDCAD",)  # USDCAD ONLY (anchor universe law)

S0_START = "2018-04-04"  # S0 window (ng2 S0_WINDOW, frozen)
S0_END = "2025-04-30"

H_GRID_DAYS = 5  # DEFAULT_HOLD = 5 (books.py line 77); exit fill at i+H

# Folds frozen inherited Stage-A law (ng1 run_contract folds block via the
# identity extract fold_boundaries; three_cell_contract fold_boundaries).
FOLDS = _MappingProxyType({
    "F1": ("2018-04", "2020-06"),
    "F2": ("2020-07", "2022-10"),
    "F3": ("2022-11", "2025-04"),
})
FOLD_FORCE_FLAT = True

# Frozen grid census constants (committed spot_grid_census.json, digest
# 42612576... == identity pin): USDCAD own weekday calendar and the
# four-pair COMMON grid (GBPUSD binding leg).
OWN_GRID_DAYS = 1846
OWN_GRID_BY_YEAR = _MappingProxyType({
    "2018": 194, "2019": 261, "2020": 262, "2021": 261,
    "2022": 260, "2023": 260, "2024": 262, "2025": 86,
})
COMMON_GRID_DAYS = 1842
COMMON_GRID_BY_YEAR = _MappingProxyType({
    "2018": 194, "2019": 260, "2020": 262, "2021": 261,
    "2022": 260, "2023": 260, "2024": 262, "2025": 83,
})

# Frozen cost ladder (cost_contract.json FXNG3-A4-P1): flat 1.5 bps/side
# proxy x {1.0, 1.5, 2.0}; tier 2.0 PRIMARY; charged once per fill;
# 72 positions x 2 fills; ceiling 432.0 bps/unit-notional at tier 2.0
# (source arithmetic preserved: 72 * 2 * 3.0).
COST_BPS_PER_SIDE = 1.5
COST_TIERS = _MappingProxyType({
    "1.0": _MappingProxyType({"bps_per_side": 1.5}),
    "1.5": _MappingProxyType({"bps_per_side": 2.25}),
    "2.0": _MappingProxyType({"bps_per_side": 3.0}),
})
PRIMARY_TIER = "2.0"
COST_CEILING_BPS = 432.0  # 72 * 2 * 3.0 (frozen source arithmetic)

POSITION_ROW_COLUMNS = (
    "event_id", "obs_month", "v2_availability_day", "R", "r_pp", "D", "d",
    "entry_day", "exit_day", "fold", "hold_days",
    "entry_open", "exit_open", "gross", "costs", "net", "status",
)
# Back-compat alias for the dispatch's per-position row request.
DECISION_ROW_COLUMNS = POSITION_ROW_COLUMNS

# The fixed public API surface (introspection-enforced by the golden tests).
PUBLIC_API = (
    "ALLOW_SCORE",
    "BLOCKED_DATA",
    "CELL_ID",
    "COMMON_GRID_BY_YEAR",
    "COMMON_GRID_DAYS",
    "COST_BPS_PER_SIDE",
    "COST_CEILING_BPS",
    "COST_TIERS",
    "DECISION_ROW_COLUMNS",
    "FOLDS",
    "FOLD_FORCE_FLAT",
    "H_GRID_DAYS",
    "OWN_GRID_BY_YEAR",
    "OWN_GRID_DAYS",
    "POSITION_ROW_COLUMNS",
    "PRIMARY_TIER",
    "PUBLIC_API",
    "REFUSES_PRELAUNCH",
    "S0_END",
    "S0_START",
    "S1_ACCESS_DENIED",
    "UNIVERSE",
    "build_benchmark",
    "build_grid",
    "build_positions",
    "construction_check",
    "load_bars",
    "load_events",
    "score_cells",
)

_POSITION_SET_SCHEMA = "fxng3_engine_position_set@1"
_LABEL = (
    "NON_GOVERNING_DIAGNOSTIC REPLAY_NOT_PROSPECTIVE — per-position rows "
    "only; no aggregate PnL/expectancy is computed by this engine "
    "(score_cells refuses prelaunch)"
)
_FOLDS_NOTE = (
    "FOLDS_FROZEN_F1_F2_F3_FORCE_FLAT: F1 2018-04..2020-06, F2 "
    "2020-07..2022-10, F3 2022-11..2025-04; force-flat AT boundaries — a "
    "position never spans a fold boundary and exits at the decision fold's "
    "LAST grid bar (force_flat_law: ng1 run_contract folds block via the "
    "identity extract; dispatch reading 'exit at the last grid bar of the "
    "decision's fold')"
)
_GRID_NOTE = (
    "grid = the bound USDCAD calendar intersected to weekdays in "
    "2018-04-04..2025-04-30 (weekend provider surface rows excluded by the "
    "frozen grid law); frozen census: own 1846 days, four-pair COMMON grid "
    "1842 days (GBPUSD binding leg) — the +4-day delta is 2019/2025-only "
    "and provably cannot move any bound event's D/entry/exit dates "
    "(construction_check demonstrates this)"
)


# --------------------------------------------------------------------------
# Fail-closed exception types
# --------------------------------------------------------------------------

class REFUSES_PRELAUNCH(RuntimeError):
    """Aggregate outcome computation attempted before orchestrator GO."""


class S1_ACCESS_DENIED(PermissionError):
    """Any path touching '/S1/' or 's1_' data roots is denied (S1 SEALED)."""


class BLOCKED_DATA(RuntimeError):
    """Bound-data defect: the engine fails closed, never imputes."""


# Module-level GO flag. ONLY the orchestrator may set fxng3_engine.ALLOW_SCORE
# = True at GO time. This implementation lane never sets it.
ALLOW_SCORE = False


def score_cells(*args, **kwargs):
    """REFUSES to compute aggregate PnL/expectancy in this lane.

    Raises REFUSES_PRELAUNCH unless the orchestrator has set the module-level
    ALLOW_SCORE flag at GO time. Even with the flag set, this lane provides
    no aggregate implementation (NotImplementedError): scoring belongs to the
    orchestrator's single atomic E-phase job, never to an implementation lane.
    """
    if not ALLOW_SCORE:
        raise REFUSES_PRELAUNCH(
            "REFUSES_PRELAUNCH: aggregate PnL/expectancy computation is "
            "locked in the implementation lane; fxng3_engine builds "
            "per-position rows only. ALLOW_SCORE may be set only by the "
            "orchestrator at GO time (cycle D2-CURIOSITY-V1, "
            "NON_GOVERNING_DIAGNOSTIC)."
        )
    raise NotImplementedError(
        "score_cells has no implementation in the implementation lane; "
        "aggregate scoring runs only in the orchestrator's atomic E-phase job."
    )


# --------------------------------------------------------------------------
# S1 denial + digest helpers
# --------------------------------------------------------------------------

def _deny_s1(path):
    """Raise S1_ACCESS_DENIED for any path containing '/S1/' or 's1_'."""
    s = str(path).lower()
    if "/s1/" in s or "s1_" in s:
        raise S1_ACCESS_DENIED(
            "S1_ACCESS_DENIED: path %r touches a sealed S1 data root; S1 is "
            "SEALED_UNTOUCHED for every asset in cycle D2-CURIOSITY-V1 "
            "(plans/PLAN_d2_curiosity_v1.md section 0)" % (str(path),)
        )


def _verify_digest(data, expected_sha256, path):
    observed = _hashlib.sha256(data).hexdigest()
    if observed != str(expected_sha256).lower():
        raise ValueError(
            "DIGEST_MISMATCH for %r: expected %s, observed %s (fail-closed)"
            % (str(path), expected_sha256, observed)
        )


# --------------------------------------------------------------------------
# Loaders (bound derived events + bound USDCAD daily bars)
# --------------------------------------------------------------------------

def load_events(path, expected_sha256=None):
    """Load the bound derived restricted-event stream (the 72 events).

    Fail-closed (identity missing_data_law): duplicate obs_month events
    raise and nothing is built; a non-first-print (backfill) event raises
    (the bound stream must already be the RESTRICTED stream); the engine
    recomputes R = I_v2/I_v1 - 1 from the bound v1/v2 values and raises on
    any mismatch with the stored bound ratio (no later vintage is ever
    read; both values strictly inside their own realtime windows is a
    property of the bound upstream stream, re-asserted here via the
    v2_availability_day == v2 day equality law). Optional digest pin
    verification. S1 denial runs before any file access.
    """
    _deny_s1(path)
    data = _Path(path).read_bytes()
    if expected_sha256 is not None:
        _verify_digest(data, expected_sha256, path)
    raw = _json.loads(data)
    if not isinstance(raw, dict) or not isinstance(raw.get("restricted_events"), list):
        raise BLOCKED_DATA(
            "events file %r malformed: no restricted_events list (fail-closed)"
            % (str(path),)
        )
    events = []
    seen = set()
    for e in raw["restricted_events"]:
        for field in ("obs_month", "v1", "v2", "v2_availability_day",
                      "ratio", "first_print_in_realtime_era"):
            if field not in e:
                raise BLOCKED_DATA(
                    "event missing field %r in %r (fail-closed)" % (field, str(path))
                )
        obs_month = str(e["obs_month"])
        if obs_month in seen:
            raise BLOCKED_DATA(
                "duplicate restricted (economy, obs-month) event %r in %r: "
                "raise and nothing is built (identity missing_data_law)"
                % (obs_month, str(path))
            )
        seen.add(obs_month)
        if e["first_print_in_realtime_era"] is not True:
            raise BLOCKED_DATA(
                "event %r is not first_print_in_realtime_era: the bound file "
                "must already be the RESTRICTED stream (fail-closed)" % (obs_month,)
            )
        v1_day, v1_val = str(e["v1"][0]), float(e["v1"][1])
        v2_day, v2_val = str(e["v2"][0]), float(e["v2"][1])
        if str(e["v2_availability_day"]) != v2_day:
            raise BLOCKED_DATA(
                "event %r: v2_availability_day %r != v2 day %r (fail-closed)"
                % (obs_month, str(e["v2_availability_day"]), v2_day)
            )
        stored = float(e["ratio"])
        recomputed = v2_val / v1_val - 1.0
        if recomputed != stored:
            raise BLOCKED_DATA(
                "event %r: recomputed R %r != stored bound ratio %r "
                "(fail-closed; no silent substitution)" % (obs_month, recomputed, stored)
            )
        events.append({
            "event_id": obs_month,
            "obs_month": obs_month,
            "v1_day": v1_day,
            "v1_value": v1_val,
            "v2_day": v2_day,
            "v2_value": v2_val,
            "v2_availability_day": v2_day,
            "R": recomputed,
            "r_pp": 100.0 * recomputed,  # books.py line 192 convention
        })
    if not events:
        raise BLOCKED_DATA("events file %r has an empty restricted stream (fail-closed)" % (str(path),))
    return events


def load_bars(path, expected_sha256=None):
    """Load the bound USDCAD Twelve Data 1day repull into {date: bar}.

    Bars carry string OHLC in the bound file; converted to float here.
    Fail-closed: duplicate dates, missing OHLC fields, non-finite or
    non-positive open/close raise (BLOCKED_DATA). Weekend provider surface
    rows are LOADED (recorded per-date) — the frozen grid law excludes
    them at grid construction, not at load. Optional digest pin
    verification. S1 denial runs before any file access.
    """
    _deny_s1(path)
    data = _Path(path).read_bytes()
    if expected_sha256 is not None:
        _verify_digest(data, expected_sha256, path)
    raw = _json.loads(data)
    if not isinstance(raw, dict) or not isinstance(raw.get("bars"), list):
        raise BLOCKED_DATA(
            "bars file %r malformed: no bars list (fail-closed)" % (str(path),)
        )
    bars = {}
    for b in raw["bars"]:
        day = str(b.get("datetime", ""))
        if len(day) != 10:
            raise BLOCKED_DATA("malformed bar datetime %r in %r (fail-closed)" % (day, str(path)))
        if day in bars:
            raise BLOCKED_DATA("duplicate bar date %s in %r (fail-closed)" % (day, str(path)))
        try:
            o = float(b["open"])
            h = float(b["high"])
            l = float(b["low"])
            c = float(b["close"])
        except (KeyError, TypeError, ValueError) as exc:
            raise BLOCKED_DATA(
                "bar %s missing/non-numeric OHLC in %r (fail-closed): %r" % (day, str(path), exc)
            )
        if not (_math.isfinite(o) and o > 0.0 and _math.isfinite(c) and c > 0.0):
            raise BLOCKED_DATA(
                "bar %s has non-plausible open/close in %r (fail-closed)" % (day, str(path))
            )
        bars[day] = {"open": o, "high": h, "low": l, "close": c}
    if not bars:
        raise BLOCKED_DATA("bars file %r is empty (fail-closed)" % (str(path),))
    return bars


def build_grid(bars):
    """Frozen grid law: weekday dates of the bound bars inside S0.

    grid = sorted weekday dates d with S0_START <= d <= S0_END (weekend
    provider surface rows deterministically excluded — the 38 new-surface
    rows in the bound repull never enter the grid). Fail-closed: duplicate
    dates cannot occur (loader law); non-date keys raise.
    """
    days = []
    excluded_weekend = 0
    for day in bars:
        try:
            d = _dt.date.fromisoformat(day)
        except ValueError:
            raise ValueError("build_grid: non-ISO date key %r (fail-closed)" % (day,))
        if not (S0_START <= day <= S0_END):
            continue
        if d.weekday() >= 5:
            excluded_weekend += 1
            continue
        days.append(day)
    days.sort()
    if not days:
        raise ValueError("build_grid: empty grid (fail-closed)")
    return days


# --------------------------------------------------------------------------
# Internals (private)
# --------------------------------------------------------------------------

def _check_grid_shape(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        raise ValueError("grid must be a non-empty list of YYYY-MM-DD weekday dates")
    prev = None
    for day in grid:
        if not isinstance(day, str) or len(day) != 10:
            raise ValueError("grid date %r is not a YYYY-MM-DD string" % (day,))
        if prev is not None and not (prev < day):
            raise ValueError("grid is not strictly ascending at %s (fail-closed)" % (day,))
        if _dt.date.fromisoformat(day).weekday() >= 5:
            raise ValueError("grid date %s is a weekend (frozen grid law violated)" % (day,))
        if not (S0_START <= day <= S0_END):
            raise ValueError("grid date %s outside the frozen S0 window" % (day,))
        prev = day


def _fold_of(day):
    """Fold of a decision day, by frozen month boundaries."""
    month = day[:7]
    for fid in ("F1", "F2", "F3"):
        lo, hi = FOLDS[fid]
        if lo <= month <= hi:
            return fid
    raise ValueError(
        "decision day %s (month %s) outside the frozen folds %s (fail-closed)"
        % (day, month, dict(FOLDS))
    )


def _fold_last_index(grid, fold_id):
    """Index of the decision fold's LAST grid day (force-flat exit bar)."""
    lo, hi = FOLDS[fold_id]
    last = None
    for idx, day in enumerate(grid):
        if lo <= day[:7] <= hi:
            last = idx
    if last is None:
        raise ValueError("fold %s has no grid days (fail-closed)" % (fold_id,))
    return last


def _valid_open(bars, day):
    """A grid day's fillable open: present and finite > 0, else None."""
    bar = bars.get(day)
    if bar is None:
        return None
    o = bar.get("open")
    if o is None or not (_math.isfinite(o) and o > 0.0):
        return None
    return o


def _costs_per_position():
    """2 fills x (1.5 bps/side x tier 2.0 PRIMARY) = 6.0 bps as a fraction."""
    bps_per_fill = COST_TIERS[PRIMARY_TIER]["bps_per_side"]
    return 2.0 * bps_per_fill / 10000.0


def _net_sign(signs):
    """Sign-of-sum netting, NEVER 0 (identity tie_breaking_law: sum > 0 ->
    +1 else -1). Returns (net_sign, had_conflict)."""
    s = sum(signs)
    conflict = (1 in signs) and (-1 in signs)
    return (1 if s > 0 else -1), conflict


# --------------------------------------------------------------------------
# Position-set builder (per-position rows; the only artifact of this lane)
# --------------------------------------------------------------------------

def build_positions(events, grid, bars):
    """FXNG3-A4-P1 verbatim per-position builder.

    events: normalized restricted events (load_events shape or the same
            fields as dicts).
    grid:   the decision grid (build_grid shape — ascending weekday dates
            in S0).
    bars:   {date: {'open': float, ...}} (load_bars shape).

    Per event: D(e) = first grid day STRICTLY after v2_availability_day
    (EOD law); d = sign(R) (R<0 -> +1 LONG USDCAD, R>0 -> -1, exact zero
    -> SIGN_ZERO_SKIP counted); i = index of the entry bar = the next grid
    bar after D (STRICT_NEXT_BAR); exit fill at bar i+H open (H = 5; the
    exit bar is NOT a held cell), force-flat to the decision fold's LAST
    grid bar when i+H lies beyond it; missing/unfillable bars fail closed
    as counted UNMEASURED rows; D on the fold's last grid day (or an entry
    bar equal to it) is a DROPPED_TAIL_ENTRY, counted (positions never
    span a fold boundary). Costs: 6.0 bps per position at tier 2.0
    PRIMARY, debited only on rows with actual fills.

    Returns a position-set dict: per-position rows + derived schedule
    cells (sign-of-sum netting, never 0) + counts + labels. NO aggregate
    PnL/expectancy is computed anywhere.
    """
    _cells_registry.validate_cell_id(CELL_ID)
    _check_grid_shape(grid)
    if not isinstance(bars, dict) or not bars:
        raise ValueError("bars must be a non-empty {date: bar} dict")
    if not isinstance(events, (list, tuple)) or not events:
        raise ValueError("events must be a non-empty list of restricted events")

    day_index = {day: k for k, day in enumerate(grid)}
    costs = _costs_per_position()

    rows = []
    cell_signs = {}  # grid day -> [signs of held cells] (schedule artifact)
    counts = {
        "MEASURED": 0,
        "FORCE_FLAT_FOLD_BOUNDARY": 0,
        "SIGN_ZERO_SKIP": 0,
        "MISSING_ENTRY_BAR": 0,
        "MISSING_EXIT_BAR": 0,
        "DROPPED_TAIL_ENTRY": 0,
        "NO_DECISION_DAY": 0,
    }

    # Deterministic order: (v2 availability day, obs_month).
    ordered = sorted(events, key=lambda e: (str(e["v2_availability_day"]), str(e["obs_month"])))

    for e in ordered:
        row = {col: None for col in POSITION_ROW_COLUMNS}
        row["event_id"] = str(e.get("event_id", e["obs_month"]))
        row["obs_month"] = str(e["obs_month"])
        row["v2_availability_day"] = str(e["v2_availability_day"])
        r = float(e["R"])
        row["R"] = r
        row["r_pp"] = 100.0 * r

        def finish(status):
            counts[status] += 1
            row["status"] = status
            rows.append(row)

        # (1) Strictly-after clock: D(e) = first grid day STRICTLY after
        # EOD(v2.realtime_start) — a same-date 16:00-NY decision can never
        # see the v2 (leak protection carried entirely by this clock).
        k = _bisect.bisect_right(grid, row["v2_availability_day"])
        if k >= len(grid):
            finish("NO_DECISION_DAY")
            continue
        d_day = grid[k]
        row["D"] = d_day

        # (2) Direction: sign(R); exact zero -> skip, counted.
        if r == 0.0:
            finish("SIGN_ZERO_SKIP")
            continue
        row["d"] = 1 if r < 0.0 else -1  # R<0 -> LONG USDCAD (+1)

        # (3) Fold of the DECISION day; the fold's last grid day.
        fold_id = _fold_of(d_day)
        row["fold"] = fold_id
        l_idx = _fold_last_index(grid, fold_id)

        # (4) Entry fill: STRICT_NEXT_BAR — the next grid bar's open after D.
        i = k + 1
        if i >= len(grid):
            finish("MISSING_ENTRY_BAR")
            continue
        if i >= l_idx:
            # Entry bar would be at or beyond the fold's last grid day:
            # positions never span a fold boundary; the tail entry is
            # dropped and counted (identity exit_rule).
            finish("DROPPED_TAIL_ENTRY")
            continue
        entry_day = grid[i]
        entry_open = _valid_open(bars, entry_day)
        if entry_open is None:
            finish("MISSING_ENTRY_BAR")
            continue
        row["entry_day"] = entry_day
        row["entry_open"] = entry_open

        # (5) Exit fill: bar i+H open; force-flat AT the fold boundary.
        exit_idx = i + H_GRID_DAYS
        if exit_idx > l_idx:
            exit_idx = l_idx
            status = "FORCE_FLAT_FOLD_BOUNDARY"
        else:
            status = "MEASURED"
        exit_day = grid[exit_idx]
        exit_open = _valid_open(bars, exit_day)
        if exit_open is None:
            finish("MISSING_EXIT_BAR")
            continue
        row["exit_day"] = exit_day
        row["exit_open"] = exit_open
        row["hold_days"] = exit_idx - i

        # (6) PnL per position + frozen cost debit (once per fill, 2 fills).
        gross = row["d"] * (exit_open / entry_open - 1.0)
        row["gross"] = gross
        row["costs"] = costs
        row["net"] = gross - costs
        finish(status)

        # (7) Exposure-schedule artifact: held cells i..exit_idx-1 (the
        # exit fill bar is NOT a held cell), netted sign-of-sum never 0.
        for c in range(i, exit_idx):
            cell_signs.setdefault(grid[c], []).append(row["d"])

    # Net the schedule cells (never 0; collisions counted).
    schedule_cells = {}
    net_collisions = 0
    for day in sorted(cell_signs):
        sign, conflict = _net_sign(cell_signs[day])
        if conflict:
            net_collisions += 1
        schedule_cells[day] = sign

    return {
        "schema": _POSITION_SET_SCHEMA,
        "cell_id": CELL_ID,
        "label": _LABEL,
        "universe": list(UNIVERSE),
        "grid_note": _GRID_NOTE,
        "folds": {k: list(v) for k, v in FOLDS.items()},
        "folds_note": _FOLDS_NOTE,
        "fold_force_flat": FOLD_FORCE_FLAT,
        "hold_grid_days": H_GRID_DAYS,
        "cost_tier": PRIMARY_TIER,
        "cost_bps_per_side_ladder": {k: v["bps_per_side"] for k, v in COST_TIERS.items()},
        "cost_bps_round_trip_per_position": {
            t: 2.0 * v["bps_per_side"] for t, v in COST_TIERS.items()
        },
        "cost_ceiling_bps_unit_notional": COST_CEILING_BPS,
        "counts": counts,
        "net_collisions": net_collisions,
        "schedule_cells": schedule_cells,
        "rows": rows,
    }


# --------------------------------------------------------------------------
# Descriptive benchmark builder (DESCRIPTIVE_ONLY — never fold evidence)
# --------------------------------------------------------------------------

def build_benchmark(position_set):
    """Buy-and-hold USDCAD over the same held cells (DESCRIPTIVE_ONLY).

    Per measured/force-flat position, the long return over the identical
    entry/exit opens: bh_gross = exit_open/entry_open - 1. No direction,
    no costs, no aggregation — the evaluation contract fixes this
    comparison as DESCRIPTIVE only. Raises on anything that is not this
    engine's position-set shape.
    """
    if not isinstance(position_set, dict) or position_set.get("schema") != _POSITION_SET_SCHEMA:
        raise ValueError("build_benchmark: input is not an fxng3 position-set (fail-closed)")
    rows = []
    for r in position_set["rows"]:
        if r["status"] not in ("MEASURED", "FORCE_FLAT_FOLD_BOUNDARY"):
            continue
        rows.append({
            "event_id": r["event_id"],
            "entry_day": r["entry_day"],
            "exit_day": r["exit_day"],
            "entry_open": r["entry_open"],
            "exit_open": r["exit_open"],
            "bh_gross": r["exit_open"] / r["entry_open"] - 1.0,
        })
    return {
        "schema": "fxng3_benchmark_bench@1",
        "cell_id": CELL_ID,
        "label": (
            "DESCRIPTIVE_ONLY buy-and-hold USDCAD over the same held cells "
            "(evaluation_contract benchmark_control_comparison_law "
            "FXNG3-A4-P1); NON_GOVERNING_DIAGNOSTIC — never fold evidence, "
            "never an acceptance battery"
        ),
        "descriptive_only": True,
        "n_rows": len(rows),
        "rows": rows,
    }


# --------------------------------------------------------------------------
# Real-data construction invariants (NO positions, NO PnL, NO returns)
# --------------------------------------------------------------------------

_OUTCOME_FORBIDDEN_KEYS = ("gross", "net", "pnl", "return", "expectancy",
                           "profit_factor", "win", "drawdown")


def construction_check(events_path, bars_path,
                       events_sha256=None, bars_sha256=None):
    """Construction invariants on the REAL bound files — nothing else.

    Asserts (all fail-closed): the bound restricted stream has EXACTLY 72
    events with the by-year (v2 availability day) 8/47/17 split; every
    event is first-print-era; no exact-zero R (all 72 fire); the USDCAD
    grid built from the bound bars has the frozen own-calendar census
    (1846 days, by-year exact, S0 first/last) and reports the disclosed
    +4-day delta vs the frozen 1842-day four-pair COMMON grid with the
    no-effect demonstration (identical by-year counts in every event
    v2-year). The returned dict carries construction invariants ONLY —
    structurally no position/return/PnL fields (enforced below).
    """
    _cells_registry.validate_cell_id(CELL_ID)
    events = load_events(events_path, events_sha256)
    bars = load_bars(bars_path, bars_sha256)

    n = len(events)
    if n != 72:
        raise BLOCKED_DATA("construction_check: restricted stream has %d events, frozen law says 72" % (n,))
    by_year = {}
    for e in events:
        by_year[e["v2_availability_day"][:4]] = by_year.get(e["v2_availability_day"][:4], 0) + 1
    if by_year != {"2018": 8, "2022": 47, "2024": 17}:
        raise BLOCKED_DATA(
            "construction_check: by-year split %s != frozen 8/47/17 (fail-closed)" % (sorted(by_year.items()),)
        )
    if any(e["R"] == 0.0 for e in events):
        raise BLOCKED_DATA("construction_check: exact-zero R present in the bound stream (fail-closed)")
    v2_days = sorted({e["v2_availability_day"] for e in events})

    grid = build_grid(bars)
    grid_by_year = {}
    for day in grid:
        grid_by_year[day[:4]] = grid_by_year.get(day[:4], 0) + 1
    if len(grid) != OWN_GRID_DAYS or grid_by_year != dict(OWN_GRID_BY_YEAR):
        raise BLOCKED_DATA(
            "construction_check: grid %d days %s != frozen USDCAD own-calendar census "
            "(%d days, fail-closed)" % (len(grid), sorted(grid_by_year.items()), OWN_GRID_DAYS)
        )
    if grid[0] != S0_START or grid[-1] != S0_END:
        raise BLOCKED_DATA(
            "construction_check: grid first/last %s/%s != frozen S0 %s/%s"
            % (grid[0], grid[-1], S0_START, S0_END)
        )
    weekend_rows = sum(1 for day in bars if _dt.date.fromisoformat(day).weekday() >= 5)

    # No-effect demonstration: in every event v2-year the own calendar and
    # the COMMON grid have identical by-year counts, so the grid-day
    # SEQUENCE within those years (hence every D(e)/entry/exit date) is
    # identical under either grid.
    event_years = sorted(by_year)
    common_equal_in_event_years = all(
        grid_by_year[y] == COMMON_GRID_BY_YEAR[y] for y in event_years
    )
    if not common_equal_in_event_years:
        raise BLOCKED_DATA(
            "construction_check: own vs COMMON census differ inside an event "
            "v2-year — the disclosed no-effect argument would not hold (fail-closed)"
        )
    delta_by_year = {
        y: grid_by_year.get(y, 0) - COMMON_GRID_BY_YEAR.get(y, 0)
        for y in sorted(set(grid_by_year) | set(COMMON_GRID_BY_YEAR))
    }
    delta_by_year = {y: d for y, d in delta_by_year.items() if d != 0}

    out = {
        "schema": "fxng3_construction_check@1",
        "cell_id": CELL_ID,
        "label": "NON_GOVERNING_DIAGNOSTIC construction invariants ONLY — no positions, no PnL, no returns",
        "events": {
            "n_restricted": n,
            "by_v2_year": by_year,
            "first_print_all": True,
            "exact_zero_R_events": 0,
            "distinct_v2_availability_days": v2_days,
            "ratio_recompute_exact": True,
        },
        "grid": {
            "first": grid[0],
            "last": grid[-1],
            "days_own_calendar": len(grid),
            "by_year_own_calendar": grid_by_year,
            "weekend_surface_rows_excluded": weekend_rows,
            "common_grid_frozen_days": COMMON_GRID_DAYS,
            "delta_vs_common_grid_by_year": delta_by_year,
            "delta_note": (
                "the 1842-day COMMON grid (four-pair intersection, GBPUSD "
                "binding leg) is not recomputable from this lane's "
                "USDCAD-only bound bytes; the +4-day delta sits entirely in "
                "2019/2025, where no bound event has a v2 day, and by-year "
                "counts are identical in every event v2-year — so every "
                "D(e)/entry/exit date is provably identical under either grid"
            ),
            "no_effect_demonstration": True,
        },
    }
    # Structural refusal: no outcome field may escape this function.
    flat = _json.dumps(out).lower()
    for bad in _OUTCOME_FORBIDDEN_KEYS:
        if '"%s"' % (bad,) in flat:
            raise BLOCKED_DATA(
                "construction_check attempted to emit an outcome-like field %r "
                "(structural no-outcome law)" % (bad,)
            )
    return out
