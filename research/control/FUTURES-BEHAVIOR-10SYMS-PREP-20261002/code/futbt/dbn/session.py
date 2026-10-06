"""Session calendar: UTC <-> exchange tz, DST-correct session boundaries,
absence-aware holiday/short-session detection, full-session reconstruction.

Exchange timezone is America/Chicago (all 10 roots trade on CME/CBOT/
NYMEX/COMEX Globex). DST correctness comes from zoneinfo — no manual
offset tables. Holiday calendars are NOT fetched (exchange pages were
transport-blocked in earlier stages); therefore holiday/short sessions
are inferred FROM THE DATA (absence-aware) and every such classification
is typed as inference (POSTULATED_WITH_DATA), never asserted as exchange
fact. Definitions bound the tradable window (activation..expiration).

Session-date convention used here: a record at exchange time T belongs
to the trading session dated the next weekday if T >= 17:00 CT else the
same weekday's session (CME-style 17:00 open, 16:00 close, 16:00-17:00
maintenance break excluded).
"""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from enum import Enum
from zoneinfo import ZoneInfo

from . import spec as _spec
from .ingest import Bar, ContractRegistry, Ingested
from ..taxonomy import PolicyError

CHICAGO = ZoneInfo("America/Chicago")
NS = 1_000_000_000
MINUTE = 60 * NS

DAILY_RTYPES = frozenset({_spec.RTYPE_OHLCV_1D, _spec.RTYPE_OHLCV_EOD})
_OHLCV_INTRADAY = frozenset({_spec.RTYPE_OHLCV_1S, _spec.RTYPE_OHLCV_1M,
                             _spec.RTYPE_OHLCV_1H})

SESSION_OPEN_CT = dt.time(17, 0)     # Globex open (synthetic convention)
SESSION_CLOSE_CT = dt.time(16, 0)    # Globex close
DEFAULT_EXPECTED_MINUTES = 23 * 60   # 17:00 -> 16:00 next day, minus break
SHORT_SESSION_RATIO = 0.85           # below this coverage -> SHORT (inferred)


def utc_to_exchange(ns: int) -> dt.datetime:
    return dt.datetime.fromtimestamp(ns / NS, tz=dt.timezone.utc).astimezone(CHICAGO)


def exchange_to_utc(wall: dt.datetime) -> int:
    if wall.tzinfo is None:
        wall = wall.replace(tzinfo=CHICAGO)
    return int(wall.timestamp()) * NS


class SessionKind(str, Enum):
    NORMAL = "NORMAL"
    DST_SHIFTED = "DST_SHIFTED"        # session spans a UTC-offset change
    HOLIDAY_SHORT = "HOLIDAY_SHORT"    # inferred from data (absence-aware)
    NO_DATA = "NO_DATA"                # weekday inside listing, zero records
    OUT_OF_LISTING = "OUT_OF_LISTING"  # outside activation..expiration


@dataclass(frozen=True)
class SessionWindow:
    date: dt.date
    open_utc_ns: int
    close_utc_ns: int
    kind: SessionKind
    inferred_short: bool = False       # True => classification is inference
    n_bars: int = 0
    coverage_ratio: float | None = None

    def contains(self, ts_ns: int) -> bool:
        return self.open_utc_ns <= ts_ns < self.close_utc_ns


def session_date_of(ts_ns: int) -> dt.date:
    """Exchange-date of the session a timestamp belongs to (>= 17:00 CT
    rolls to the NEXT weekday)."""
    local = utc_to_exchange(ts_ns)
    d = local.date()
    if local.time() >= SESSION_OPEN_CT:
        d = d + dt.timedelta(days=1)
    while d.weekday() >= 5:            # Sat/Sun belong to the next Monday
        d += dt.timedelta(days=1)
    return d


def _session_bounds(d: dt.date) -> tuple[int, int]:
    prev = d - dt.timedelta(days=1)
    open_ns = exchange_to_utc(dt.datetime.combine(prev, SESSION_OPEN_CT))
    close_ns = exchange_to_utc(dt.datetime.combine(d, SESSION_CLOSE_CT))
    return open_ns, close_ns


def _spans_dst_change(open_ns: int, close_ns: int) -> bool:
    return (utc_to_exchange(open_ns).utcoffset()
            != utc_to_exchange(close_ns).utcoffset()
            or utc_to_exchange(open_ns).utcoffset()
            != utc_to_exchange((open_ns + close_ns) // 2).utcoffset())


@dataclass
class SessionMap:
    raw_symbol: str
    sessions: dict  # date -> SessionWindow

    def window(self, d: dt.date) -> SessionWindow:
        return self.sessions[d]

    def reconstruction(self) -> list[dict]:
        """Full-session reconstruction: contiguous session windows with
        UTC boundaries (what a replayer iterates)."""
        return [
            {"date": w.date.isoformat(), "open_utc_ns": w.open_utc_ns,
             "close_utc_ns": w.close_utc_ns, "kind": w.kind.value,
             "inferred_short": w.inferred_short, "n_bars": w.n_bars,
             "coverage_ratio": w.coverage_ratio}
            for w in sorted(self.sessions.values(), key=lambda w: w.date)
        ]


def build_session_map(raw_symbol: str, bars: list[Bar],
                      registry: ContractRegistry,
                      expected_minutes: int = DEFAULT_EXPECTED_MINUTES
                      ) -> SessionMap:
    """Absence-aware session classification for one contract.

    Cadence-aware:
      * INTRADAY bars (1s/1m/1h): sessions derive from the data; every
        distinct session date observed via session_date_of becomes a
        window; short sessions are INFERRED from bar coverage
        (HOLIDAY_SHORT, inferred flag set); DST_SHIFTED marks windows whose
        UTC offset changes between open and close.
      * DAILY bars (ohlcv-1d = UTC-day aggregation per the Databento docs;
        ohlcv-eod = session-end): one bar per observed date, presence-only
        classification (coverage/short inference is meaningless at daily
        cadence and would mislabel every session); a UTC-midnight daily
        bar maps to the exchange session of that UTC date.
      * mixing intraday and daily rtypes in one call is ambiguous and
        raises (fail-closed).

    Weekday gaps between consecutive observed sessions are typed NO_DATA
    (cannot distinguish holiday from outage offline — typed as inference,
    never asserted)."""
    rt = {b.rtype for b in bars}
    if rt <= DAILY_RTYPES:
        cadence = "daily"
    elif rt <= _OHLCV_INTRADAY:
        cadence = "intraday"
    elif rt:
        raise PolicyError(
            f"build_session_map: mixed record cadences {sorted(rt)} for "
            f"{raw_symbol} — refusing an ambiguous session reconstruction")
    ident = registry.require(raw_symbol=raw_symbol)
    by_date: dict[dt.date, list[Bar]] = {}
    for b in sorted(bars, key=lambda b: b.ts_event):
        by_date.setdefault(session_date_of(b.ts_event), []).append(b)

    observed = sorted(by_date)
    sessions: dict[dt.date, SessionWindow] = {}

    for d in observed:
        day_bars = by_date[d]
        open_ns, close_ns = _session_bounds(d)
        kind = SessionKind.NORMAL
        inferred_short = False
        coverage = None
        if cadence == "intraday":
            last_bar = max(b.ts_event for b in day_bars)
            span_minutes = (last_bar - open_ns) / MINUTE
            coverage = round(max(0.0, min(1.0, span_minutes / expected_minutes)), 4)
            if _spans_dst_change(open_ns, close_ns):
                kind = SessionKind.DST_SHIFTED
            if coverage < SHORT_SESSION_RATIO:
                # short session INFERRED from absence of late bars (holiday
                # early close is the common cause; not asserted as fact)
                kind = SessionKind.HOLIDAY_SHORT
                inferred_short = True
        sessions[d] = SessionWindow(
            d, open_ns, close_ns, kind, inferred_short=inferred_short,
            n_bars=len(day_bars), coverage_ratio=coverage)

    # absence-aware NO_DATA: weekdays inside the observed span with no bars
    if observed:
        first, last = observed[0], observed[-1]
        cur = first
        while cur <= last:
            if cur.weekday() < 5 and cur not in sessions:
                sessions[cur] = SessionWindow(
                    cur, *_session_bounds(cur), SessionKind.NO_DATA)
            cur += dt.timedelta(days=1)
    return SessionMap(raw_symbol=raw_symbol, sessions=sessions)


def rth_slice(bars: list[Bar], rth_open: dt.time = dt.time(8, 30),
              rth_close: dt.time = dt.time(15, 0)) -> list[Bar]:
    """Filter bars to the RTH window in exchange time (default 08:30-15:00
    CT, the synthetic convention; per-symbol verification is the pilot's
    job, not assumed)."""
    out = []
    for b in bars:
        local = utc_to_exchange(b.ts_event).time()
        if rth_open <= local < rth_close:
            out.append(b)
    return out
