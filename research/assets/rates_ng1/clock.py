"""RATES-NG1 P1 decision-clock identity: daily NY-close grid + auction
PIT anchoring.

P1 work item 3 (dispatch packet RATES-NG1 / rates-ng1-p1-kernel-costs).
Plan section 5 law:

- Clock: daily NY-close decision grid on EODHD EOD ETP bars; the
  availability convention is "bar readable close+1 session" (V7 law):
  the EOD bar DATED session S may first inform a decision at the NY
  close of the NEXT session (never at S's own close).

- UTC/NY DST handling is mandatory-fixture territory: every decision
  instant is materialized through zoneinfo(America/New_York) at 16:00
  NY and converted to UTC.  No hardcoded UTC offsets live here.

- Auction-instant PIT anchoring: the P0 auction census carries official
  ``announcementDate`` values at DAY granularity (no intraday
  timestamp is evidenced).  Per the house availability law (RULES.md:
  "conservative LATER bound when unevidenced"), a day-dated official
  event becomes a decision-clock input only AFTER its PIT instant,
  defined here as the END of the announced NY day (23:59:59 NY).  The
  first eligible decision is therefore the first session whose NY close
  is strictly after that instant -- which lands on the close+1 session
  relative to the announcement date, and REFUSES the same-day close.

No signals, no proposals, no scoring here: this module produces
timestamps and calendar facts only.
"""

from __future__ import annotations

from datetime import date, datetime, time, timezone
from zoneinfo import ZoneInfo

SCHEMA = "rates_ng1/clock@1"

#: Decision-grid instant: the NY equity close (V7 daily-grid law).
DECISION_HOUR_NY = 16
DECISION_MINUTE_NY = 0

NY = ZoneInfo("America/New_York")
UTC = timezone.utc


def ny_close_utc(session_date: date) -> datetime:
    """The 16:00 America/New_York instant of ``session_date`` as an
    aware UTC datetime (DST handled by the tz database)."""
    d = session_date if isinstance(session_date, date) \
        else date.fromisoformat(str(session_date))
    local = datetime.combine(d, time(DECISION_HOUR_NY, DECISION_MINUTE_NY),
                             tzinfo=NY)
    return local.astimezone(UTC)


def sessions_from_bars(bar_dates: list[str]) -> list[date]:
    """Session calendar from the EOD bar dates (ascending, deduped):
    the session calendar is the DATA's own calendar -- no holiday
    calendar is invented."""
    seen = sorted({str(d) for d in bar_dates})
    return [date.fromisoformat(s) for s in seen]


def next_session(bar_date: str | date, sessions: list[date]) -> date | None:
    """First session STRICTLY after ``bar_date`` (the close+1 session of
    the V7 availability law); None when no later session exists."""
    d = bar_date if isinstance(bar_date, date) \
        else date.fromisoformat(str(bar_date))
    later = [s for s in sessions if s > d]
    return later[0] if later else None


def decision_instant_for_bar(bar_date: str | date,
                             sessions: list[date]) -> dict | None:
    """V7 law: the EOD bar dated ``bar_date`` is first readable as a
    decision input at the NY close of the NEXT session.  Returns
    ``{"bar_date", "decision_session", "decision_utc"}`` or None when
    the bar has no later session (end-of-data bar is never readable)."""
    nxt = next_session(bar_date, sessions)
    if nxt is None:
        return None
    return {
        "bar_date": str(bar_date),
        "decision_session": nxt.isoformat(),
        "decision_utc": ny_close_utc(nxt).isoformat(),
    }


def decision_grid(sessions: list[date]) -> list[dict]:
    """The full decision grid: for every session with a successor, the
    16:00-NY decision instant as UTC (DST transitions visible as the
    21:00Z <-> 20:00Z flip)."""
    out: list[dict] = []
    for s in sessions:
        rec = decision_instant_for_bar(s, sessions)
        if rec is not None:
            out.append(rec)
    return out


def pit_instant_for_day_event(event_date: str | date) -> datetime:
    """Conservative LATER-bound PIT instant for an OFFICIAL event that is
    evidenced at DAY granularity only (the P0 auction census
    ``announcementDate`` shape): end of the announced NY day
    (23:59:59.999999 America/New_York) as UTC."""
    d = event_date if isinstance(event_date, date) \
        else date.fromisoformat(str(event_date))
    local = datetime.combine(d, time(23, 59, 59, 999999), tzinfo=NY)
    return local.astimezone(UTC)


def first_decision_after_pit(event_date: str | date,
                             sessions: list[date]) -> dict | None:
    """First session whose 16:00-NY close is STRICTLY AFTER the event's
    PIT instant (day-dated auction announcement -> next session's
    close; the same-day close is refused by construction)."""
    pit = pit_instant_for_day_event(event_date)
    for s in sessions:
        close = ny_close_utc(s)
        if close > pit:
            return {
                "event_date": str(event_date),
                "pit_instant_utc": pit.isoformat(),
                "decision_session": s.isoformat(),
                "decision_utc": close.isoformat(),
                "same_day_close_eligible": False,
            }
    return None
