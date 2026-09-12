"""VOL-NG1 P2 feasibility census (Q-6, no-PnL): decision grid, A5
realized-proxy determination, cost ceilings.

Task: vol-ng1-p2-feasibility.  Everything here is a MEASUREMENT over
the plane-consumed, event-adjusted substrate.  NO proposals, NO signal
design, NO scoring, NO PnL/outcome numbers anywhere.

FROZEN FLOORS (task objective, declared before this measurement; a
shortfall is recorded fail-closed, never renegotiated):

- A4 term-structure slope lane: >= 1500 bookable daily decision
  instants post-2015-01-01 on the common VIX9D x VIX x VIX3M x
  event-adjusted-ETP grid AFTER a declared 252-trading-day warmup
  carve-out; coverage >= 90% of common NY business days on the window.
- A5 risk-premium lane: >= 1000 bookable daily instants post-2015-01-01
  where the implied-vs-realized state is computable from GRANTED series
  ONLY; the realized proxy is declared explicitly below with its
  structural limitation recorded; no lawful granted-series proxy means
  the lane dies BLOCKED (a valid outcome; the cycle proceeds A4-only).
- Both lanes: worst-case round-trip cost ceiling per leg documented
  from the frozen ``p1_cost_contract.json`` (CS p90 x 2 fills +
  expense bps/day x declared holding convention + the applicable
  path-cost component), constants cited by sha256.

DECLARED MEASUREMENT CONVENTIONS (fixed before measurement):

- C1 Grid legs: the three granted CBOE index closes (VIX9D, VIX,
  VIX3M) and the EVENT-ADJUSTED close series of ALL SIX living ETP
  legs (VXX, UVXY, SVXY, VIXY, VIXM, VXZ).  Law: ETP legs are consumed
  ONLY through the event-adjusted layer
  (``research.assets.vol_ng1.corp_actions``) -- never raw, never
  vendor-adjusted.
- C2 Common grid = strict date-set intersection of all nine series.
- C3 Window = common-grid sessions with date >= 2015-01-01.
- C4 Warmup carve-out = the FIRST 252 common-grid sessions of the
  window (252 trading days on the grid itself).
- C5 Bookable instant = a post-warmup common-grid session that also
  has a NEXT common-grid session (V7 close+1 executability, per
  ``research.assets.vol_ng1.clocks``; the final session can never
  host a decision).
- C6 Coverage = bookable instants / NY business days (Mon-Fri, no
  holiday calendar assumed) in the measurement window
  ``[first_bookable_instant, last_common_grid_session]``.  The
  full-window variant (denominator spans the warmup too) is recorded
  as a disclosed secondary number; the floor is evaluated on the
  declared primary.
- C7 A5 realized proxy (declared): annualized trailing 21-common-grid-
  session realized volatility of the EVENT-ADJUSTED VXX close --
  ``rv = std(daily log returns over the trailing 21 sessions) *
  sqrt(252)``.  Implied side: the granted CBOE VIX close.  The state
  is computable at a bookable instant iff the trailing 21 sessions of
  the event-adjusted VXX series are fully populated on the grid ending
  at that instant (warmup sessions may serve the lookback -- that is
  the declared purpose of the warmup).  No state VALUES are recorded:
  only computability counts, first-computable date and the verdict.
- C8 A5 structural limitation (recorded verbatim): an ETP-leg realized
  vol is NOT S&P realized vol -- it is implied-complex realized vol:
  a leveraged, fee-bearing VIX-futures-complex instrument whose
  realized path embeds roll and decay.  The implied-vs-realized state
  computed under C7 is therefore an implied-vs-implied-complex proxy,
  never the classic implied-vs-spot-realized variance risk premium.
- C9 Cost ceiling (per leg, primary tier 2.0):
  ``ceiling_bps = 2 * execution_spread_bps_per_fill + expense_bps_per_day
  * H + adverse_path_tail_daily_bps * H`` with the declared holding
  convention ``H`` = the leg's own measured path ``day_gap`` (21
  sessions SHORT bucket, 90 sessions MID bucket) and
  ``adverse_path_tail_daily_bps = max(|p10_daily_bps|, |p90_daily_bps|)``
  from the frozen contract.  A ceiling is a cost bound, not an
  expectation and not a PnL number.
"""

from __future__ import annotations

import math
from datetime import date, timedelta

from research.assets.vol_ng1 import clocks as ck  # noqa: F401 (V7 law)

SCHEMA = "vol_ng1/feasibility@1"

#: C1 -- the nine grid legs (frozen consumption set, living legs only).
GRID_INDEX_LEGS = ("VIX9D", "VIX", "VIX3M")
GRID_ETP_LEGS = ("VXX", "UVXY", "SVXY", "VIXY", "VIXM", "VXZ")

#: C4 -- declared warmup carve-out (trading days on the common grid).
WARMUP_SESSIONS = 252

#: Frozen floor values (task objective; never renegotiated here).
POST_2015 = date(2015, 1, 1)
A4_FLOOR_INSTANTS = 1500
COVERAGE_FLOOR = 0.90
A5_FLOOR_INSTANTS = 1000

#: C7 -- declared A5 realized proxy.
PROXY_LEG = "VXX"
PROXY_LOOKBACK_SESSIONS = 21
PROXY_ANNUALIZATION = 252.0

#: The frozen cycle series ids carrying the A5 inputs (must match
#: ``research.assets.vol_ng1.plane_adapter`` exactly).
SERIES_ETP_EOD = "EODHD-F1:eodhd-vol-etp-eod"
SERIES_CBOE = "S7:cboe-vol-index-histories"

#: C9 -- declared holding conventions (the contract's own measured
#: path day_gap per bucket).
HOLD_SESSIONS_BY_BUCKET = {"SHORT": 21.0, "MID": 90.0}

A5_LIMITATION_TEXT = (
    "STRUCTURAL LIMITATION (declared, C8): the realized proxy is the "
    "realized volatility of the event-adjusted VXX close.  An ETP-leg "
    "realized vol is NOT S&P 500 realized vol -- it is implied-complex "
    "realized vol: a leveraged, fee-bearing VIX-futures-complex "
    "instrument whose realized path embeds roll and decay.  The "
    "implied-vs-realized state computed from it is an "
    "implied-vs-implied-complex proxy, never the classic "
    "implied-vs-spot-realized variance risk premium.")


class FeasibilityError(Exception):
    """Fail-closed census input: nothing inferred, nothing repaired."""


# --------------------------------------------------------------------------- #
# grid construction (C1-C3)
# --------------------------------------------------------------------------- #
def common_grid(index_closes: dict[str, dict[str, float]],
                etp_adj_closes: dict[str, dict[str, float]]) -> list[str]:
    """Strict date-set intersection of all nine grid legs (fail-closed
    on any missing or empty leg)."""
    sets: list[set[str]] = []
    for leg in GRID_INDEX_LEGS:
        s = index_closes.get(leg)
        if not s:
            raise FeasibilityError(
                f"grid index leg {leg!r} missing/empty: census refuses")
        sets.append(set(s))
    for leg in GRID_ETP_LEGS:
        s = etp_adj_closes.get(leg)
        if not s:
            raise FeasibilityError(
                f"grid ETP leg {leg!r} missing/empty: census refuses "
                "(consumption is ONLY through the event-adjusted layer)")
        sets.append(set(s))
    common = sets[0]
    for s in sets[1:]:
        common = common & s
    if not common:
        raise FeasibilityError("empty common grid: census refuses")
    return sorted(common)


def window_sessions(grid: list[str]) -> list[str]:
    """C3: the post-2015-01-01 common-grid sessions."""
    return [d for d in grid if date.fromisoformat(d) >= POST_2015]


def bookable_sessions(grid: list[str],
                      window: list[str]) -> tuple[list[str], list[str]]:
    """C4+C5: carve the warmup, then keep only sessions with a next
    common-grid session (V7 close+1 executability).

    Returns ``(bookable, dropped_tail)`` where ``dropped_tail`` records
    post-warmup sessions refused by the V7 law (the final session).
    """
    if len(window) <= WARMUP_SESSIONS:
        return [], []
    candidates = window[WARMUP_SESSIONS:]
    bookable: list[str] = []
    tail: list[str] = []
    for s in candidates:
        try:
            ck.next_session(grid, s)
            bookable.append(s)
        except ck.ClockError:
            tail.append(s)
    return bookable, tail


def ny_business_days_between(first_iso: str, last_iso: str) -> int:
    """Mon-Fri calendar count in [first, last] inclusive (no holiday
    calendar is assumed or invented)."""
    d0 = date.fromisoformat(first_iso)
    d1 = date.fromisoformat(last_iso)
    if d1 < d0:
        raise FeasibilityError("empty business-day span")
    n = 0
    d = d0
    while d <= d1:
        if d.weekday() < 5:
            n += 1
        d += timedelta(days=1)
    return n


def coverage_fraction(bookable: list[str], last_grid_date: str,
                      window: list[str] | None = None) -> dict:
    """C6: primary + disclosed secondary coverage over NY business
    days.

    Primary denominator: Mon-Fri dates in
    ``[first_bookable, last_grid_date]`` (the measurement window the
    bookable instants live in; the FLOOR is evaluated on this).
    Secondary denominator (disclosed, never gated): Mon-Fri dates over
    the FULL post-2015 window INCLUDING the warmup span.
    """
    if not bookable:
        return {"primary": 0.0, "full_window_secondary": 0.0,
                "primary_window": None, "denominator_primary": 0,
                "denominator_secondary_full_window": 0}
    first_b = bookable[0]
    denom_primary = ny_business_days_between(first_b, last_grid_date)
    out = {
        "primary": len(bookable) / denom_primary,
        "primary_window": [first_b, last_grid_date],
        "denominator_primary": denom_primary,
        "primary_note": "bookable instants / Mon-Fri dates in "
                        "[first_bookable, last_common_grid_session]",
    }
    if window:
        denom_full = ny_business_days_between(window[0], last_grid_date)
        out["full_window_secondary"] = len(bookable) / denom_full
        out["denominator_secondary_full_window"] = denom_full
        out["secondary_note"] = ("disclosed only, never gated: "
                                 "bookable instants / Mon-Fri dates "
                                 "over the full post-2015 window "
                                 "including the warmup span")
    return out


# --------------------------------------------------------------------------- #
# A4 lane
# --------------------------------------------------------------------------- #
def a4_lane(grid: list[str]) -> dict:
    """A4 term-structure slope lane census (counts + floor verdicts
    only; no signal, no outcome numbers)."""
    window = window_sessions(grid)
    bookable, tail = bookable_sessions(grid, window)
    cov = coverage_fraction(bookable, grid[-1], window)
    instants = len(bookable)
    cov_ok = cov["primary"] >= COVERAGE_FLOOR
    inst_ok = instants >= A4_FLOOR_INSTANTS
    return {
        "schema": SCHEMA,
        "lane": "A4_term_structure_slope",
        "grid_legs": {"indices": list(GRID_INDEX_LEGS),
                      "etp_event_adjusted": list(GRID_ETP_LEGS)},
        "grid_sessions_total": len(grid),
        "window_sessions_post_2015": len(window),
        "warmup_carveout_sessions": WARMUP_SESSIONS,
        "warmup_first_session": window[0] if window else None,
        "warmup_last_session": (window[WARMUP_SESSIONS - 1]
                                if len(window) >= WARMUP_SESSIONS else None),
        "first_bookable_instant": bookable[0] if bookable else None,
        "last_bookable_instant": bookable[-1] if bookable else None,
        "v7_tail_refused_sessions": tail,
        "bookable_instants": instants,
        "coverage_primary": round(cov["primary"], 6),
        "coverage_primary_denominator": cov["denominator_primary"],
        "coverage_primary_window": cov["primary_window"],
        "coverage_full_window_secondary_disclosed":
            round(cov["full_window_secondary"], 6),
        "coverage_secondary_denominator_full_window":
            cov.get("denominator_secondary_full_window"),
        "coverage_note": "FLOOR evaluated on coverage_primary only; "
                         "the full-window variant (warmup span in the "
                         "denominator) is disclosed, never gated (C6)",
        "frozen_floors": {
            "min_bookable_instants": A4_FLOOR_INSTANTS,
            "min_coverage": COVERAGE_FLOOR,
        },
        "verdict": "PASS" if (inst_ok and cov_ok) else "FAIL",
        "verdict_components": {"instants_ok": inst_ok,
                               "coverage_ok": cov_ok},
    }


# --------------------------------------------------------------------------- #
# A5 lane
# --------------------------------------------------------------------------- #
def realized_proxy_computable(adj_closes: dict[str, float],
                              grid: list[str]) -> dict:
    """C7 computability census for the declared proxy (NO state values
    recorded): at a bookable instant the trailing 21 common-grid
    sessions of the event-adjusted proxy leg must be fully populated."""
    n = len(grid)
    first_idx = None
    for i, s in enumerate(grid):
        if s not in adj_closes:
            continue
        need = [g for g in grid[max(0, i - PROXY_LOOKBACK_SESSIONS):i]]
        if len(need) == PROXY_LOOKBACK_SESSIONS and all(
                g in adj_closes for g in need):
            first_idx = i
            break
    if first_idx is None:
        return {"computable": False, "first_computable_instant": None,
                "grid_index_first_computable": None}
    return {"computable": True,
            "first_computable_instant": grid[first_idx],
            "grid_index_first_computable": first_idx}


def a5_lane(grid: list[str], proxy_adj_closes: dict[str, float],
            granted_verdicts: dict[str, str]) -> dict:
    """A5 risk-premium lane: declared-proxy computability determination
    (C7) on the A4 bookable grid.  Verdict FEASIBLE or BLOCKED -- a
    BLOCKED lane is a valid outcome (the cycle proceeds A4-only)."""
    window = window_sessions(grid)
    bookable, _tail = bookable_sessions(grid, window)
    # GRANTED-only law: the proxy leg consumes SERIES_ETP_EOD and the
    # implied side consumes SERIES_CBOE -- both verdicts must be
    # exactly GRANTED for the state to be lawful.
    required_series = {SERIES_ETP_EOD, SERIES_CBOE}
    missing = required_series - set(granted_verdicts)
    if missing:
        raise FeasibilityError(f"proxy series verdict unknown: {missing}")
    all_granted = all(v == "GRANTED"
                      for v in granted_verdicts.values())
    comp = realized_proxy_computable(proxy_adj_closes, grid)
    count = 0
    first_bookable_computable = None
    if comp["computable"]:
        bookable_set = set(bookable)
        for i, s in enumerate(grid):
            if s not in bookable_set:
                continue
            need_start = i - PROXY_LOOKBACK_SESSIONS
            window_ok = (need_start >= 0 and all(
                grid[k] in proxy_adj_closes
                for k in range(need_start, i)))
            if window_ok:
                count += 1
                if first_bookable_computable is None:
                    first_bookable_computable = s
    feasible = (all_granted and comp["computable"]
                and count >= A5_FLOOR_INSTANTS)
    return {
        "schema": SCHEMA,
        "lane": "A5_risk_premium_state",
        "implied_series": "S7:cboe-vol-index-histories VIX close (granted)",
        "realized_proxy_declared": (
            f"trailing {PROXY_LOOKBACK_SESSIONS}-common-grid-session "
            f"realized volatility of the event-adjusted {PROXY_LEG} "
            "close, annualized (x sqrt(252)) -- C7"),
        "proxy_lookback_sessions": PROXY_LOOKBACK_SESSIONS,
        "proxy_leg_first_adjusted_close": min(proxy_adj_closes)
        if proxy_adj_closes else None,
        "granted_series_verdicts": granted_verdicts,
        "all_inputs_granted": all_granted,
        "computable_at_all": comp["computable"],
        "first_computable_instant": comp["first_computable_instant"],
        "first_bookable_computable_instant": first_bookable_computable,
        "bookable_instants_state_computable": count,
        "frozen_floor": {"min_bookable_computable_instants":
                         A5_FLOOR_INSTANTS},
        "structural_limitation": A5_LIMITATION_TEXT,
        "no_state_values_recorded_note": (
            "computability census only: no state values, no "
            "distribution statistics, no outcomes (Q-6 no-PnL law)"),
        "verdict": "FEASIBLE" if feasible else "BLOCKED",
        "blocked_note": None if feasible else (
            "lane dies BLOCKED at P2; the cycle proceeds A4-only "
            "(valid outcome per the frozen task objective)"),
    }


# --------------------------------------------------------------------------- #
# cost ceilings (C9) -- from the FROZEN P1 contract
# --------------------------------------------------------------------------- #
def cost_ceilings(contract: dict) -> dict:
    """Worst-case round-trip cost ceiling per leg from the frozen
    ``p1_cost_contract.json`` (constants cited by sha256 at the gate
    level; per-leg expense source_sha256 as recorded in the contract).

    ``ceiling_bps = 2 * execution_spread_bps_per_fill(tier 2.0)
                 + expense_bps_per_day * H
                 + max(|p10|, |p90|) * H``
    with ``H`` = the leg's own measured path ``day_gap`` (declared
    holding convention, C9).  A ceiling is a cost bound, NOT an
    expectation and NOT a PnL number.
    """
    out: dict[str, dict] = {}
    for leg, block in sorted(contract["legs"].items()):
        tier2 = block["tiers"]["2.0"]
        path = block["path_cost"]
        bucket = block["bucket"]
        h = HOLD_SESSIONS_BY_BUCKET.get(bucket)
        if h is None:
            raise FeasibilityError(
                f"leg {leg}: bucket {bucket!r} has no declared holding "
                "convention")
        day_gap = float(path["day_gap"])
        if abs(day_gap - h) > 1e-9:
            raise FeasibilityError(
                f"leg {leg}: contract path day_gap {day_gap} != declared "
                f"holding convention {h}: refusing (C9 binds to the "
                "contract's own measured day_gap)")
        exec_per_fill = float(tier2["execution_spread_bps_per_fill"])
        expense_daily = float(tier2["expense_bps_per_day"])
        adverse_tail = max(abs(float(path["p10_daily_bps"])),
                           abs(float(path["p90_daily_bps"])))
        ceiling = (2.0 * exec_per_fill + expense_daily * h
                   + adverse_tail * h)
        out[leg] = {
            "bucket": bucket,
            "tier": "2.0",
            "holding_convention_sessions": h,
            "execution_spread_bps_per_fill": exec_per_fill,
            "execution_spread_bps_round_trip": 2.0 * exec_per_fill,
            "expense_bps_per_day": expense_daily,
            "expense_bps_over_holding": expense_daily * h,
            "path_formula": path["formula"],
            "path_day_gap": day_gap,
            "path_adverse_tail_daily_bps": adverse_tail,
            "path_adverse_tail_source": "max(|p10_daily_bps|, "
                                        "|p90_daily_bps|) from the "
                                        "frozen contract",
            "path_adverse_tail_over_holding": adverse_tail * h,
            "expense_source_sha256": block["expense"]["source_sha256"],
            "round_trip_cost_ceiling_bps": ceiling,
            "note": "worst-case COST CEILING at stress tier 2.0; a "
                    "bound, not an expectation, not a PnL number",
        }
    return {
        "schema": SCHEMA,
        "source": "research/control/vol_ng1_run/p1_cost_contract.json "
                  "(FROZEN, sha256 cited at the gate level)",
        "q8_law": contract.get("q8_law"),
        "q16_law": contract.get("q16_law"),
        "execution_note": contract.get("execution_note"),
        "legs": out,
    }
