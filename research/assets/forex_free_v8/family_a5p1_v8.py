"""FOREX-FREE-V8 family FXFV8-A5-P1 runner -- US inflation-compensation
term-structure dispersion regime (FROZEN at research/control/forex_free_v8_run/
d1/a5-axis3/proposal-1.json + selection_freeze_v8.json).

Verbatim frozen mechanics (implemented exactly; never "improved"):

- conditioning: T10YIE + T5YIE (anchor/neighbour legs) and DGS10 (control),
  daily vintaged series, as-of reconstruction per AX2-C1..C4
  (research.assets.forex_free_v8.conditioning).
- driver:
    anchor    z of slope D(t)=T10YIE-T5YIE over trailing 252 BINDING clocks
    neighbour identical slope, trailing 504 binding clocks (dose-response;
              ONLY the standardization window differs)
    control   z of DGS10 LEVEL over trailing 252 binding clocks (AX2-C8)
  The trailing window is composed of values AS BOUND at their own decision
  clocks (never re-pulled at current vintage); the current value and the
  z are computed inside one as-of snapshot per clock (AX2-C1/C2).
  z uses the population standard deviation (ddof=0; determinism pinned by
  a hand-computed fixture test).
- entry |z| >= 1.0:
    anchor/neighbour: z >= +1 => SHORT USD basket (buy EURUSD AUDUSD NZDUSD
      GBPUSD; sell USDJPY USDCAD USDCHF); z <= -1 => LONG USD basket (mirror)
    control: z >= +1 => LONG USD basket; z <= -1 => SHORT USD basket
- exit |z| <= 0.5 (hysteresis) OR 21 business days max hold, whichever
  first; re-entry allowed at the NEXT clock only; max one position per pair
  at any time; fills at the decision clock's 16:00-NY close from the staged
  H1 snapshot; fixed notional 1 unit per pair.
- warmup: the first 252 binding clocks of S0 are burned; the usable decision
  grid begins at the clock AFTER the 252nd binding clock (~2019-04).
- folds: 3 equal thirds of the usable decision grid, split mechanically at
  run time (indices n//3, 2n//3).

This module produces decision records only.  Costs, financing, books, gates
and diagnostics are driver-owned (exec_driver_v8.py).  No PnL here.
"""
from __future__ import annotations

import glob
import hashlib
import json
import math
import os
from collections import OrderedDict
from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo

from research.assets.forex_free_v8.conditioning import (
    DataBlocked,
    AsOfReconstructor,
    build_grid,
    load_staged_series,
    parse_date,
    zscore,
)

__all__ = [
    "run_arm", "simulate_arm", "compute_driver_series", "ARM_IDS",
    "FAMILY_ID", "PAIRS", "WARMUP", "MAX_HOLD_BD", "ENTRY_Z", "EXIT_Z",
    "arm_frozen_config", "arm_config_digest", "fold_bounds", "fold_of_index",
    "load_decision_closes", "ny_close_ts",
]

UTC = timezone.utc
NY_TZ = ZoneInfo("America/New_York")

CYCLE_ID = "FOREX-FREE-V8"
FAMILY_ID = "FXFV8-A5-P1"
PROPOSAL_ID = "FXFV8-A5-P1"
DECISION_CLOCK = "daily 16:00 America/New_York (DST-correct via zoneinfo)"

ARM_IDS = OrderedDict((
    ("anchor", "anchor_breakeven_slope_z252_21bd"),
    ("neighbour", "neighbour_breakeven_slope_z504_21bd"),
    ("control", "control_dgs10_level_z252_21bd"),
))
Z_WINDOW = {"anchor": 252, "neighbour": 504, "control": 252}
DRIVER_SPEC = {
    "anchor": ("slope", "T10YIE", "T5YIE"),
    "neighbour": ("slope", "T10YIE", "T5YIE"),
    "control": ("level", None, "DGS10"),
}

PAIRS = ("EURUSD", "USDJPY", "USDCAD", "AUDUSD", "NZDUSD", "USDCHF", "GBPUSD")
# usd_sign_map from the frozen proposal: long_pair == short_USD for these
SHORT_USD_PAIRS = frozenset(("EURUSD", "AUDUSD", "NZDUSD", "GBPUSD"))
LONG_USD_PAIRS = frozenset(("USDJPY", "USDCAD", "USDCHF"))

WARMUP = 252                 # in-S0 binding clocks burned before decisions
ENTRY_Z = 1.0                # |z| >= 1.0 activates
EXIT_Z = 0.5                 # |z| <= 0.5 hysteresis exit
MAX_HOLD_BD = 21             # business days (grid clocks) max hold
N_FOLDS = 3

PAIR_AREAS = {   # financing attribution (driver bookkeeping input, V7 kernel)
    "EURUSD": ("EMU", "US"), "GBPUSD": ("GB", "US"), "USDJPY": ("US", "JP"),
    "USDCAD": ("US", "CA"), "AUDUSD": ("AU", "US"), "NZDUSD": ("NZ", "US"),
    "USDCHF": ("US", "CH"),
}
S0_START = date(2018, 4, 4)
S0_END = date(2025, 7, 24)
EXPECTED_GRID_CLOCKS = 1907  # P2 census: daily US fields, full S0


def ny_close_ts(day: date) -> datetime:
    """The decision instant: 16:00 America/New_York on ``day`` (DST-correct),
    as UTC."""
    return datetime(day.year, day.month, day.day, 16, 0,
                    tzinfo=NY_TZ).astimezone(UTC)


def _iso(t: datetime) -> str:
    return t.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%S+00:00")


def side_for_z(arm: str, z: float, pair: str) -> int:
    """Frozen direction map.  Returns +1 (long the pair) / -1 (short the
    pair).  Called only when |z| >= ENTRY_Z.

    anchor/neighbour: z >= +1 => SHORT USD basket (buy EURUSD/AUDUSD/NZDUSD/
    GBPUSD -- the pairs whose long side IS short USD; sell USDJPY/USDCAD/
    USDCHF); z <= -1 => mirror.  control: z >= +1 => LONG USD basket (the
    convenient nominal-yield exposure), i.e. the map inverts.
    """
    short_usd_basket = z >= 0.0
    if arm == "control":
        short_usd_basket = not short_usd_basket   # frozen control inversion
    if pair in SHORT_USD_PAIRS:
        return 1 if short_usd_basket else -1
    return -1 if short_usd_basket else 1


def arm_frozen_config(arm: str) -> dict:
    """The arm's frozen configuration (the exact bytes hashed into
    arm_config_digest).  Every field is frozen by the proposal / p3 freeze."""
    kind, leg_a, leg_b = DRIVER_SPEC[arm]
    return {
        "arm": arm,
        "arm_id": ARM_IDS[arm],
        "cost_ladder": "1.5 bps/side x {1.0, 1.5, 2.0}",
        "decision_clock": DECISION_CLOCK,
        "driver": f"z_{kind}({Z_WINDOW[arm]})",
        "driver_legs": [leg for leg in (leg_a, leg_b) if leg],
        "entry_z": ENTRY_Z,
        "exit_z": EXIT_Z,
        "family_id": FAMILY_ID,
        "folds": {"n_folds": N_FOLDS,
                  "rule": "equal thirds of the usable decision grid"},
        "max_hold_bd": MAX_HOLD_BD,
        "pairs": list(PAIRS),
        "s0_window": [S0_START.isoformat(), S0_END.isoformat()],
        "tier_primary": 2.0,
        "usd_sign_map": {
            "short_usd_pairs": sorted(SHORT_USD_PAIRS),
            "long_usd_pairs": sorted(LONG_USD_PAIRS),
            "control_inverts": arm == "control",
        },
        "warmup_binding_clocks": WARMUP,
        "z_std": "population_ddof0",
    }


def arm_config_digest(arm: str) -> str:
    """sha256 of the arm's frozen config JSON (canonical sort_keys)."""
    blob = json.dumps(arm_frozen_config(arm), sort_keys=True,
                      separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


# --------------------------------------------------------------- driver walk #
def compute_driver_series(recon: AsOfReconstructor, arm: str,
                          return_history: bool = False):
    """Walk the grid once; return (z_by_clock, meta) for the arm.

    At each grid clock d (in order):
      * if d is a binding clock and the current as-of value is not None, the
        value AS BOUND AT d is appended to the trailing history (never
        re-pulled later -- AX2-C1);
      * usable(d) = at least WARMUP binding clocks occurred strictly before d
        (the first 252 binding clocks are burned);
      * z(d) = zscore(history[-W:], current as-of value) when the history
        holds at least W bound values, else None.

    return_history=True additionally returns the as-bound history (tests:
    the never-re-pulled property is asserted against it directly).
    """
    kind, leg_a, leg_b = DRIVER_SPEC[arm]
    w = Z_WINDOW[arm]
    history: list[float] = []
    z_by_clock: dict[date, float | None] = {}
    counts = {"no_value_clocks": 0, "window_short_clocks": 0,
              "zero_dispersion_clocks": 0}
    for d in recon.grid:
        if kind == "slope":
            v = recon.slope_at(d, leg_a, leg_b)
        else:
            v = recon.value_at(leg_b, d)
        bound_now = recon.is_binding_clock(d) and v is not None
        usable = recon.binding_clocks_before(d) >= WARMUP
        if bound_now:
            history.append(v)   # the value AS BOUND at its own clock (AX2-C1)
        if v is None:
            z_by_clock[d] = None
            if usable:
                counts["no_value_clocks"] += 1
            continue
        if not usable:
            z_by_clock[d] = None
            continue
        window = history[-w:]
        if len(window) < w:
            z_by_clock[d] = None
            counts["window_short_clocks"] += 1
            continue
        z = zscore(window, v)
        z_by_clock[d] = z
        if z is None:
            counts["zero_dispersion_clocks"] += 1
    meta = {
        "driver": f"z_{kind}({w})",
        "binding_clocks_total": recon.total_binding_clocks,
        "history_len": len(history),
        "counts": counts,
    }
    if return_history:
        return z_by_clock, meta, history
    return z_by_clock, meta


# ------------------------------------------------------------ state machine #
def simulate_arm(z_by_clock, fills, usable_clocks, arm,
                 max_hold_bd: int = MAX_HOLD_BD,
                 pairs=PAIRS, entry_z: float = ENTRY_Z,
                 exit_z: float = EXIT_Z):
    """The frozen per-pair state machine over the usable decision grid.

    z_by_clock : {date: float | None}   arm driver z at each grid clock
    fills      : {pair: {date: float}}  16:00-NY close per pair per clock
    usable_clocks : list[date]          post-warmup decision grid

    Transitions (frozen): FLAT --|z| >= entry_z|--> IN(side); IN --|z| <=
    exit_z (hysteresis) OR hold >= max_hold_bd (time cap)--> FLAT; a pair
    that exits at clock j cannot re-enter before clock j+1; at most one
    position per pair at any time; a position still open after the last
    usable clock is closed at the last available fill (terminal, counted).

    Returns (decisions, counts).  No PnL anywhere.
    """
    decisions: list[dict] = []
    counts = OrderedDict((
        ("usable_clocks", len(usable_clocks)),
        ("entries", 0), ("entries_fill_missing", 0),
        ("exits_hysteresis", 0), ("exits_time_cap", 0),
        ("exits_fill_missing", 0), ("terminal_closes", 0),
        ("terminal_closes_no_fill", 0),
    ))
    open_pos: dict[str, dict] = {}
    last_clock = usable_clocks[-1] if usable_clocks else None

    for idx, d in enumerate(usable_clocks):
        z = z_by_clock.get(d)
        for pair in pairs:
            st = open_pos.get(pair)
            if st is not None:
                exit_now = False
                reason = None
                if z is not None and abs(z) <= exit_z:
                    exit_now, reason = True, "hysteresis"
                elif idx - st["entry_idx"] >= max_hold_bd:
                    exit_now, reason = True, "time_cap"
                if not exit_now:
                    continue
                px = fills.get(pair, {}).get(d)
                if px is None:
                    counts["exits_fill_missing"] += 1  # stays open (counted)
                    continue
                decisions.append(_record(pair, st, d, px, z, reason, idx))
                counts[f"exits_{reason}"] += 1
                del open_pos[pair]
                continue
            # FLAT (a pair that exited this clock never reaches this branch:
            # the `continue` above skips same-clock re-entry)
            if z is None or abs(z) < entry_z:
                continue
            px = fills.get(pair, {}).get(d)
            if px is None:
                counts["entries_fill_missing"] += 1
                continue
            open_pos[pair] = {
                "side": side_for_z(arm, z, pair),
                "entry_idx": idx, "entry_day": d, "entry_price": px,
                "entry_z": z,
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
                                 z_by_clock.get(exit_day), "terminal", None))
        counts["terminal_closes"] += 1
    return decisions, counts


def _record(pair, st, exit_day, exit_price, exit_z, reason, exit_idx):
    return {
        "pair": pair,
        "side": st["side"],
        "entry_day": st["entry_day"].isoformat(),
        "exit_day": exit_day.isoformat(),
        "entry_ts": _iso(ny_close_ts(st["entry_day"])),
        "exit_ts": _iso(ny_close_ts(exit_day)),
        "entry_price": st["entry_price"],
        "exit_price": exit_price,
        "entry_z": st["entry_z"],
        "exit_z": exit_z,
        "hold_clocks": (None if exit_idx is None
                        else exit_idx - st["entry_idx"]),
        "exit_reason": reason,
        "areas": PAIR_AREAS[pair],
    }


# ------------------------------------------------------------------- folds #
def fold_bounds(n_usable: int, n_folds: int = N_FOLDS) -> tuple[int, ...]:
    """Mechanical equal-thirds split of the usable grid (indices)."""
    if n_usable <= 0:
        raise DataBlocked("EMPTY_USABLE_GRID")
    if n_folds != N_FOLDS:
        raise DataBlocked("FOLD_COUNT_FROZEN_AT_3")
    return (n_usable // n_folds, 2 * n_usable // n_folds)


def fold_of_index(idx: int, bounds: tuple[int, ...]) -> int:
    if idx < bounds[0]:
        return 1
    if idx < bounds[1]:
        return 2
    return 3


# ------------------------------------------------------------------ loaders #
_H1_CACHE: dict = {}
_DC_CACHE: dict = {}


def load_h1(price_dir: str, pair: str):
    """(sorted bar datetimes UTC, {datetime: close}) from the staged 1h
    snapshot files (V7 loader pattern; provider format forex_free_v1)."""
    key = (price_dir, pair)
    if key in _H1_CACHE:
        return _H1_CACHE[key]
    rows = []
    for fp in sorted(glob.glob(os.path.join(price_dir,
                                            f"{pair}_1h_*_a.json"))):
        with open(fp) as f:
            d = json.load(f)
        if d.get("status") != "ok":
            continue
        for v in d.get("values", []):
            rows.append((datetime.strptime(v["datetime"], "%Y-%m-%d %H:%M:%S")
                         .replace(tzinfo=UTC), float(v["close"])))
    if not rows:
        raise DataBlocked(f"NO_H1_DATA: {pair}")
    rows.sort()
    out = ([r[0] for r in rows], dict(rows))
    _H1_CACHE[key] = out
    return out


def load_decision_closes(price_dir: str, pair: str):
    """16:00 America/New_York completed weekday closes from the staged H1
    snapshot (house standard; DST-correct -- a bar qualifies only when its
    America/New_York local time is exactly 16:00 on a weekday).
    Returns (sorted days, {day: close})."""
    key = (price_dir, pair)
    if key in _DC_CACHE:
        return _DC_CACHE[key]
    bars, closes = load_h1(price_dir, pair)
    inst: dict[date, tuple[datetime, float]] = {}
    for ts in bars:
        loc = ts.astimezone(NY_TZ)
        if loc.hour == 16 and loc.minute == 0 and loc.weekday() < 5:
            want = ny_close_ts(loc.date())
            c = closes[ts]
            if loc.date() in inst and inst[loc.date()][1] != c:
                # conflicting 16:00 stamps (DST fold) -- keep the earlier UTC
                if want < inst[loc.date()][0]:
                    inst[loc.date()] = (want, c)
            else:
                inst[loc.date()] = (want, c)
    days = sorted(inst)
    out = (days, {d: inst[d][1] for d in days})
    _DC_CACHE[key] = out
    return out


def load_staged_triple(staged_dir: str):
    """Load the three frozen conditioning series (ordered dict: anchor legs
    then control).  Returns (numeric_rows_by_series, all_obs_dates_by_series).
    """
    numeric = OrderedDict()
    all_dates = OrderedDict()
    for name in ("T10YIE", "T5YIE", "DGS10"):
        rows, dates = load_staged_series(
            os.path.join(staged_dir, f"{name}.json"))
        numeric[name] = rows
        all_dates[name] = dates
    return numeric, all_dates


# ------------------------------------------------------------------ run_arm #
def run_arm(arm: str, data_paths: dict):
    """Produce the arm's decision records (no PnL anywhere).

    data_paths keys: price_dir, staged_dir, s0_start, s0_end,
    enforce_real_grid (optional fail-closed census check on real bytes).
    """
    if arm not in ARM_IDS:
        raise ValueError(f"unknown arm {arm}")
    price_dir = data_paths["price_dir"]
    staged_dir = data_paths["staged_dir"]
    s0_start = data_paths.get("s0_start", S0_START)
    s0_end = data_paths.get("s0_end", S0_END)

    numeric, all_dates = load_staged_triple(staged_dir)
    grid = build_grid(all_dates, s0_start, s0_end)
    if data_paths.get("enforce_real_grid"):
        if len(grid) != EXPECTED_GRID_CLOCKS:
            raise DataBlocked(
                f"GRID_CENSUS_MISMATCH: {len(grid)} != {EXPECTED_GRID_CLOCKS}")
        if grid[0] != S0_START or grid[-1] != S0_END:
            raise DataBlocked("GRID_BOUNDS_MISMATCH")
    recon = AsOfReconstructor(grid, numeric)

    z_by_clock, dmeta = compute_driver_series(recon, arm)

    # usable grid: clocks strictly after the WARMUP-th binding clock
    first_usable_i = None
    for i, d in enumerate(grid):
        if recon.binding_clocks_before(d) >= WARMUP:
            first_usable_i = i
            break
    if first_usable_i is None:
        raise DataBlocked("WARMUP_NEVER_COMPLETED")
    usable_clocks = grid[first_usable_i:]

    fills = {}
    fill_days = {}
    for pair in PAIRS:
        days, px = load_decision_closes(price_dir, pair)
        fill_days[pair] = set(days)
        fills[pair] = {d: px[d] for d in usable_clocks if d in px}

    decisions, counts = simulate_arm(z_by_clock, fills, usable_clocks, arm)

    bounds = fold_bounds(len(usable_clocks))
    fold_days = {1: usable_clocks[bounds[0]],
                 2: usable_clocks[bounds[1]],
                 3: usable_clocks[-1]}
    digest = arm_config_digest(arm)
    for rec in decisions:
        i_e = usable_clocks.index(parse_date(rec["entry_day"]))
        i_x = usable_clocks.index(parse_date(rec["exit_day"]))
        rec["entry_clock_idx"] = i_e
        rec["exit_clock_idx"] = i_x
        rec["hold_clocks"] = i_x - i_e
        rec["fold"] = fold_of_index(i_e, bounds)
        rec["arm_config_digest"] = digest
        rec["driver_window"] = Z_WINDOW[arm]

    holds = [rec["hold_clocks"] for rec in decisions]
    meta = {
        "family_id": FAMILY_ID, "arm": arm, "arm_id": ARM_IDS[arm],
        "proposal_id": PROPOSAL_ID, "cycle_id": CYCLE_ID,
        "decision_clock": DECISION_CLOCK,
        "grid_clocks": len(grid),
        "binding_clocks_total": recon.total_binding_clocks,
        "warmup_burned_clocks": WARMUP,
        "first_usable_clock": usable_clocks[0].isoformat(),
        "last_usable_clock": usable_clocks[-1].isoformat(),
        "usable_clocks": len(usable_clocks),
        "usable_clock_list": [d.isoformat() for d in usable_clocks],
        "fold_bounds_idx": bounds,
        "fold_first_clocks": {k: v.isoformat() for k, v in fold_days.items()},
        "driver_window": Z_WINDOW[arm],
        "counts": counts,
        "driver_meta": dmeta,
        "hold_clocks_mean": (round(math.fsum(holds) / len(holds), 6)
                             if holds else None),
        "hold_clocks_max": (max(holds) if holds else None),
        "n_decisions": len(decisions),
        "folds": {str(f): sum(1 for r in decisions if r["fold"] == f)
                  for f in (1, 2, 3)},
        "arm_config_digest": digest,
    }
    return {"decisions": decisions, "meta": meta}
