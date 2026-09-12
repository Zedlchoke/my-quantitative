"""COMMODITIES-NG1 P1 weekly decision-grid clock + kernel-side PIT guard.

Plan section 5 clock identity:

- weekly decision grid: CoT release (Friday 15:30 America/New_York,
  DST-correct) -> next ETP session decisions; daily EOD bars for
  execution and stops;
- V7 law: daily bars are readable CLOSE+1 -- a bar dated D carries
  D's 16:00 ET close and may inform decisions only from then on
  (never inside D's own session);
- PIT law: CFTC position data is usable only after the P0-pinned
  release rule.  The P0 plane guard lives in
  ``research/assets/commodities_ng1/cot_census.py``
  (``release_instant`` / ``pit_guard``) and the plane adapter enforces
  it at consumption; THIS module is the kernel-side wiring: the same
  rule IMPORTED (never re-derived) and applied to the decision grid,
  with fail-closed refusal when a caller asks for position data
  before its release instant.

The executable session of a release is the first ETP session STRICTLY
after the release date, taken from the MEASURED session calendar of
the substrate (never a weekday rule): exchange holidays are correct
by construction.
"""

from __future__ import annotations

from datetime import date, datetime, time, timezone
from zoneinfo import ZoneInfo

from research.assets.commodities_ng1.cot_census import (  # noqa: F401
    pit_guard,           # P0 plane guard, imported for kernel-side reuse
    release_instant,     # the single source of the release rule
)

SCHEMA = "commodities_ng1/clock@1"

#: US ETP regular-session close (America/New_York); the close+1
#: readability anchor (V7 law).
_ET_TZ = ZoneInfo("America/New_York")
_SESSION_CLOSE = time(16, 0)

#: Same rule object as the P0 plane guard (identity kept auditable).
RELEASE_CLOCK_RULE = "Friday 15:30 America/New_York of the " \
    "Tuesday-position week (DST-correct), expressed UTC"


class KernelPitRefused(Exception):
    """Kernel-side PIT refusal: position data requested before its
    release instant (same semantics as the P0 plane guard)."""


class ClockRefused(Exception):
    """Fail-closed clock refusal (non-Tuesday report date, session
    calendar exhausted, malformed inputs)."""


def bar_close_instant_utc(bar_date: date) -> datetime:
    """Close instant of the ETP session ``bar_date`` (16:00 ET,
    DST-correct, expressed UTC)."""
    local = datetime.combine(bar_date, _SESSION_CLOSE, tzinfo=_ET_TZ)
    return local.astimezone(timezone.utc)


def bar_readable(bar_date: date, use_instant_utc: datetime) -> bool:
    """V7 close+1 readability: bar ``bar_date`` is readable iff its
    session close instant is <= ``use_instant_utc``."""
    if use_instant_utc.tzinfo is None:
        use_instant_utc = use_instant_utc.replace(tzinfo=timezone.utc)
    return bar_close_instant_utc(bar_date) <= use_instant_utc


def next_session_after(d: date, session_dates: list[date]) -> date:
    """First MEASURED session strictly after ``d`` (fail-closed when
    the calendar is exhausted; holidays are correct by construction
    because the calendar comes from the substrate)."""
    later = [s for s in session_dates if s > d]
    if not later:
        raise ClockRefused(
            f"session calendar exhausted after {d.isoformat()}; "
            "no executable session exists")
    return min(later)


def kernel_pit_visible_report_dates(report_dates: list[date],
                                    use_instant_utc: datetime
                                    ) -> list[date]:
    """Kernel-side PIT view: report dates whose release instant is <=
    ``use_instant_utc`` (delegates to the P0 ``pit_guard`` per report;
    identical semantics, wired kernel-side)."""
    visible = []
    for d in report_dates:
        g = pit_guard(d, use_instant_utc)
        if g["pit_allowed"]:
            visible.append(d)
    return sorted(visible)


def kernel_pit_require_visible(report_date: date,
                               use_instant_utc: datetime) -> dict:
    """Fail-closed kernel-side PIT gate for ONE report: returns the
    guard envelope when visible, raises ``KernelPitRefused`` when the
    report is still withheld (position data before its release instant
    can never flow through a kernel consumer)."""
    g = pit_guard(report_date, use_instant_utc)
    if not g["pit_allowed"]:
        raise KernelPitRefused(
            f"PIT violation (kernel-side): report {report_date.isoformat()} "
            f"withheld until {g['release_instant_utc']}; use_instant "
            f"{g['use_instant_utc']}")
    return g


def weekly_decision_grid(report_dates: list[date],
                         session_dates: list[date]) -> list[dict]:
    """The weekly decision grid rows (plan section 5).

    Per CoT report (Tuesday position week):
    - ``release_instant_utc``: Friday 15:30 ET of that week (P0 rule);
    - ``decision_session``: first measured ETP session strictly after
      the release date (the "next ETP session decisions" anchor);
    - ``cot_visible_at_release``: every report legally visible at the
      release instant (kernel-side PIT view) -- includes this report;
    - ``bars_readable_at_decision``: sessions whose 16:00 ET close is
      at/before the release instant.  The release date's OWN bar is
      NOT readable (its close 16:00 ET is after the 15:30 release) --
      the V7 close+1 law, DST/holiday-correct by construction.
    """
    rows = []
    for d in sorted(report_dates):
        release = release_instant(d)          # refuses non-Tuesdays
        release_day = release.date()          # the Friday (UTC instant
        # of 19:30/20:30Z shares the NY calendar day)
        decision_session = next_session_after(release_day, session_dates)
        visible = kernel_pit_visible_report_dates(report_dates, release)
        readable = [s for s in sorted(set(session_dates))
                    if bar_readable(s, release)]
        rows.append({
            "schema": SCHEMA,
            "report_date": d.isoformat(),
            "release_instant_utc": release.isoformat(),
            "release_date": release_day.isoformat(),
            "decision_session": decision_session.isoformat(),
            "cot_visible_at_release": [v.isoformat() for v in visible],
            "bars_readable_at_decision": [s.isoformat() for s in readable],
            "release_date_bar_readable": bar_readable(release_day,
                                                      release),
        })
    return rows
