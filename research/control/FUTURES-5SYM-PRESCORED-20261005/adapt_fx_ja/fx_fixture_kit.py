"""fx_fixture_kit — deterministic synthetic-panel construction for ADAPT-FXJA.

Used ONLY by per-family fixtures/gen_fixtures.py scripts (which commit their
outputs). Nothing here touches real data; every number is engineered.
All timestamps are UTC ISO strings (+00:00); ts = 1m bar START.
Window membership is resolved by the adapters in the LOCAL law clock
(Asia/Tokyo for 6J windows, Australia/Sydney for 6A) via zoneinfo — the
DST-correct bucketing law (SPEC_6J s.3 / SPEC_6A s.4).
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

UTC = timezone.utc


def bar(session_date: str, ts_utc: datetime, o: float, h: float, lo: float,
        c: float, volume: int, contract: str) -> dict:
    return {"ts": ts_utc.astimezone(UTC).isoformat().replace("+00:00", "+00:00"),
            "open": o, "high": h, "low": lo, "close": c, "volume": volume,
            "session_date": session_date, "contract": contract}


def minute_range(start_utc: datetime, end_utc: datetime):
    """Inclusive-of-start, exclusive-of-end 1m starts."""
    m = start_utc
    while m < end_utc:
        yield m
        m += timedelta(minutes=1)


def session_agg(session_date: str, *, open_: float, high: float, low: float,
                close: float, volume: int, last_bar_utc: str, contract: str,
                extra: dict | None = None) -> dict:
    return {"session_date": session_date, "open": open_, "high": high,
            "low": low, "close": close, "volume": volume,
            "last_bar_utc": last_bar_utc, "contract": contract, **(extra or {})}


def walk_session(session_date: str, start_utc: datetime, end_utc: datetime,
                 base: float, step: float, volume: int, contract: str,
                 *, tick: float) -> list[dict]:
    """Deterministic 1m bars [start_utc, end_utc): each bar +`step` from the
    last close; prices snap to `tick` (era-aware grid law)."""
    out, px = [], base
    for t in minute_range(start_utc, end_utc):
        c = round_to_tick(px + step, tick)
        out.append(bar(session_date, t, px, max(px, c), min(px, c), c,
                       volume, contract))
        px = c
    return out


def round_to_tick(px: float, tick: float) -> float:
    return round(round(px / tick) * tick, 10)


def utc(hh: int, mm: int) -> datetime:
    """Convenience: a UTC datetime on 1900-01-01 (caller adds the real date)."""
    return datetime(1900, 1, 1, hh, mm, tzinfo=UTC)


def at(d: str, hh_utc: int, mm_utc: int) -> datetime:
    from datetime import date as _date
    dd = _date.fromisoformat(d)
    return datetime(dd.year, dd.month, dd.day, hh_utc, mm_utc, tzinfo=UTC)


def at_local(d: str, hh: int, mm: int, tz) -> datetime:
    """Local-wall-clock timestamp in `tz` converted to UTC — the ONLY lawful
    way fixture bars are stamped (DST-correct bucketing law)."""
    from datetime import date as _date, datetime as _datetime
    from zoneinfo import ZoneInfo as _ZoneInfo
    dd = _date.fromisoformat(d)
    loc = _datetime(dd.year, dd.month, dd.day, hh, mm, tzinfo=_ZoneInfo(tz)
                    if isinstance(tz, str) else tz)
    return loc.astimezone(UTC)
