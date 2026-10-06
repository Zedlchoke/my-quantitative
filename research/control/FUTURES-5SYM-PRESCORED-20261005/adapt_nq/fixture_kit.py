"""fixture_kit — deterministic synthetic-panel construction for ADAPT-NQ fixtures.

Used ONLY by per-family fixtures/gen_fixtures.py scripts (which commit their
outputs). Nothing here touches real data; every number is engineered.
All timestamps are America/Chicago wall-clock ISO strings with offset.
ts = 1m bar START (D5 schema law carried, RC-1.3).
"""
from __future__ import annotations

from datetime import datetime, timedelta, date
from zoneinfo import ZoneInfo

from nq_common import ct_offset_str  # re-exported for generators

CT = ZoneInfo("America/Chicago")


def bar(session_date: str, hh: int, mm: int, o: float, h: float, lo: float, c: float,
        volume: int, contract: str) -> dict:
    d = date.fromisoformat(session_date)
    dt = datetime(d.year, d.month, d.day, hh, mm, tzinfo=CT)
    return {"ts": dt.isoformat(), "open": o, "high": h, "low": lo, "close": c,
            "volume": volume, "session_date": session_date, "contract": contract}


def minute_range(start_min: int, end_min: int):
    """Inclusive 1m starts [start, end) as (hh, mm) pairs."""
    m = start_min
    while m < end_min:
        yield divmod(m, 60)
        m += 1


def session_agg(session_date: str, *, open_: float, high: float, low: float, close: float,
                volume: int, rth_core_coverage: float, last_bar_ct: str,
                contract: str, extra: dict | None = None) -> dict:
    return {"session_date": session_date, "open": open_, "high": high, "low": low,
            "close": close, "volume": volume, "rth_core_coverage": rth_core_coverage,
            "last_bar_ct": last_bar_ct, "contract": contract, **(extra or {})}


def flat_walk_session(session_date: str, contract: str, *, start_min: int, end_min: int,
                      base: float, step: float, start_volume: int = 1000) -> list[dict]:
    """Deterministic 1m bars [start_min, end_min): each bar +`step` from the last close.
    Prices land on the 0.25 grid when base/step do."""
    out, px = [], base
    for hh, mm in minute_range(start_min, end_min):
        c = px + step
        out.append(bar(session_date, hh, mm, px, max(px, c), min(px, c), c,
                       start_volume, contract))
        px = c
    return out
