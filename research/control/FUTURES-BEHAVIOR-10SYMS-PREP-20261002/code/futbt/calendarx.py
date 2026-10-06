"""Exchange calendar / DST placeholder interface.

The real CME/NYMEX/COMEX holiday calendars and DST-accurate session times are
NOT available offline in this prep (exchange pages transport-blocked on
2026-10-02; holiday calendars NOT_RUN). We therefore define a narrow protocol
and ship a deterministic synthetic weekday calendar used by tests/fixtures.

Any code path that needs the REAL calendar must call
`require_real_calendar()`, which raises `PolicyError` with an explicit
NOT_RUN marker — it must never silently fall back to the weekday calendar.
"""
from __future__ import annotations

import datetime as dt
from abc import ABC, abstractmethod
from bisect import bisect_left, bisect_right

from .taxonomy import Evidence, EvidenceTag, PolicyError

REAL_CALENDAR_STATUS = Evidence(
    tag=EvidenceTag.NOT_RUN,
    note="real CME/NYMEX/COMEX holiday calendars + DST-accurate session "
         "boundaries not fetched (cmegroup.com transport-blocked 2026-10-02). "
         "Synthetic weekday calendar is for fixtures/tests only.",
)


class ExchangeCalendar(ABC):
    """Minimal session-calendar interface the roll engine depends on."""

    @abstractmethod
    def sessions(self) -> list[dt.date]:
        """All sessions, ascending, unique."""

    @abstractmethod
    def tz_name(self) -> str:
        """IANA timezone the daily bar dates are expressed in."""

    def is_session(self, d: dt.date) -> bool:
        s = self.sessions()
        i = bisect_left(s, d)
        return i < len(s) and s[i] == d

    def next_session(self, d: dt.date, inclusive: bool = False) -> dt.date:
        s = self.sessions()
        i = bisect_left(s, d) if inclusive else bisect_right(s, d)
        if i < len(s):
            return s[i]
        raise KeyError(f"no session on/after {d}")

    def prev_session(self, d: dt.date, inclusive: bool = False) -> dt.date:
        s = self.sessions()
        i = bisect_right(s, d) if inclusive else bisect_left(s, d)
        if i - 1 >= 0:
            return s[i - 1]
        raise KeyError(f"no session on/before {d}")

    def last_session_before(self, d: dt.date) -> dt.date:
        """Greatest session strictly before `d` (KeyError if none)."""
        s = self.sessions()
        i = bisect_left(s, d)
        if i - 1 >= 0:
            return s[i - 1]
        raise KeyError(f"no session strictly before {d}")

    def sessions_between(self, a: dt.date, b: dt.date, inclusive: bool = True) -> list[dt.date]:
        s = self.sessions()
        lo = bisect_left(s, a) if inclusive else bisect_right(s, a)
        hi = bisect_right(s, b) if inclusive else bisect_left(s, b)
        return s[lo:hi]

    def session_index(self, d: dt.date) -> int:
        s = self.sessions()
        i = bisect_left(s, d)
        if i >= len(s) or s[i] != d:
            raise KeyError(f"{d} is not a session")
        return i

    def provenance(self) -> Evidence:
        return Evidence(
            tag=EvidenceTag.POSTULATED,
            note="synthetic calendar — no holiday/DST accuracy claimed",
        )


class WeekdayCalendar(ExchangeCalendar):
    """Mon-Fri calendar with no holidays and no DST awareness.

    Deterministic; used for synthetic fixtures and offline tests ONLY.
    Real-date use must go through `require_real_calendar`.
    """

    def __init__(self, start: dt.date, end: dt.date, tz: str = "Synthetic/NoDST"):
        self._tz = tz
        days: list[dt.date] = []
        d = start
        while d <= end:
            if d.weekday() < 5:
                days.append(d)
            d += dt.timedelta(days=1)
        if not days:
            raise ValueError("empty calendar")
        self._sessions = days

    def sessions(self) -> list[dt.date]:
        return list(self._sessions)

    def tz_name(self) -> str:
        return self._tz

    def provenance(self) -> Evidence:
        return Evidence(
            tag=EvidenceTag.POSTULATED,
            note="WeekdayCalendar: synthetic Mon-Fri; holidays NOT_RUN, DST NOT_RUN",
        )


def require_real_calendar(what_for: str) -> None:
    """Call before any code path that would need the true exchange calendar."""
    raise PolicyError(
        f"NOT_RUN: real exchange calendar required for '{what_for}' but "
        f"{REAL_CALENDAR_STATUS.note}"
    )


def calendar_from_bars(dates: list[dt.date], tz: str) -> ExchangeCalendar:
    """Empirical calendar: sessions = sorted unique dates present in raw bars.

    This is OBSERVED (from data) but reflects the bar stream, including any
    fetch gaps — document that caveat when using it.
    """

    class _Empirical(ExchangeCalendar):
        def __init__(self, days, tz):
            uniq = sorted(set(days))
            if not uniq:
                raise ValueError("no dates")
            self._s = uniq
            self._tz = tz

        def sessions(self):
            return list(self._s)

        def tz_name(self):
            return self._tz

        def provenance(self):
            return Evidence(
                tag=EvidenceTag.OBSERVED,
                script="futbt.calendarx.calendar_from_bars",
                window=f"{self._s[0]}..{self._s[-1]} ({len(self._s)} sessions)",
                note="union of dates in the loaded bars; holiday-vs-fetch-gap "
                     "distinction NOT_RUN",
            )

    return _Empirical(dates, tz)
