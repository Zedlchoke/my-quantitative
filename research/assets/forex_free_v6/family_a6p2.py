#!/usr/bin/env python
"""FOREX-FREE-V6 family FXFV6-A6-P2: dollar-factor concentration-gated
cross-pair short-horizon reversal (I1 implementation lane, cycle
FOREX-FREE-V6).

Implements the SELECTED family EXACTLY as frozen by

  * research/control/forex_free_v6_run/d1/a6_open/proposal_P2.json
    (sha256 077b3b1220e9070865ee3a654f4f86b28dbcba78133196592ad9b3d1722461b3),
  * research/control/forex_free_v6_run/selection_freeze.json
    (arms anchor / neighbour / control with frozen arm_config_digests),
  * the staged daily snapshots for all 7 pairs under
    data_raw/forex_free_v1 (byte-verified per p2_data_authority_v6.json).

MECHANISM (frozen law, transcribed from the proposal): PURELY price-derived
-- no calendar, no macro series, no print content, no rates input.

On the 7-pair intersection grid of weekday decision closes (a grid date has
ALL 7 closes by construction -- the A9 primary measurement grid; on it the
fail-closed all-7-pairs rule can never shrink the cross-section, and the
guard is still implemented and counted):

    r_{i,t}   = ln(C_{i,t} / C_{i,t-1})                (grid-day returns)
    s_t       = lambda_1 / sum(lambda) of the 7x7 CORRELATION matrix of
                the trailing 20 daily returns {r_{i,tau}: tau in t-19..t}
                (correlation, not covariance; PC1 sign irrelevant)
    reference = {s_tau} over the 252 decision days ENDING at t-1 (each on
                its own trailing-20 window; excludes the current day)
    state_high= s_t >= 75th percentile of the reference
    cum10_i_t = sum of {r_{i,tau}: tau in t-9..t}
    vol20_i_t = sample std of {r_{i,tau}: tau in t-19..t}
    noise floor: pair i skipped at t if |cum10| < 0.25 * vol20 * sqrt(10)
    direction = -sign(cum10)  (FADE) for every pair passing the floor

warmup = 272 decision days (252-day rolling reference + 20-day state
window + 1); the first eligible decision date is pinned by the grid, not
asserted (A9 measured 2019-09-19).

FILLS (never same-bar): entry decision at close t; entry fill at close(t+1)
(first decision day after the entry decision); exit decision at close
4 decision days after the entry fill; exit fill at close exactly 5 decision
days after the entry fill -- exposure spans exactly 5 decision-day
close-to-close intervals per pair.

ARMS (selection_freeze.json):

  anchor     fade all noise-floor-passing pairs when state_high;
  neighbour  the COMPLEMENT state (s_t < the same 75th-percentile
             reference threshold); windows, floor, direction, clock and
             fills identical (single differing design axis);
  control    deterministic placebo: the state series circularly shifted
             +100 decision days, state_placebo_t = state_{t-100} (the
             state is a past value, so the placebo is trivially PIT-safe
             and fully deterministic -- no randomness, no seeds).  A
             placebo day additionally requires the shifted source day to
             itself be state-eligible (A9 measured first placebo eligible
             t = 2020-02-06 = 100 decision days after 2019-09-19).

FAIL-CLOSED / PIT DISCIPLINE:

  * a state at decision close t uses only closes at or before t (trailing
    windows; the reference excludes the current day) -- PIT by construction;
  * if ANY of the 7 pairs lacks a decision close inside the trailing
    20-decision-day window at t, NO new entries are formed at t (counted;
    structurally impossible on the intersection grid, still enforced);
  * a singular/degenerate correlation window (a zero-variance pair column
    or non-finite input) leaves the state UNDEFINED at t: no entries, counted
    -- never computed on a shrunken cross-section;
  * overlap rule: one position per pair; while a position is open on pair i
    (open = its exit fill instant is after the new signal's decision
    instant), new signals on i are SKIPPED and counted;
  * fold boundary rule: any trade whose EXIT FILL crosses an internal fold
    boundary is DROPPED from both books and counted (the 5-interval
    exposure span is the mechanism and is never truncated);
  * S0: decision days t are restricted to the frozen S0 window
    2018-04-04..2025-07-24; exit fills resolve on the staged grid after S0
    and fail closed at staged-data end (no asserted dates).

Folds: 3 contiguous temporal thirds of S0 by decision-day count; the
boundaries in evidence are the A9 measured thirds grid (B1 2020-09-09,
B2 2023-02-16, research/control/forex_free_v6_run/d2/a9_feasibility/
FXFV6-A6-P2.json) -- the only in-repo frozen-boundary evidence for this
family.  Trades assign by entry decision date t.

Windows 20/252/10, percentile 75, floor multiplier 0.25 and hold length 5
are preregistered constants: no training, no calibration, no threshold
search anywhere.  Costs, financing and books are driver-owned
(exec_driver_v6.py); this module is decision machinery only.
"""
from __future__ import annotations

import json
import math
import os
from collections import OrderedDict
from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo

import numpy as np

__all__ = [
    "run_arm", "build_grid", "state_share_series", "percentile75",
    "DataBlocked", "ARM_IDS", "UNIVERSE", "FOLD_BOUNDARIES_P2",
]

UTC = timezone.utc
NY_TZ = ZoneInfo("America/New_York")

CYCLE_ID = "FOREX-FREE-V6"
PROPOSAL_ID = "FXFV6-A6-P2"
FAMILY_ID = "FXFV6-A6-P2"

ARM_IDS = {
    "anchor": "FXFV6-A6-P2-anchor",
    "neighbour": "FXFV6-A6-P2-neighbour",
    "control": "FXFV6-A6-P2-placebo",
}

# frozen universe: every pair enters identically as a leg of the cross-pair
# co-movement measure (proposal universe.included, freeze order)
UNIVERSE = ("AUDUSD", "EURUSD", "GBPUSD", "NZDUSD", "USDCAD", "USDCHF",
            "USDJPY")
PAIR_AREAS = {
    "AUDUSD": ("AU", "US"), "EURUSD": ("EMU", "US"), "GBPUSD": ("GB", "US"),
    "NZDUSD": ("NZ", "US"), "USDCAD": ("US", "CA"), "USDCHF": ("US", "CH"),
    "USDJPY": ("US", "JP"),
}

STATE_WINDOW = 20          # trailing returns in the correlation matrix
REFERENCE_DAYS = 252       # rolling reference window (ends at t-1)
CUM_DAYS = 10              # trailing cumulative return
HOLD_DECISION_DAYS = 5     # exposure spans exactly 5 close-to-close intervals
NOISE_FLOOR_MULT = 0.25
PERCENTILE = 75.0
PLACEBO_SHIFT_DECISION_DAYS = 100
WARMUP_DECISION_DAYS = REFERENCE_DAYS + STATE_WINDOW + 1   # 272
NOTIONAL_USD = 10000.0
S0_START = "2018-04-04"
S0_END = "2025-07-24"

# frozen fold thirds (A9 measured thirds grid -- the only in-repo
# frozen-boundary evidence for this family; see module docstring)
FOLD_BOUNDARIES_P2 = ("2020-09-09", "2023-02-16")
FOLD_IDS = ("F1", "F2", "F3")

DECISION_CLOCK = "daily 16:00 America/New_York (DST-correct via zoneinfo)"
ALPHA_DEFINITION = "per_trade_expectancy_difference_v1"
FINANCING_FORMULA_ID = "fx5_day_start_asof_policy_rate_diff_v5ledger_v1"

REASON_UNDEFINED_STATE = "state_undefined_days"
REASON_MISSING_TRAILING = "missing_trailing_close_days"
REASON_NOISE_FLOOR = "leg_skips_noise_floor"
REASON_COLLISION = "leg_skips_collision"
REASON_END_OF_DATA = "leg_skips_end_of_data"
REASON_BOUNDARY_DROP = "boundary_crossing_dropped"

PERCENTILE_METHOD = "linear_interpolation"   # numpy default, deterministic


class DataBlocked(RuntimeError):
    """A required evidenced input is missing/malformed; fail closed."""

    reason = "BLOCKED_DATA"

    def __init__(self, detail: str) -> None:
        super().__init__(f"BLOCKED_DATA: {detail}")
        self.detail = detail


def _iso(t: datetime) -> str:
    return t.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%S+00:00")


def ny_decision_stamp(day: date) -> datetime:
    """UTC instant of the 16:00 America/New_York decision of ``day``."""
    return datetime(day.year, day.month, day.day, 16, 0,
                    tzinfo=NY_TZ).astimezone(UTC)


# ------------------------------------------------------------------ #
# staged daily closes + the intersection grid                         #
# ------------------------------------------------------------------ #
def load_daily_closes(price_dir: str, pair: str) -> dict:
    """One pair's weekday decision-close series {date: close} from the
    staged 1day snapshots (daily-or-slower only; the 4h snapshots are
    never read).  Weekend stamps are not decision days.  Fail closed on
    malformed files, conflicting duplicates and non-positive closes."""
    sym = pair.replace("/", "")
    paths = sorted(p for p in os.listdir(price_dir)
                   if p.startswith(f"{sym}_1day_") and p.endswith(".json")) \
        if os.path.isdir(price_dir) else []
    if not paths:
        raise DataBlocked(f"no 1day staged snapshot for {pair} under {price_dir}")
    rows = {}
    for name in paths:
        full = os.path.join(price_dir, name)
        try:
            with open(full, "r", encoding="utf-8") as handle:
                payload = json.load(handle)
        except (OSError, ValueError) as exc:
            raise DataBlocked(f"unreadable 1day snapshot {full}: {exc}")
        if isinstance(payload, dict) and payload.get("status") == "error":
            continue  # provider no-data window
        values = payload.get("values") if isinstance(payload, dict) else None
        if not isinstance(values, list):
            raise DataBlocked(f"1day snapshot {full} carries no values list")
        for row in values:
            if not isinstance(row, dict):
                raise DataBlocked(f"1day snapshot {full} malformed row")
            try:
                day = date.fromisoformat(str(row["datetime"]))
                close = float(row["close"])
            except (KeyError, TypeError, ValueError) as exc:
                raise DataBlocked(f"1day snapshot {full}: unparseable bar ({exc})")
            if day.weekday() >= 5:
                continue
            if not (math.isfinite(close) and close > 0):
                raise DataBlocked(f"1day snapshot {full}: non-positive close "
                                  f"at {day.isoformat()}")
            if day in rows and rows[day] != close:
                raise DataBlocked(f"conflicting duplicate daily close at "
                                  f"{day.isoformat()} in {full}")
            rows[day] = close
    if not rows:
        raise DataBlocked(f"1day snapshot for {pair} holds no weekday closes")
    return rows


def build_grid(price_dir: str) -> tuple:
    """(grid_days, close_matrix) on the 7-pair INTERSECTION of weekday
    decision closes (a grid date has all 7 closes by construction -- the
    A9 primary measurement grid).  Fail closed if any pair is missing."""
    per_pair = OrderedDict((p, load_daily_closes(price_dir, p))
                           for p in UNIVERSE)
    common = sorted(set.intersection(*[set(v) for v in per_pair.values()]))
    if not common:
        raise DataBlocked("empty 7-pair intersection grid")
    matrix = np.array([[per_pair[p][d] for p in UNIVERSE] for d in common],
                      dtype=float)
    return common, matrix


# ------------------------------------------------------------------ #
# the frozen state series (PC1 share of the correlation matrix)       #
# ------------------------------------------------------------------ #
def state_share_series(grid_days, close_matrix):
    """s_i for every grid index i >= STATE_WINDOW (None where the state is
    UNDEFINED: a zero-variance pair column or non-finite input leaves the
    state undefined -- never computed on a shrunken cross-section).

    Returns (shares, singular_count) with shares[i] defined for
    i >= STATE_WINDOW (possibly None)."""
    returns = np.diff(np.log(close_matrix), axis=0)   # R[j]: day j -> j+1
    n = len(grid_days)
    shares = {i: None for i in range(n)}
    singular = 0
    for i in range(STATE_WINDOW, n):
        win = returns[i - STATE_WINDOW:i, :]           # 20 x 7, ends at day i
        if not np.all(np.isfinite(win)):
            singular += 1
            continue
        sd = win.std(axis=0, ddof=1)
        if np.any(sd == 0.0):
            singular += 1
            continue
        corr = np.corrcoef(win, rowvar=False)
        if not np.all(np.isfinite(corr)):
            singular += 1
            continue
        eig = np.linalg.eigvalsh(corr)                 # ascending, symmetric
        total = float(np.sum(eig))
        if not math.isfinite(total) or total <= 0.0:
            singular += 1
            continue
        shares[i] = float(eig[-1]) / total
    return shares, singular, returns


def percentile75(values) -> float:
    """The preregistered 75th percentile of the reference distribution
    (linear interpolation between order statistics -- the deterministic
    numpy default; the method is fixed, never fitted)."""
    return float(np.percentile(np.asarray(values, dtype=float), PERCENTILE,
                               method="linear"))


def fold_of_index(grid_days, i):
    """Fold id by entry decision date (frozen thirds; internal boundaries
    only -- an exit beyond S0 end crosses no internal boundary)."""
    d = grid_days[i]
    b1 = date.fromisoformat(FOLD_BOUNDARIES_P2[0])
    b2 = date.fromisoformat(FOLD_BOUNDARIES_P2[1])
    if d < b1:
        return "F1"
    if d < b2:
        return "F2"
    return "F3"


# ------------------------------------------------------------------ #
# family API entry point                                              #
# ------------------------------------------------------------------ #
def run_arm(arm: str, data_paths: dict):
    """Frozen family API (V6 driver runner contract).

    Returns {"decisions": [...], "meta": {...}}.  No PnL is computed here.
    """
    arm_id = ARM_IDS.get(arm)
    if arm_id is None:
        raise ValueError(f"arm must be one of {sorted(ARM_IDS)}, got {arm!r}")
    if not isinstance(data_paths, dict):
        raise DataBlocked("data_paths must be a mapping")
    for key in ("price_1day_dir",):
        if not isinstance(data_paths.get(key), str):
            raise DataBlocked(f"data_paths is missing the {key!r} path")

    grid_days, close_matrix = build_grid(data_paths["price_1day_dir"])
    if len(grid_days) <= WARMUP_DECISION_DAYS + 2:
        raise DataBlocked(
            f"intersection grid too short for the frozen {WARMUP_DECISION_DAYS}"
            f"-decision-day warmup: {len(grid_days)} grid days")
    shares, singular_count, returns = state_share_series(grid_days,
                                                         close_matrix)
    n = len(grid_days)
    s0_end_day = date.fromisoformat(S0_END)
    last_decision_i = max(i for i in range(n)
                          if grid_days[i] <= s0_end_day)

    counts = {
        REASON_UNDEFINED_STATE: 0,
        REASON_MISSING_TRAILING: 0,
        REASON_NOISE_FLOOR: 0,
        REASON_COLLISION: 0,
        REASON_END_OF_DATA: 0,
        REASON_BOUNDARY_DROP: 0,
        "decision_days_scanned": 0,
        "state_days": 0,
        "entry_days": 0,
        "state_undefined_days": 0,
    }
    decisions = []
    last_exit_index = {p: None for p in UNIVERSE}

    for i in range(WARMUP_DECISION_DAYS, last_decision_i + 1):
        reference = [shares[j] for j in range(i - REFERENCE_DAYS, i)]
        if any(v is None for v in reference):
            counts[REASON_UNDEFINED_STATE] += 1
            continue
        if shares[i] is None:
            counts[REASON_UNDEFINED_STATE] += 1
            continue
        threshold = percentile75(reference)
        if arm == "control":
            src = i - PLACEBO_SHIFT_DECISION_DAYS
            if src < WARMUP_DECISION_DAYS:
                continue  # shifted source state not yet defined (counted
                          # by the scan window, never inferred)
            src_ref = [shares[j] for j in range(src - REFERENCE_DAYS, src)]
            if any(v is None for v in src_ref) or shares[src] is None:
                counts[REASON_UNDEFINED_STATE] += 1
                continue
            active = shares[src] >= percentile75(src_ref)
            source_date = grid_days[src].isoformat()
        else:
            high = shares[i] >= threshold
            active = high if arm == "anchor" else (not high)  # neighbour:
                                                              # complement state
            source_date = None
        counts["decision_days_scanned"] += 1
        if active:
            counts["state_days"] += 1
        if not active:
            continue
        # fail-closed all-7-pairs trailing-close rule (structurally
        # guaranteed on the intersection grid, still enforced)
        if i - STATE_WINDOW < 0:  # pragma: no cover (warmup guarantees)
            counts[REASON_MISSING_TRAILING] += 1
            continue
        any_entry = False
        for pi, pair in enumerate(UNIVERSE):
            r_win = returns[i - STATE_WINDOW:i, pi]
            vol20 = float(np.std(r_win, ddof=1))
            cum10 = float(np.sum(returns[i - CUM_DAYS:i, pi]))
            if abs(cum10) < NOISE_FLOOR_MULT * vol20 * math.sqrt(CUM_DAYS):
                counts[REASON_NOISE_FLOOR] += 1
                continue
            le = last_exit_index[pair]
            if le is not None and le > i:   # position open at the signal
                counts[REASON_COLLISION] += 1
                continue
            entry_i = i + 1                 # first decision day after t
            exit_i = i + 1 + HOLD_DECISION_DAYS
            if exit_i >= n:
                counts[REASON_END_OF_DATA] += 1
                continue
            t_fold = fold_of_index(grid_days, i)
            x_fold = fold_of_index(grid_days, exit_i)
            if t_fold != x_fold:
                # exit fill crosses an internal fold boundary: DROPPED from
                # both books and counted (never truncated)
                counts[REASON_BOUNDARY_DROP] += 1
                continue
            last_exit_index[pair] = exit_i
            entry_day, exit_day = grid_days[entry_i], grid_days[exit_i]
            exit_decision_day = grid_days[exit_i - 1]
            decisions.append({
                "decision_id": f"{PROPOSAL_ID}-{arm}-{pair}-"
                               f"{grid_days[i].isoformat()}",
                "pair": pair,
                "side": -1 if cum10 > 0 else 1,       # FADE: -sign(cum10)
                "decision_ts": _iso(ny_decision_stamp(grid_days[i])),
                "notional_usd": NOTIONAL_USD,
                "entry_ts": _iso(ny_decision_stamp(entry_day)),
                "entry_price": float(close_matrix[entry_i, pi]),
                "exit_ts": _iso(ny_decision_stamp(exit_day)),
                "exit_price": float(close_matrix[exit_i, pi]),
                "exit_decision_ts": _iso(ny_decision_stamp(exit_decision_day)),
                "s_t": shares[i],
                "reference_percentile_threshold": threshold,
                "cum10": cum10,
                "vol20": vol20,
                "noise_floor_pass": True,
                "placebo_source_date": source_date,
                "force_flat": False,
                "boundary_crossing_dropped": False,
                "fold": t_fold,
                "state_high_source": ("placebo_state_t_minus_100"
                                      if arm == "control" else
                                      ("state_high" if arm == "anchor"
                                       else "state_complement")),
            })
            any_entry = True
        if any_entry:
            counts["entry_days"] += 1

    counts["state_undefined_days"] = counts[REASON_UNDEFINED_STATE]
    meta = {
        "proposal_id": PROPOSAL_ID,
        "family_id": FAMILY_ID,
        "cycle_id": CYCLE_ID,
        "arm": arm,
        "arm_id": arm_id,
        "decision_clock": DECISION_CLOCK,
        "alpha_definition": ALPHA_DEFINITION,
        "financing_formula_id": FINANCING_FORMULA_ID,
        "granularity": "daily decision closes only (1day snapshots)",
        "frozen_constants": {
            "state_window": STATE_WINDOW,
            "reference_days": REFERENCE_DAYS,
            "cum_days": CUM_DAYS,
            "hold_decision_days": HOLD_DECISION_DAYS,
            "noise_floor_mult": NOISE_FLOOR_MULT,
            "percentile": PERCENTILE,
            "percentile_method": PERCENTILE_METHOD,
            "placebo_shift_decision_days": (PLACEBO_SHIFT_DECISION_DAYS
                                            if arm == "control" else 0),
            "warmup_decision_days": WARMUP_DECISION_DAYS,
            "notional_usd_unit": NOTIONAL_USD,
            "universe": list(UNIVERSE),
            "s0_window": {"start": S0_START, "end": S0_END},
        },
        "fold_boundaries": list(FOLD_BOUNDARIES_P2),
        "fold_boundary_evidence": ("A9 measured thirds grid "
                                   "d2/a9_feasibility/FXFV6-A6-P2.json "
                                   "(sensitivity_fold_thirds_full_S0_grid)"),
        "grid_days": n,
        "grid_first_date": grid_days[0].isoformat(),
        "grid_last_date": grid_days[-1].isoformat(),
        "first_eligible_decision_date":
            grid_days[WARMUP_DECISION_DAYS].isoformat(),
        "singular_or_degenerate_correlation": singular_count,
        "skipped_counts": {kk: v for kk, v in sorted(counts.items())},
        "n_decisions": len(decisions),
    }
    return {"decisions": decisions, "meta": meta}
