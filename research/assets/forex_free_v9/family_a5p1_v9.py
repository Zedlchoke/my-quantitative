"""FOREX-FREE-V9 family FXFV9-A5-P1 runner -- realized-inflation SURPRISE
differential conditioning (FROZEN at research/control/forex_free_v9_run/
d1/a5-open/proposal-1.json; mechanics frozen per the I-phase mission).

Verbatim frozen mechanics (implemented exactly; never "improved"):

- legs: GB (ONS D7BT official) / CA (StatCan official) / AU, NZ (FRED
  vintaged quarterly at quarter-first-months) / US (FRED vintaged
  monthly); availability GB/CA from the pinned calendars over the
  mid-next-month placeholder class, AU/NZ/US at FRED first-binding
  realtime_start (research.assets.forex_free_v9.conditioning).
- surprise per economy leg (PERCENTAGE POINTS):
      surprise = (y/y log step - trailing-OLS-trend value) * 100
  trend window = trailing 24 calendar months of prints (24 obs monthly
  legs, 8 obs quarterly legs), recomputed ONLY at print instants; the
  state is piecewise constant between prints.
- arms:
    anchor     D(t) = surprise_home(t) - surprise_US(t)  (single as-of
               state per clock; AX2-C2)
    neighbour  +7d sham-calendar: EVERY print's availability instant
               (pinned dates AND FRED realtime_starts) shifted exactly
               +7 calendar days when constructing the state path
               (MANDATORY sham, neighbour slot)
    control    home-only surprise (US leg removed), same thresholds,
               holds, clock, sign map, costs (differential content
               removed -- R1 semantics)
- activation |D| >= 0.25pp (control |s| >= 0.25pp); exit |D| <= 0.15pp
  hysteresis or driver sign flip, evaluated after a 5-binding-clock
  minimum hold; hard max hold 63 binding clocks with immediate re-entry
  at the NEXT clock if still in-region; direction: LONG home on D >= 0
  per the home sign map (GBPUSD +1, AUDUSD +1, NZDUSD +1, USDCAD -1);
  max one position per pair; fills at decision-instant closes.
- warmup: 0 in-S0 burned clocks (>= 36 print periods of per-leg history
  bind from staged pre-S0 depth); usable grid = the full S0 weekday grid.
- folds: 3 equal thirds of the usable decision grid, mechanical.

This module produces decision records only.  Costs, financing, books,
gates and diagnostics are driver-owned (exec_driver_v9.py).  No PnL here.
"""
from __future__ import annotations

import hashlib
import json
import math
from collections import OrderedDict

from research.assets.forex_free_v9 import family_common as FC
from research.assets.forex_free_v9.conditioning import (
    DataBlocked,
    build_economy_legs,
    walk_surprise_states,
)

__all__ = [
    "run_arm", "simulate_arm", "compute_driver_series", "ARM_IDS",
    "FAMILY_ID", "PROPOSAL_ID", "PAIRS", "ENTRY_PP", "EXIT_PP",
    "MIN_HOLD_CLOCKS", "MAX_HOLD_CLOCKS", "arm_frozen_config",
    "arm_config_digest", "SHAM_SHIFT_DAYS",
]

CYCLE_ID = FC.CYCLE_ID
FAMILY_ID = "FXFV9-A5-P1"
PROPOSAL_ID = "FXFV9-A5-P1"
DECISION_CLOCK = FC.DECISION_CLOCK

ARM_IDS = OrderedDict((
    ("anchor", "anchor_surprise_diff_025pp_015pp_h5_63"),
    ("neighbour", "neighbour_surprise_diff_025pp_015pp_sham7d"),
    ("control", "control_home_surprise_025pp_015pp_h5_63"),
))
ENTRY_PP = 0.25              # |D| >= 0.25pp activates
EXIT_PP = 0.15               # |D| <= 0.15pp hysteresis band
MIN_HOLD_CLOCKS = FC.MIN_HOLD_CLOCKS     # 5
MAX_HOLD_CLOCKS = FC.MAX_HOLD_CLOCKS     # 63
SHAM_SHIFT_DAYS = 7          # mandatory +7d sham-calendar neighbour

PAIRS = FC.PAIRS
S0_START = FC.S0_START
S0_END = FC.S0_END


def side_for_driver(driver: float, pair: str) -> int:
    """Frozen direction map: LONG home currency on driver >= 0 per the home
    sign map (USDCAD's long home is the SHORT pair)."""
    return FC.LONG_HOME_SIGN[pair] * (1 if driver >= 0.0 else -1)


def arm_frozen_config(arm: str) -> dict:
    """The arm's frozen configuration (the exact bytes hashed into
    arm_config_digest).  Every field is frozen by the proposal / p3 freeze."""
    return {
        "arm": arm,
        "arm_id": ARM_IDS[arm],
        "cost_ladder": "1.5 bps/side x {1.0, 1.5, 2.0}",
        "decision_clock": DECISION_CLOCK,
        "driver": {
            "anchor": "surprise_home_minus_surprise_US",
            "neighbour": "surprise_home_minus_surprise_US_+7d_sham_calendar",
            "control": "home_surprise_only",
        }[arm],
        "driver_legs": (["home", "US"] if arm != "control" else ["home"]),
        "entry_pp": ENTRY_PP,
        "exit_pp": EXIT_PP,
        "family_id": FAMILY_ID,
        "folds": {"n_folds": 3,
                  "rule": "equal thirds of the usable decision grid"},
        "home_sign_map": {p: FC.LONG_HOME_SIGN[p] for p in PAIRS},
        "max_hold_clocks": MAX_HOLD_CLOCKS,
        "min_hold_clocks": MIN_HOLD_CLOCKS,
        "pairs": list(PAIRS),
        "sham_shift_days": (SHAM_SHIFT_DAYS if arm == "neighbour" else 0),
        "s0_window": [S0_START.isoformat(), S0_END.isoformat()],
        "tier_primary": 2.0,
        "trend_window_by_freq": {"monthly": 24, "quarterly": 8},
        "warmup_burn_clocks": 0,
    }


def arm_config_digest(arm: str) -> str:
    """sha256 of the arm's frozen config JSON (canonical sort_keys)."""
    blob = json.dumps(arm_frozen_config(arm), sort_keys=True,
                      separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


# ------------------------------------------------------------ driver walk #
def compute_driver_series(legs, grid, arm: str,
                          surprise_states=None):
    """Walk the grid once; return (per_pair_driver, meta) for the arm.

    Surprise states are computed from the as-bound print history exactly as
    frozen (trend recomputed only at print instants; the state is piecewise
    constant between prints).  The anchor/neighbour differential reads BOTH
    legs under the same per-clock state (AX2-C2 single snapshot); the
    control reads the home leg alone.  Returns
    ({pair: {clock: driver|None}}, meta).
    """
    if surprise_states is None:
        shift = SHAM_SHIFT_DAYS if arm == "neighbour" else 0
        surprise_states = walk_surprise_states(legs, grid, shift)
    elif arm == "neighbour":
        raise DataBlocked("NEIGHBOUR_REQUIRES_SHIFTED_STATES")

    per_pair: dict = {}
    no_value_clocks = 0
    for pair in PAIRS:
        home_e = FC.HOME_OF_PAIR[pair]
        series: dict = {}
        for d in grid:
            s_home = surprise_states[home_e][d]
            if arm == "control":
                v = s_home
            else:
                s_us = surprise_states["US"][d]
                v = (None if s_home is None or s_us is None
                     else s_home - s_us)
            series[d] = v
            if v is None:
                no_value_clocks += 1
        per_pair[pair] = series
    meta = {
        "driver": arm_frozen_config(arm)["driver"],
        "surprise_states_bound": {e: sum(1 for v in st.values()
                                         if v is not None)
                                  for e, st in sorted(surprise_states.items())},
        "no_value_clocks_pooled": no_value_clocks,
    }
    return per_pair, meta


def simulate_arm(per_pair_driver, fills, usable_clocks, arm: str,
                 pairs=PAIRS, entry_pp: float = ENTRY_PP,
                 exit_pp: float = EXIT_PP):
    """The frozen state machine per pair on the arm's per-pair driver."""
    all_decisions: list[dict] = []
    counts: "OrderedDict[str, int]" = OrderedDict()
    for pair in pairs:
        dec, cnt = FC.simulate_arm(
            per_pair_driver[pair], fills, usable_clocks,
            side_for_driver, pairs=(pair,), entry=entry_pp, exit_band=exit_pp,
            min_hold=MIN_HOLD_CLOCKS, max_hold=MAX_HOLD_CLOCKS)
        all_decisions.extend(dec)
        if not counts:
            counts = OrderedDict((k, 0) for k in cnt)
        for k, v in cnt.items():
            counts[k] = counts.get(k, 0) + v
    counts["usable_clocks"] = len(usable_clocks)   # grid size, not per-pair
    all_decisions.sort(key=lambda r: (r["entry_day"], r["pair"]))
    return all_decisions, counts


# ------------------------------------------------------------------ run_arm #
def run_arm(arm: str, data_paths: dict):
    """Produce the arm's decision records (no PnL anywhere).

    data_paths keys: price_dir, cpi_dir, gb_calendar_path, ca_calendar_path,
    s0_start, s0_end, enforce_real_grid (optional bounds check on real
    bytes).
    """
    if arm not in ARM_IDS:
        raise ValueError(f"unknown arm {arm}")
    price_dir = data_paths["price_dir"]
    s0_start = data_paths.get("s0_start", S0_START)
    s0_end = data_paths.get("s0_end", S0_END)

    legs = build_economy_legs(
        data_paths["cpi_dir"], data_paths["gb_calendar_path"],
        data_paths["ca_calendar_path"])
    grid = FC.build_grid(price_dir, s0_start, s0_end)
    if data_paths.get("enforce_real_grid"):
        if grid[0] != s0_start or grid[-1] != s0_end:
            raise DataBlocked("GRID_BOUNDS_MISMATCH")

    per_pair, dmeta = compute_driver_series(legs, grid, arm)

    usable_clocks = list(grid)          # warmup burn = 0 (frozen)
    fills = {}
    for pair in PAIRS:
        _days, px = FC.load_spot_daily(price_dir, pair)
        fills[pair] = {d: px[d] for d in usable_clocks if d in px}

    decisions, counts = simulate_arm(per_pair, fills, usable_clocks, arm)

    bounds = FC.fold_bounds(len(usable_clocks))
    fold_days = {1: usable_clocks[bounds[0]],
                 2: usable_clocks[bounds[1]],
                 3: usable_clocks[-1]}
    digest = arm_config_digest(arm)
    for rec in decisions:
        i_e = usable_clocks.index(FC.parse_day(rec["entry_day"]))
        i_x = usable_clocks.index(FC.parse_day(rec["exit_day"]))
        rec["entry_clock_idx"] = i_e
        rec["exit_clock_idx"] = i_x
        rec["hold_clocks"] = i_x - i_e
        rec["fold"] = FC.fold_of_index(i_e, bounds)
        rec["arm_config_digest"] = digest

    holds = [rec["hold_clocks"] for rec in decisions]
    meta = {
        "family_id": FAMILY_ID, "arm": arm, "arm_id": ARM_IDS[arm],
        "proposal_id": PROPOSAL_ID, "cycle_id": CYCLE_ID,
        "decision_clock": DECISION_CLOCK,
        "grid_clocks": len(grid),
        "first_usable_clock": usable_clocks[0].isoformat(),
        "last_usable_clock": usable_clocks[-1].isoformat(),
        "usable_clocks": len(usable_clocks),
        "usable_clock_list": [d.isoformat() for d in usable_clocks],
        "fold_bounds_idx": bounds,
        "fold_first_clocks": {k: v.isoformat() for k, v in fold_days.items()},
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
