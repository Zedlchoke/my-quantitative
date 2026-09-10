"""FOREX-FREE-V9 family FXFV9-A5-P2 runner -- cross-economy
inflation-differential MOMENTUM conditioning (FROZEN at research/control/
forex_free_v9_run/d1/a5-open/proposal-2.json; mechanics frozen per the
I-phase mission).

Verbatim frozen mechanics (implemented exactly; never "improved"):

- legs: identical five legs to FXFV9-A5-P1 (GB/CA official tables, AU/NZ
  FRED vintaged quarterly, US FRED vintaged monthly); identical pinned /
  first-binding availability; identical +7d sham-calendar neighbour.
- gap:  gap_p(x) = pi_home(latest print as-of x) - pi_US(latest print
  as-of x); each leg's value is the AS-BOUND y/y (computed once at the
  print's own availability snapshot, never recomputed -- AX2-C1), so the
  gap at any clock is exactly what was knowable then (AX2-C2 single
  snapshot per instant; the two momentum snapshots are two separate as-of
  instants, each internally consistent).
- momentum (the mechanism-bearing FIRST DIFFERENCE, never the level):
      M(t) = gap_p(t) - gap_p(t - 63 calendar days)
  both snapshots as-bound at their own instants; no interpolation between
  prints -- the state is piecewise constant in both snapshots.  Units: pp
  per quarter-scale window (log-gap difference * 100).
- arms:
    anchor     |M| >= 0.15pp in, |M| <= 0.10pp out
    neighbour  +7d sham-calendar (EVERY availability instant shifted
               exactly +7 calendar days in BOTH snapshots' construction)
    control    differential-LEVEL form: |gap| >= 0.50pp in, |gap| <=
               0.35pp out (level-scale thresholds frozen ex ante; the
               momentum order removed -- R1 semantics)
- exit on hysteresis band or driver sign flip, evaluated after a
  5-binding-clock minimum hold; hard max hold 63 binding clocks with
  immediate re-entry at the NEXT clock if still in-region; direction LONG
  home on driver >= 0 per the home sign map (GBPUSD +1, AUDUSD +1,
  NZDUSD +1, USDCAD -1); max one position per pair; fills at
  decision-instant closes.
- warmup: 0 in-S0 burned clocks (y/y chain + a 63-day earlier snapshot
  bind from staged pre-S0 depth); usable grid = the full S0 weekday grid.

This module produces decision records only.  Costs, financing, books,
gates and diagnostics are driver-owned (exec_driver_v9.py).  No PnL here.
"""
from __future__ import annotations

import hashlib
import json
import math
from collections import OrderedDict
from datetime import timedelta

from research.assets.forex_free_v9 import family_common as FC
from research.assets.forex_free_v9.conditioning import (
    DataBlocked,
    build_economy_legs,
    walk_pi_states,
)

__all__ = [
    "run_arm", "simulate_arm", "compute_driver_series", "ARM_IDS",
    "FAMILY_ID", "PROPOSAL_ID", "PAIRS", "ENTRY_MOM_PP", "EXIT_MOM_PP",
    "ENTRY_LVL_PP", "EXIT_LVL_PP", "MOM_LAG_DAYS", "MIN_HOLD_CLOCKS",
    "MAX_HOLD_CLOCKS", "arm_frozen_config", "arm_config_digest",
    "SHAM_SHIFT_DAYS", "gap_series", "momentum_series",
]

CYCLE_ID = FC.CYCLE_ID
FAMILY_ID = "FXFV9-A5-P2"
PROPOSAL_ID = "FXFV9-A5-P2"
DECISION_CLOCK = FC.DECISION_CLOCK

ARM_IDS = OrderedDict((
    ("anchor", "anchor_gap_momentum63_015pp_010pp_h5_63"),
    ("neighbour", "neighbour_gap_momentum63_015pp_010pp_sham7d"),
    ("control", "control_gap_level_050pp_035pp_h5_63"),
))
ENTRY_MOM_PP = 0.15         # |M| >= 0.15pp activates (momentum form)
EXIT_MOM_PP = 0.10          # |M| <= 0.10pp hysteresis band
ENTRY_LVL_PP = 0.50         # |gap| >= 0.50pp activates (control LEVEL form)
EXIT_LVL_PP = 0.35          # |gap| <= 0.35pp hysteresis band (control)
MOM_LAG_DAYS = 63           # calendar-day lag of the momentum snapshot
MIN_HOLD_CLOCKS = FC.MIN_HOLD_CLOCKS     # 5
MAX_HOLD_CLOCKS = FC.MAX_HOLD_CLOCKS     # 63
SHAM_SHIFT_DAYS = 7         # mandatory +7d sham-calendar neighbour

PAIRS = FC.PAIRS
S0_START = FC.S0_START
S0_END = FC.S0_END


def side_for_driver(driver: float, pair: str) -> int:
    """Frozen direction map (identical to P1): LONG home on driver >= 0."""
    return FC.LONG_HOME_SIGN[pair] * (1 if driver >= 0.0 else -1)


def arm_frozen_config(arm: str) -> dict:
    """The arm's frozen configuration (the exact bytes hashed into
    arm_config_digest)."""
    return {
        "arm": arm,
        "arm_id": ARM_IDS[arm],
        "cost_ladder": "1.5 bps/side x {1.0, 1.5, 2.0}",
        "decision_clock": DECISION_CLOCK,
        "driver": {
            "anchor": "gap63d_momentum_home_minus_US",
            "neighbour": "gap63d_momentum_home_minus_US_+7d_sham_calendar",
            "control": "gap_level_home_minus_US",
        }[arm],
        "driver_legs": ["home", "US"],
        "entry_pp": (ENTRY_LVL_PP if arm == "control" else ENTRY_MOM_PP),
        "exit_pp": (EXIT_LVL_PP if arm == "control" else EXIT_MOM_PP),
        "family_id": FAMILY_ID,
        "folds": {"n_folds": 3,
                  "rule": "equal thirds of the usable decision grid"},
        "home_sign_map": {p: FC.LONG_HOME_SIGN[p] for p in PAIRS},
        "max_hold_clocks": MAX_HOLD_CLOCKS,
        "min_hold_clocks": MIN_HOLD_CLOCKS,
        "momentum_lag_days": (MOM_LAG_DAYS if arm != "control" else None),
        "pairs": list(PAIRS),
        "sham_shift_days": (SHAM_SHIFT_DAYS if arm == "neighbour" else 0),
        "s0_window": [S0_START.isoformat(), S0_END.isoformat()],
        "tier_primary": 2.0,
        "warmup_burn_clocks": 0,
    }


def arm_config_digest(arm: str) -> str:
    """sha256 of the arm's frozen config JSON (canonical sort_keys)."""
    blob = json.dumps(arm_frozen_config(arm), sort_keys=True,
                      separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


# ------------------------------------------------------------ driver walk #
def gap_series(pi_states, grid, pair: str) -> dict:
    """{clock: gap_pp_x100_log_units | None}: the as-bound home-minus-US
    y/y gap, piecewise constant between binding clocks (both legs read
    under the same per-clock state; AX2-C2)."""
    home_e = FC.HOME_OF_PAIR[pair]
    out: dict = {}
    for d in grid:
        h = pi_states[home_e][d]
        u = pi_states["US"][d]
        out[d] = (None if h is None or u is None else h - u)
    return out


def momentum_series(gap: dict, grid) -> dict:
    """M(t) = (gap(t) - gap(t - 63 calendar days)) * 100 -- the frozen
    first-difference driver.  The earlier snapshot is the as-bound gap at
    the latest grid clock <= t - 63d (never recomputed at current
    vintage); None when either snapshot is undefined."""
    out: dict = {}
    j = -1
    for d in grid:
        target = d - timedelta(days=MOM_LAG_DAYS)
        while j + 1 < len(grid) and grid[j + 1] <= target:
            j += 1
        g_now = gap[d]
        g_then = (gap[grid[j]] if j >= 0 else None)
        out[d] = (None if g_now is None or g_then is None
                  else (g_now - g_then) * 100.0)
    return out


def compute_driver_series(legs, grid, arm: str, pi_states=None):
    """Walk the grid once; return ({pair: {clock: driver|None}}, meta)."""
    if pi_states is None:
        shift = SHAM_SHIFT_DAYS if arm == "neighbour" else 0
        pi_states = walk_pi_states(legs, grid, shift)
    elif arm == "neighbour":
        raise DataBlocked("NEIGHBOUR_REQUIRES_SHIFTED_STATES")

    per_pair: dict = {}
    no_value_clocks = 0
    for pair in PAIRS:
        gap = gap_series(pi_states, grid, pair)
        if arm == "control":
            # LEVEL form in pp (same x100 scale as the momentum driver)
            series = {d: (None if v is None else v * 100.0)
                      for d, v in gap.items()}
        else:
            series = momentum_series(gap, grid)
        per_pair[pair] = series
        no_value_clocks += sum(1 for v in series.values() if v is None)
    meta = {
        "driver": arm_frozen_config(arm)["driver"],
        "pi_states_bound": {e: sum(1 for v in st.values() if v is not None)
                            for e, st in sorted(pi_states.items())},
        "no_value_clocks_pooled": no_value_clocks,
        "momentum_lag_days": (MOM_LAG_DAYS if arm != "control" else None),
    }
    return per_pair, meta


def simulate_arm(per_pair_driver, fills, usable_clocks, arm: str,
                 pairs=PAIRS):
    """The frozen state machine per pair on the arm's per-pair driver."""
    entry = ENTRY_LVL_PP if arm == "control" else ENTRY_MOM_PP
    exit_band = EXIT_LVL_PP if arm == "control" else EXIT_MOM_PP
    all_decisions: list[dict] = []
    counts: "OrderedDict[str, int]" = OrderedDict()
    for pair in pairs:
        dec, cnt = FC.simulate_arm(
            per_pair_driver[pair], fills, usable_clocks,
            side_for_driver, pairs=(pair,), entry=entry, exit_band=exit_band,
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

    data_paths keys mirror family_a5p1_v9.run_arm.
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
