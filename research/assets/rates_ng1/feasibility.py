"""RATES-NG1 P2 Q-6 feasibility census (no-PnL, no signals, no scoring).

P2 work items 1-3 (dispatch packet RATES-NG1 / rates-ng1-p2-feasibility).
The FROZEN floors were declared in the dispatch packet BEFORE any
measurement and are restated here as constants; they are measured
exactly and fail-closed per lane (a lane under floor dies cheap, plan
section 4):

- A5 curve-shape lane:
  * >= 1500 bookable daily decision instants post-2018-01-01 on the
    common curve-CSV x ETP-EOD grid AFTER a declared 252-trading-day
    warmup carve-out;
  * AND grid coverage >= 90% of common NY business days
    2018-01-01..2026-09-11.
- A4 auction lane: >= 150 grid-eligible auction announcement events
  post-2018-01-01 after PIT later-bound mapping (P1 clock semantics:
  end-of-announced-NY-day conservative bound; the same-day close is
  refused).

Declared measurement conventions (frozen with this module, never moved
retroactively):

- Common grid = dates that carry BOTH an official curve-CSV row AND an
  EOD bar for ALL FOUR frozen ETP legs (TLT/IEF/IEI/SHY), i.e. the
  strictest all-legs intersection, restricted to the window.
- Trading days = the common grid's own sessions (the DATA's calendar;
  no holiday calendar is invented -- P1 clock law).
- Warmup carve-out = the FIRST ``WARMUP_SESSIONS`` common-grid sessions
  of the window serve as history only: no decision instant is counted
  there (a 252-session rolling-history reserve for any future lane
  estimator).
- Bookable decision instant at session S (0-based index t >= warmup,
  t >= 1): the 16:00 America/New_York close of S materialized to UTC
  (P1 clock law); the V7-readable bar at that instant is dated the
  PREVIOUS common-grid session (close+1 availability law).
- Coverage denominator = Mon-Fri weekday count in the window (the same
  disclosed expectation convention as the P0 treasury census; holidays
  are not enumerated -- the data's own calendar is the calendar).
- Auction grid-eligibility = the event's PIT later-bound instant (end
  of the announced NY day) precedes some common-grid session close;
  the first such close is the event's first eligible decision.  The
  candidate index is found by bisection on the ordered session list
  (mathematically identical to the P1 clock scan because session closes
  are strictly increasing in session date); every materialized record
  carries the exact ``clock.pit_instant_for_day_event`` /
  ``clock.ny_close_utc`` instants, and a deterministic sample is
  cross-checked against ``clock.first_decision_after_pit`` itself.
- Worst-case round-trip cost ceiling per leg = ``CS p90 bps x 2`` (the
  stress tier charged once per fill on BOTH fills of the round trip;
  cost frequency once-per-fill is the frozen P1 contract law) ``+ ER
  drag`` for the declared holding convention (5 trading days held =
  7 calendar days of ACT/365F expense drag).  These are COST
  PROJECTIONS ONLY: no PnL, no outcome number, no expectancy anywhere.

No proposals, no signal design, no scoring, no PnL here.
"""

from __future__ import annotations

import bisect
import datetime as dt
import json
from typing import Any, Mapping, Sequence

from research.assets.rates_ng1 import clock as ck
from research.assets.rates_ng1.cost_model import bps

SCHEMA = "rates_ng1/feasibility@1"

# --------------------------------------------------------------------- #
# FROZEN FLOORS (declared in the dispatch packet BEFORE measurement)     #
# --------------------------------------------------------------------- #

FEASIBILITY_WINDOW = ("2018-01-01", "2026-09-11")
WARMUP_SESSIONS = 252
MIN_BOOKABLE_INSTANTS = 1500
MIN_GRID_COVERAGE_FRACTION = 0.90
MIN_GRID_ELIGIBLE_AUCTION_EVENTS = 150

# --------------------------------------------------------------------- #
# Declared cost-ceiling convention (frozen with this module)             #
# --------------------------------------------------------------------- #

ROUND_TRIP_SPREAD_MULTIPLIER = 2.0
HOLDING_TRADING_DAYS = 5
HOLDING_CALENDAR_DAYS_CHARGED = 7   # 5 trading days held ~= 7 calendar
                                    # days of ACT/365F expense drag


def expected_weekday_count(start_iso: str, end_iso: str) -> int:
    """Mon-Fri day count in [start, end] inclusive (the disclosed
    expectation convention shared with the P0 treasury census)."""
    d0 = dt.date.fromisoformat(start_iso)
    d1 = dt.date.fromisoformat(end_iso)
    n = 0
    d = d0
    while d <= d1:
        if d.weekday() < 5:
            n += 1
        d += dt.timedelta(days=1)
    return n


def in_window(iso: str, window: tuple[str, str]) -> bool:
    return window[0] <= iso <= window[1]


def build_common_grid(curve_dates: set[str],
                      etp_dates_by_ticker: Mapping[str, set[str]],
                      window: tuple[str, str] = FEASIBILITY_WINDOW
                      ) -> list[str]:
    """Common curve-CSV x ETP-EOD grid: dates carrying an official curve
    row AND an EOD bar for ALL frozen legs, inside ``window``
    (strictest all-legs intersection; ascending)."""
    common = {d for d in curve_dates if in_window(d, window)}
    for ticker, dates in etp_dates_by_ticker.items():
        common &= {d for d in dates if in_window(d, window)}
    return sorted(common)


def grid_census(common_grid: Sequence[str], *,
                warmup_sessions: int = WARMUP_SESSIONS,
                window: tuple[str, str] = FEASIBILITY_WINDOW) -> dict:
    """Bookable decision-instant census + coverage fraction.

    A session S at 0-based index ``t`` is a BOOKABLE decision instant
    iff ``t >= warmup_sessions`` (252-trading-day warmup carve-out) and
    ``t >= 1`` (a predecessor session exists, so the V7-readable bar
    dated the previous common-grid session exists).  The decision
    instant is S's 16:00 America/New_York close as UTC (P1 clock law;
    DST via the tz database).  Hand-computed small-fixture coverage in
    ``tests/test_rates_ng1_p2.py``.
    """
    grid = [str(d) for d in common_grid]
    if sorted(grid) != grid or len(set(grid)) != len(grid):
        raise ValueError("common grid must be ascending and unique")
    instants: list[dict[str, Any]] = []
    for t, s in enumerate(grid):
        if t < max(1, warmup_sessions):
            continue
        instants.append({
            "session_index": t,
            "decision_session": s,
            "decision_utc": ck.ny_close_utc(s).isoformat(),
            "readable_bar_date": grid[t - 1],
        })
    weekdays = sum(1 for d in grid
                   if dt.date.fromisoformat(d).weekday() < 5)
    denom = expected_weekday_count(window[0], window[1])
    return {
        "schema": SCHEMA,
        "window": list(window),
        "warmup_sessions": warmup_sessions,
        "grid_session_count": len(grid),
        "grid_dates": grid,
        "warmup_carveout_dates": grid[:warmup_sessions],
        "first_decision_session": (
            grid[warmup_sessions]
            if len(grid) > warmup_sessions else None),
        "bookable_instants": instants,
        "bookable_count": len(instants),
        "covered_weekdays": weekdays,
        "expected_weekdays_window": denom,
        "coverage_fraction": (round(weekdays / denom, 6) if denom else 0.0),
    }


def first_decision_index_after(announcement_date: str,
                               grid: Sequence[str]) -> int | None:
    """Index of the first grid session STRICTLY after ``announcement_date``
    (the P1 later-bound law: end-of-announced-NY-day PIT instant is
    strictly before the NEXT session's 16:00 close and strictly after
    the same-day close, so the eligible session is exactly the first
    session with date > announcement date).  None when no later session
    exists."""
    i = bisect.bisect_right([str(d) for d in grid], str(announcement_date))
    return i if i < len(grid) else None


def auction_grid_eligibility(events: Sequence[Mapping[str, Any]],
                             grid: Sequence[str],
                             cross_check_stride: int = 500,
                             cross_check_edges: int = 5) -> dict:
    """PIT later-bound grid-eligibility mapping for the census events.

    Per event: the exact PIT instant (``clock.pit_instant_for_day_event``,
    end of the announced NY day) and the exact first eligible decision
    (``clock.ny_close_utc`` of the first session STRICTLY after the
    announcement date); the same-day close is refused by construction
    (``same_day_close_eligible`` is False for every record).  A
    deterministic sample (first/last ``cross_check_edges`` + every
    ``cross_check_stride``-th event) is recomputed through
    ``clock.first_decision_after_pit`` itself and must agree exactly --
    the bisection fast path never drifts from the P1 clock authority.
    """
    grid_l = [str(d) for d in grid]
    grid_dates = [dt.date.fromisoformat(d) for d in grid_l]
    mappings: list[dict[str, Any]] = []
    ineligible: list[dict[str, Any]] = []
    for idx, ev in enumerate(events):
        ann = str(ev["announcementDate"])[:10]
        j = first_decision_index_after(ann, grid_l)
        pit = ck.pit_instant_for_day_event(ann)
        rec = {
            "event_index": idx,
            "cusip": ev.get("cusip"),
            "securityType": ev.get("securityType"),
            "securityTerm": ev.get("securityTerm"),
            "announcementDate": ann,
            "auctionDate": str(ev.get("auctionDate", ""))[:10],
            "pit_instant_utc": pit.isoformat(),
            "same_day_close_eligible": False,
        }
        if j is None:
            rec.update({"eligible": False, "decision_session": None,
                        "decision_utc": None,
                        "refusal": "NO_LATER_GRID_SESSION"})
            ineligible.append(rec)
        else:
            s = grid_l[j]
            rec.update({
                "eligible": True,
                "decision_session": s,
                "decision_utc": ck.ny_close_utc(s).isoformat(),
            })
        mappings.append(rec)

    # clock-authority cross-check on a deterministic sample
    sample_idx = sorted({*(i for i in range(min(cross_check_edges,
                                                   len(events)))),
                         *(i for i in range(
                             max(0, len(events) - cross_check_edges),
                             len(events))),
                         *range(0, len(events), max(1, cross_check_stride))})
    cross_check: list[dict[str, Any]] = []
    for i in sample_idx:
        ev = events[i]
        ann = str(ev["announcementDate"])[:10]
        authority = ck.first_decision_after_pit(ann, grid_dates)
        fast = mappings[i]
        agree = (
            (authority is None and not fast["eligible"])
            or (authority is not None and fast["eligible"]
                and authority["decision_session"] == fast["decision_session"]
                and authority["decision_utc"] == fast["decision_utc"]
                and authority["pit_instant_utc"] == fast["pit_instant_utc"]))
        cross_check.append({
            "event_index": i, "announcementDate": ann,
            "authority_decision_session": (authority or {}).get(
                "decision_session"),
            "fast_path_decision_session": fast["decision_session"],
            "agree": bool(agree),
        })
    if not all(c["agree"] for c in cross_check):
        raise ValueError(
            "auction eligibility fast path disagrees with the P1 clock "
            "authority on the deterministic sample: fail-closed")
    eligible = [m for m in mappings if m["eligible"]]
    by_type: dict[str, int] = {}
    for m in eligible:
        t = m["securityType"] or "UNKNOWN"
        by_type[t] = by_type.get(t, 0) + 1
    return {
        "schema": SCHEMA,
        "events_total": len(events),
        "eligible_count": len(eligible),
        "ineligible_count": len(ineligible),
        "ineligible": ineligible,
        "mappings": mappings,
        "eligible_by_security_type": by_type,
        "first_eligible_decision_session": (
            eligible[0]["decision_session"] if eligible else None),
        "last_eligible_decision_session": (
            eligible[-1]["decision_session"] if eligible else None),
        "clock_authority_cross_check": {
            "authority": "research/assets/rates_ng1/clock.py::"
                         "first_decision_after_pit",
            "sample_size": len(cross_check),
            "sample": cross_check,
            "all_agree": True,
        },
    }


def round_trip_cost_ceilings(contract: Mapping[str, Any], *,
                             holding_calendar_days: int =
                             HOLDING_CALENDAR_DAYS_CHARGED,
                             spread_multiplier: float =
                             ROUND_TRIP_SPREAD_MULTIPLIER) -> dict:
    """Projected WORST-CASE round-trip cost ceiling per leg, from the
    FROZEN tier-2.0 P1 cost contract only (constants cited by the
    contract sha256 at the call site):

        ceiling_bps = spread_multiplier x stress_tier_bps  (CS p90,
                      charged once per fill on BOTH fills of the round
                      trip; cost_frequency = once_per_fill)
                    + holding_calendar_days x drag_per_day_fraction
                      x 10^4   (ACT/365F expense drag over the declared
                      holding convention)

    COST PROJECTION ONLY: no PnL, no expectancy, no outcome number.
    """
    per_leg: dict[str, Any] = {}
    for ticker, rec in sorted(contract["per_etp"].items()):
        cs_p90 = rec["stress_tier_bps"]
        drag_day = rec["expense_drag"]["drag_per_day_fraction"]
        spread_rt = spread_multiplier * float(cs_p90)
        drag_rt = holding_calendar_days * float(drag_day) * 1e4
        per_leg[ticker] = {
            "cs_p90_stress_tier_bps": cs_p90,
            "round_trip_spread_bps": spread_rt,
            "er_drag_round_trip_bps": drag_rt,
            "worst_case_round_trip_ceiling_bps": spread_rt + drag_rt,
        }
    return {
        "schema": SCHEMA + ":cost_ceilings",
        "formula": ("worst_case_round_trip_ceiling_bps = "
                    f"{spread_multiplier} x cs_p90_stress_tier_bps + "
                    f"{holding_calendar_days} x drag_per_day_fraction x "
                    "1e4"),
        "holding_convention": {
            "holding_trading_days": HOLDING_TRADING_DAYS,
            "calendar_days_charged": holding_calendar_days,
            "drag_basis": "ACT/365F (frozen P1 contract: "
                          "drag_per_day_fraction = er_annual / 365)",
            "note": "5 trading days held ~= 7 calendar days of expense "
                    "drag; declared convention, never moved retroactively",
        },
        "spread_convention": {
            "round_trip_multiplier": spread_multiplier,
            "basis": "stress tier (CS p90) charged once per fill on BOTH "
                     "fills of the round trip; cost_frequency = "
                     "once_per_fill (frozen P1 contract law); worst case "
                     "= the stress tier on every fill",
        },
        "per_leg": per_leg,
        "no_pnl_note": "cost projection only; this census computes no "
                       "PnL, no expectancy and no outcome number (Q-6 "
                       "no-PnL law)",
    }


def deterministic_payload_sha256(payload: Any) -> str:
    """sha256 of the canonical JSON serialization (sort_keys, compact) --
    the drift detector for the committed census sidecar artifacts."""
    import hashlib
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()
