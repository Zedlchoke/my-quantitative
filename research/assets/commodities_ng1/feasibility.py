"""COMMODITIES-NG1 P2 Q-6 feasibility census (NO PnL, NO signal design).

Frozen floors (declared in the dispatch packet BEFORE this measurement;
measured against exactly, fail-closed per lane A4/A5):

    BOTH lanes (A4/A5), PER QUALIFYING MARKET-PAIR:
    (a) >= 300 grid-eligible weekly decision instants post-2018-01-01
        after a declared 52-week warmup carve-out; AND
    (b) >= 90% of expected weekly CoT releases on the window map to a
        measured ETP session on the decision grid.

    A pair under any floor is EXCLUDED from the bookable set and
    reported -- never silently dropped.

DECLARED CENSUS CONVENTIONS (frozen before measurement, applied exactly):

1. Window: decision instants whose release DATE (the Friday) is
   >= 2018-01-01 (WINDOW_START).
2. Release rule: the P0 frozen rule ``cot_census.release_instant``
   (Friday 15:30 America/New_York of the Tuesday-position week,
   DST-correct) is IMPORTED as the single source of the rule and is
   used verbatim for every Tuesday as-of date.  The measured substrate
   also contains 6 holiday-shifted MONDAY as-of dates (July-4 /
   Christmas / New-Year weeks); these are measured weekly releases and
   are never silently dropped: they take the SAME week-anchor rule --
   Friday 15:30 America/New_York of the Mon-Sun week containing the
   as-of date -- which reduces EXACTLY to the P0 rule for Tuesdays
   (asserted per-report at census time; any mismatch aborts
   fail-closed).  Any as-of weekday other than Tuesday/Monday is
   refused fail-closed.
3. Decision session: first MEASURED ETP session strictly after the
   release date (``clock.next_session_after`` on the pair's measured
   session calendar; holidays correct by construction).  A decision
   instant is GRID-ELIGIBLE iff its decision session exists.
4. Warmup carve-out: the FIRST 52 decision instants of the window
   (ordered by release) are warmup; BOTH floors are evaluated on the
   remaining counted window.
5. Instant floor (a): grid-eligible count on the counted window
   >= 300.
6. Coverage floor (b): the counted-window rows ARE the expected weekly
   CoT releases (every measured weekly report whose release falls in
   the window; expected = measured weekly cadence of the pair's CoT
   market).  Coverage = grid-eligible / expected on the counted
   window >= 0.90.
7. Cost ceiling (documentation only, NO PnL): per ETP pair-leg from the
   frozen P1 tier-2.0 cost contract: worst-case round-trip transaction
   ceiling = 2 fills x ``half_spread_frac_p90_per_fill`` (= the CS p90
   full spread, charged once per fill); expense component where
   ``MEASURED_OFFICIAL_PAGE``: ``expense_ratio_annual`` accrued over a
   DECLARED worst-case holding horizon of 10 trading days
   (expense is horizon-linear; the annual rate is reported alongside so
   any horizon can be reconstructed).  Legs with expense NOT_MEASURED
   are listed explicitly (transaction-only ceiling + fail-closed flag);
   downstream lanes treat them conservatively or exclude them.
   Constants are cited by sha256 of the frozen contract artifacts.

The census runs on the plane-consumed frozen substrate ONLY (NO
network): report dates from the sha256-pinned CoT weekly targets
surface, session calendars from the sha256-pinned ETP EOD surfaces.
"""

from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from research.assets.commodities_ng1.cot_census import (
    release_instant as p0_release_instant,
)
from research.assets.commodities_ng1.clock import (
    ClockRefused,
    next_session_after,
)

SCHEMA = "commodities_ng1/feasibility@1"

# -- frozen floors (dispatch packet; declared BEFORE measurement) ---- #
WINDOW_START = date(2018, 1, 1)
WARMUP_WEEKS = 52
INSTANT_FLOOR = 300
COVERAGE_FLOOR = 0.90

LANES = ("A4", "A5")

# -- declared cost-ceiling conventions -------------------------------- #
CEILING_HORIZON_TRADING_DAYS = 10
TRADING_DAYS_PER_YEAR = 252
EXPENSE_MEASURED_STATUS = "MEASURED_OFFICIAL_PAGE"

_ET_TZ = ZoneInfo("America/New_York")
_RELEASE_CLOCK = time(15, 30)

_ALLOWED_ASOF_WEEKDAYS = {1: "tuesday_p0_rule", 0: "monday_holiday_shift"}


class FeasibilityRefused(Exception):
    """Fail-closed feasibility refusal (never improvise, never drop)."""


def week_friday(report_date: date) -> date:
    """Friday of the Mon-Sun calendar week containing ``report_date``.

    For a Tuesday as-of date this equals ``report_date + 3 days`` --
    exactly the P0 rule's week anchor (asserted at census time).
    """
    monday = report_date - timedelta(days=report_date.weekday())
    return monday + timedelta(days=4)


def release_instant_for_report(report_date: date) -> tuple[datetime, str]:
    """Release instant + rule source for ONE measured as-of date.

    Tuesday -> the P0 frozen rule verbatim (imported, never
    re-derived).  Monday (measured CFTC holiday shift) -> the same
    week-anchor rule.  Anything else -> refused fail-closed.
    """
    kind = _ALLOWED_ASOF_WEEKDAYS.get(report_date.weekday())
    if kind is None:
        raise FeasibilityRefused(
            f"as-of date {report_date.isoformat()} is neither Tuesday nor "
            "Monday (measured holiday-shift set); fail closed")
    if kind == "tuesday_p0_rule":
        release = p0_release_instant(report_date)   # refuses non-Tuesdays
        # identity of the week anchor under the generalized rule:
        friday = week_friday(report_date)
        if release.date() != friday:
            raise FeasibilityRefused(
                f"P0 rule/week-anchor mismatch for {report_date.isoformat()}")
        return release, "p0_release_instant"
    local = datetime.combine(week_friday(report_date), _RELEASE_CLOCK,
                             tzinfo=_ET_TZ)
    return local.astimezone(timezone.utc), "week_anchor_holiday_shift"


def census_pair_grid(report_dates: list[date], session_dates: list[date],
                     window_start: date = WINDOW_START) -> dict:
    """Decision-grid census for ONE market-pair (measured inputs only).

    Returns the per-instant rows (release date, release instant, rule
    source, decision session) restricted to ``release_date >=
    window_start``, plus window-wide aggregates.  Fail-closed: non-Tue
    /non-Mon as-of dates, duplicate reports, unsorted/duplicate session
    calendars, and P0-rule identity violations are refusals.
    """
    reports = sorted(set(report_dates))
    if len(reports) != len(report_dates):
        raise FeasibilityRefused("duplicate report dates in pair grid input")
    sessions = sorted(set(session_dates))
    if len(sessions) != len(session_dates):
        raise FeasibilityRefused("duplicate session dates in pair grid input")
    if sessions and sessions != sorted(session_dates):
        raise FeasibilityRefused("session calendar not date-sorted")

    rows = []
    for d in reports:
        release, rule_source = release_instant_for_report(d)
        release_day = release.date()
        row = {
            "report_date": d.isoformat(),
            "release_date": release_day.isoformat(),
            "release_instant_utc": release.isoformat(),
            "rule_source": rule_source,
            "decision_session": None,
        }
        if release_day >= window_start:
            try:
                row["decision_session"] = next_session_after(
                    release_day, sessions).isoformat()
            except ClockRefused:
                # measured calendar exhausted after the release date:
                # the release does NOT map to a measured ETP session
                # (counted as unmapped, never dropped, never fabricated)
                row["decision_session"] = None
        rows.append(row)

    # window restriction is on the release date (declared convention 1)
    window_rows = [r for r in rows if r["release_date"]
                   >= window_start.isoformat()]
    grid_eligible = [r for r in window_rows if r["decision_session"]]
    return {
        "schema": SCHEMA,
        "window_start": window_start.isoformat(),
        "instants_window": len(window_rows),
        "instants_grid_eligible": len(grid_eligible),
        "unmapped_release_dates": [r["release_date"] for r in window_rows
                                   if not r["decision_session"]],
        "rows": rows,
    }


def evaluate_floors(grid: dict, warmup_weeks: int = WARMUP_WEEKS,
                    instant_floor: int = INSTANT_FLOOR,
                    coverage_floor: float = COVERAGE_FLOOR) -> dict:
    """Frozen floors (a)/(b) on ONE pair's census grid (fail-closed).

    The first ``warmup_weeks`` window instants (ordered by release) are
    the declared warmup carve-out; both floors are evaluated on the
    remaining counted window.
    """
    if grid.get("schema") != SCHEMA:
        raise FeasibilityRefused("evaluate_floors on a non-census grid")
    window_rows = sorted(
        (r for r in grid["rows"]
         if r["release_date"] >= grid["window_start"]),
        key=lambda r: r["release_date"])
    carved = window_rows[:warmup_weeks]
    counted = window_rows[warmup_weeks:]
    expected = len(counted)
    mapped_rows = [r for r in counted if r["decision_session"]]
    mapped = len(mapped_rows)
    coverage = (mapped / expected) if expected else 0.0
    instants_ok = mapped >= instant_floor
    coverage_ok = coverage >= coverage_floor
    return {
        "warmup_carve_out_instants": len(carved),
        "warmup_first_release": (carved[0]["release_date"]
                                 if carved else None),
        "warmup_last_release": (carved[-1]["release_date"]
                                if carved else None),
        "counted_expected_releases": expected,
        "counted_first_release": (counted[0]["release_date"]
                                  if counted else None),
        "counted_last_release": (counted[-1]["release_date"]
                                 if counted else None),
        "grid_eligible_instants": mapped,
        "unmapped_release_dates_counted": [r["release_date"]
                                           for r in counted
                                           if not r["decision_session"]],
        "release_to_session_coverage": round(coverage, 6),
        "floor_a_instants": {"frozen_floor": instant_floor,
                             "measured": mapped,
                             "verdict": "PASS" if instants_ok else "FAIL"},
        "floor_b_coverage": {"frozen_floor": coverage_floor,
                             "measured": round(coverage, 6),
                             "verdict": "PASS" if coverage_ok else "FAIL"},
        "pair_meets_floors": bool(instants_ok and coverage_ok),
    }


# -- cost ceilings (documentation only; NO PnL) ------------------------ #

def round_trip_cost_ceiling(leg: dict,
                            horizon_trading_days: int =
                            CEILING_HORIZON_TRADING_DAYS) -> dict:
    """Worst-case round-trip cost ceiling for ONE ETP pair-leg.

    From the frozen P1 tier-2.0 cost contract leg record:
    transaction = 2 fills x half-spread CS p90 (cost once per fill);
    expense where MEASURED_OFFICIAL_PAGE: annual rate accrued over the
    DECLARED horizon (linear).  NOT_MEASURED expense -> transaction-only
    ceiling + explicit fail-closed listing.
    """
    half = leg.get("half_spread_frac_p90_per_fill")
    if half is None:
        raise FeasibilityRefused(
            f"leg {leg.get('symbol')!r}: half-spread constant absent "
            "(cost contract incomplete; fail closed)")
    tx_frac = 2.0 * half
    tx_bps = tx_frac * 1e4
    fee = leg.get("expense_fact") or {}
    status = fee.get("status")
    rate = fee.get("expense_ratio_annual")
    expense_measured = status == EXPENSE_MEASURED_STATUS
    if expense_measured and rate is None:
        raise FeasibilityRefused(
            f"leg {leg.get('symbol')!r}: expense MEASURED but rate absent")
    horizon_frac = horizon_trading_days / TRADING_DAYS_PER_YEAR
    expense_bps_at_horizon = (rate * horizon_frac * 1e4) \
        if expense_measured else None
    ceiling_frac = tx_frac + (rate * horizon_frac
                              if expense_measured else 0.0)
    return {
        "symbol": leg["symbol"],
        "transaction_ceiling_frac_round_trip": tx_frac,
        "transaction_ceiling_bps_round_trip": round(tx_bps, 6),
        "fill_count_round_trip": 2,
        "half_spread_frac_p90_per_fill": half,
        "expense_status": status,
        "expense_ratio_annual": rate,
        "expense_bps_at_declared_horizon": (
            round(expense_bps_at_horizon, 6)
            if expense_bps_at_horizon is not None else None),
        "declared_horizon_trading_days": horizon_trading_days,
        "trading_days_per_year": TRADING_DAYS_PER_YEAR,
        "round_trip_cost_ceiling_bps": (
            round(ceiling_frac * 1e4, 6) if expense_measured else None),
        "expense_fail_closed": not expense_measured,
        "limitation": (None if expense_measured else
                       "expense fact NOT MEASURED (fail-closed): ceiling "
                       "is transaction-only; downstream lanes must treat "
                       "this leg conservatively or exclude it"),
    }
