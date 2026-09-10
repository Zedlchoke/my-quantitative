"""FOREX-FREE-V9 shared family machinery: universe constants, the daily
16:00-NY decision grid, decision-instant fills from the staged daily spot
snapshot, the frozen per-pair state machine and the mechanical fold split.

Frozen mechanics implemented here (proposals FXFV9-A5-P1/-P2 + p3 freeze):

* UNIVERSE   GBPUSD, USDCAD, AUDUSD, NZDUSD (funded pairs only, P0 census).
* SIGN MAP   long home currency on driver >= 0:
                 GBPUSD +1 (long home = long pair)
                 AUDUSD +1, NZDUSD +1
                 USDCAD -1 (long home = SHORT pair)
* CLOCK      first daily 16:00 America/New_York (DST-correct) after each
             binding instant; one decision per clock per pair; the state
             persists on the universal weekday grid (FX 24/5) -- NO window
             opens or closes at any release instant.
* FILLS      at the decision-instant close from the staged daily spot
             snapshot (data_raw/forex_free_v9_spot/, Twelve Data time_series
             1day format; V9 re-staging of the lost V1 H1 snapshot).
* STATE MACHINE (both families)
     FLAT  --abs(driver) >= entry-->  IN(side)   [at the decision clock,
                when flat and the driver is defined]
     IN    --hold >= min_hold AND (abs(driver) <= exit_band OR driver
                crossed zero against the entry side)--> FLAT ("hysteresis"
                / "sign_flip")
     IN    --hold >= max_hold (63)--> FLAT ("time_cap"; immediate
                re-entry at the NEXT clock if activation re-fires)
     max one position per pair at any time; a pair that exits at clock j
     never re-enters at clock j; a position still open after the last
     usable clock is closed at the last available fill ("terminal",
     counted, never dropped); a missing exit fill keeps the position open
     (counted, never fabricated).
* WARMUP     in_S0 burn = 0 clocks (both proposals: warmup is satisfied
             from staged pre-S0 print depth); the usable grid is the full
             decision grid, the driver is None until its state binds.
* FOLDS      3 equal thirds of the usable decision grid, split mechanically
             at run time (indices n//3, 2n//3).

No PnL anywhere in this module.
"""
from __future__ import annotations

import json
import math
import os
from collections import OrderedDict
from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo

from research.assets.forex_free_v9.conditioning import DataBlocked

__all__ = [
    "CYCLE_ID", "PAIRS", "HOME_OF_PAIR", "LONG_HOME_SIGN", "PAIR_AREAS",
    "USD_LEG_SIGN", "NY_TZ", "ny_close_ts", "iso_ts", "load_spot_daily",
    "build_grid", "simulate_arm", "fold_bounds", "fold_of_index",
    "MIN_HOLD_CLOCKS", "MAX_HOLD_CLOCKS", "N_FOLDS", "S0_START", "S0_END",
]

UTC = timezone.utc
NY_TZ = ZoneInfo("America/New_York")

CYCLE_ID = "FOREX-FREE-V9"
DECISION_CLOCK = "daily 16:00 America/New_York (DST-correct via zoneinfo)"

PAIRS = ("GBPUSD", "USDCAD", "AUDUSD", "NZDUSD")
HOME_OF_PAIR = OrderedDict((("GBPUSD", "GB"), ("USDCAD", "CA"),
                            ("AUDUSD", "AU"), ("NZDUSD", "NZ")))
# frozen home sign map (proposal universe.home_sign_map): long home == long
# pair for GBPUSD/AUDUSD/NZDUSD; long home == SHORT pair for USDCAD.
LONG_HOME_SIGN = OrderedDict((("GBPUSD", 1), ("USDCAD", -1),
                              ("AUDUSD", 1), ("NZDUSD", 1)))
# financing attribution (driver bookkeeping input, V7 kernel; accounting
# only, never a signal)
PAIR_AREAS = OrderedDict((("GBPUSD", ("GB", "US")), ("USDCAD", ("US", "CA")),
                          ("AUDUSD", ("AU", "US")), ("NZDUSD", ("NZ", "US"))))
# signed USD-leg of each pair (gate-9 diagnostic input, V7-inherited)
USD_LEG_SIGN = {"GBPUSD": -1, "USDCAD": 1, "AUDUSD": -1, "NZDUSD": -1}

MIN_HOLD_CLOCKS = 5          # soft exits evaluate only after 5 held clocks
MAX_HOLD_CLOCKS = 63         # hard cap: exit + immediate re-entry next clock
N_FOLDS = 3

S0_START = date(2018, 4, 4)
S0_END = date(2025, 7, 24)


def ny_close_ts(day: date) -> datetime:
    """The decision instant: 16:00 America/New_York on ``day`` (DST-correct),
    as UTC."""
    return datetime(day.year, day.month, day.day, 16, 0,
                    tzinfo=NY_TZ).astimezone(UTC)


def iso_ts(t: datetime) -> str:
    return t.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%S+00:00")


# ------------------------------------------------------------------- fills #
def load_spot_daily(price_dir: str, pair: str):
    """Decision-instant closes from the staged daily spot snapshot (Twelve
    Data time_series 1day provider format, values stored newest-first).
    Returns (sorted days, {day: close})."""
    path = os.path.join(price_dir, f"{pair}.json")
    try:
        with open(path) as f:
            d = json.load(f)
    except OSError as exc:
        raise DataBlocked(f"SPOT_SNAPSHOT_MISSING: {path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise DataBlocked(f"SPOT_SNAPSHOT_MALFORMED: {path}: {exc}") from exc
    if d.get("status") != "ok":
        raise DataBlocked(f"SPOT_SNAPSHOT_STATUS: {path}: {d.get('status')}")
    inst: dict[date, float] = {}
    for v in d.get("values", []):
        try:
            day = parse_day(v["datetime"])
            c = float(v["close"])
        except (KeyError, TypeError, ValueError) as exc:
            raise DataBlocked(f"SPOT_ROW_MALFORMED: {path}: {v!r}") from exc
        if not math.isfinite(c) or c <= 0:
            raise DataBlocked(f"SPOT_ROW_NONFINITE: {path}: {v!r}")
        inst[day] = c                    # newest-first storage: keep the
    if not inst:                         # last write = the earliest bar
        raise DataBlocked(f"SPOT_SNAPSHOT_EMPTY: {path}")
    days = sorted(inst)
    return days, {k: inst[k] for k in days}


def parse_day(s: str) -> date:
    y, m, d = str(s).split("-")
    return date(int(y), int(m), int(d))


def build_grid(price_dir: str, s0_start: date = S0_START,
               s0_end: date = S0_END, pairs=PAIRS) -> list:
    """The S0 decision grid: FX 24/5 weekdays in [s0_start, s0_end]
    intersected with every pair's staged daily calendar (a clock without a
    decision-instant close for any pair is not a decision clock --
    fail-closed, deterministic)."""
    common = None
    for pair in pairs:
        days, _closes = load_spot_daily(price_dir, pair)
        s = {d for d in days if s0_start <= d <= s0_end and d.weekday() < 5}
        common = s if common is None else (common & s)
    grid = sorted(common) if common else []
    if not grid:
        raise DataBlocked("EMPTY_GRID")
    return grid


# ------------------------------------------------------------ state machine #
def simulate_arm(driver_by_clock, fills, usable_clocks, side_fn, pairs=PAIRS,
                 entry: float = 0.0, exit_band: float = 0.0,
                 min_hold: int = MIN_HOLD_CLOCKS,
                 max_hold: int = MAX_HOLD_CLOCKS):
    """The frozen per-pair state machine over the usable decision grid.

    driver_by_clock : {date: float | None}   arm driver at each clock
    fills           : {pair: {date: float}}  decision-instant closes
    usable_clocks   : list[date]             decision grid
    side_fn         : (driver, pair) -> +1|-1   frozen direction map

    Transitions in the module docstring.  Returns (decisions, counts).
    Decisions are round-trip records only -- no PnL anywhere.
    """
    decisions: list[dict] = []
    counts = OrderedDict((
        ("usable_clocks", len(usable_clocks)),
        ("entries", 0), ("entries_fill_missing", 0),
        ("exits_hysteresis", 0), ("exits_sign_flip", 0),
        ("exits_time_cap", 0), ("exits_fill_missing", 0),
        ("terminal_closes", 0), ("terminal_closes_no_fill", 0),
    ))
    open_pos: dict[str, dict] = {}

    for idx, d in enumerate(usable_clocks):
        v = driver_by_clock.get(d)
        for pair in pairs:
            st = open_pos.get(pair)
            if st is not None:
                hold = idx - st["entry_idx"]
                reason = None
                if v is not None and hold >= min_hold:
                    if abs(v) <= exit_band:
                        reason = "hysteresis"
                    elif v * st["entry_driver"] < 0.0:
                        reason = "sign_flip"
                if reason is None and hold >= max_hold:
                    reason = "time_cap"
                if reason is None:
                    continue
                px = fills.get(pair, {}).get(d)
                if px is None:
                    counts["exits_fill_missing"] += 1   # stays open (counted)
                    continue
                decisions.append(_record(pair, st, d, px, v, reason, idx))
                counts[f"exits_{reason}"] += 1
                del open_pos[pair]
                continue
            # FLAT (a pair that exited this clock never reaches this branch:
            # the exit branch above `continue`s past same-clock re-entry)
            if v is None or abs(v) < entry:
                continue
            px = fills.get(pair, {}).get(d)
            if px is None:
                counts["entries_fill_missing"] += 1
                continue
            open_pos[pair] = {
                "side": side_fn(v, pair),
                "entry_idx": idx, "entry_day": d, "entry_price": px,
                "entry_driver": v,
            }
            counts["entries"] += 1

    # terminal closes: the book must end complete (no half-open trades)
    for pair in pairs:
        st = open_pos.get(pair)
        if st is None:
            continue
        series = fills.get(pair, {})
        exit_day = None
        for d in reversed(usable_clocks):
            if d in series:
                exit_day = d
                break
        if exit_day is None:
            counts["terminal_closes_no_fill"] += 1
            continue
        decisions.append(_record(pair, st, exit_day, series[exit_day],
                                 driver_by_clock.get(exit_day), "terminal",
                                 None))
        counts["terminal_closes"] += 1
    return decisions, counts


def _record(pair, st, exit_day, exit_price, exit_driver, reason, exit_idx):
    return {
        "pair": pair,
        "side": st["side"],
        "entry_day": st["entry_day"].isoformat(),
        "exit_day": exit_day.isoformat(),
        "entry_ts": iso_ts(ny_close_ts(st["entry_day"])),
        "exit_ts": iso_ts(ny_close_ts(exit_day)),
        "entry_price": st["entry_price"],
        "exit_price": exit_price,
        "entry_driver": st["entry_driver"],
        "exit_driver": exit_driver,
        "hold_clocks": (None if exit_idx is None
                        else exit_idx - st["entry_idx"]),
        "exit_reason": reason,
        "areas": list(PAIR_AREAS[pair]),
    }


# ------------------------------------------------------------------- folds #
def fold_bounds(n_usable: int, n_folds: int = N_FOLDS) -> tuple:
    """Mechanical equal-thirds split of the usable grid (indices)."""
    if n_usable <= 0:
        raise DataBlocked("EMPTY_USABLE_GRID")
    if n_folds != N_FOLDS:
        raise DataBlocked("FOLD_COUNT_FROZEN_AT_3")
    return (n_usable // n_folds, 2 * n_usable // n_folds)


def fold_of_index(idx: int, bounds: tuple) -> int:
    if idx < bounds[0]:
        return 1
    if idx < bounds[1]:
        return 2
    return 3
