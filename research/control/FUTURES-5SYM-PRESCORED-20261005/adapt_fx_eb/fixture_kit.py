"""fixture_kit — deterministic synthetic-panel construction for ADAPT-FXEB.

Used ONLY by per-family fixtures/gen_fixtures.py scripts (which commit their
outputs). Nothing here touches real data; every number is engineered and all
contract labels carry a "-SYN" suffix so synthetic provenance is visible.
All timestamps are America/Chicago (or Europe/London, where the law anchors
there) wall-clock ISO strings with offset; ts = 1m bar START (D5 schema law).
London wall times are computed with zoneinfo — DST-correct by construction.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

CT = ZoneInfo("America/Chicago")
LONDON = ZoneInfo("Europe/London")

WARMUP_SESSIONS = 30          # >= 20 so ATR(20) resolves; deterministic weekdays
WARMUP_END = date(2026, 4, 14)


def weekday_dates(end: date, n: int) -> list[str]:
    """The n weekday session dates ending at `end` (inclusive)."""
    out, d = [], end
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d.isoformat())
        d -= timedelta(days=1)
    return list(reversed(out))


def ct(session_date: str, hh: int, mm: int) -> str:
    d = date.fromisoformat(session_date)
    return datetime(d.year, d.month, d.day, hh, mm, tzinfo=CT).isoformat()


def bar(session_date: str, hh: int, mm: int, o: float, h: float, lo: float, c: float,
        volume: int, contract: str) -> dict:
    return {"ts": ct(session_date, hh, mm), "open": o, "high": h, "low": lo,
            "close": c, "volume": volume, "session_date": session_date,
            "contract": contract}


def flat_bars(session_date: str, start_hm: tuple[int, int], end_hm: tuple[int, int],
              px: float, volume: int, contract: str,
              step: float = 0.0, overrides: dict[int, dict] | None = None) -> list[dict]:
    """Deterministic 1m bars over CT minutes [start, end): flat walk (or +`step`
    per bar). `overrides` maps an absolute CT minute -> full bar spec so single
    bars can be shaped (release spikes, reopen prints) without breaking the walk."""
    out, px0, m = [], px, start_hm[0] * 60 + start_hm[1]
    end = end_hm[0] * 60 + end_hm[1]
    ov = overrides or {}
    while m < end:
        o = px0
        c = round(px0 + step, 10)
        spec = ov.get(m)
        if spec is None:
            b = bar(session_date, m // 60, m % 60, o, max(o, c), min(o, c), c,
                    volume, contract)
        else:
            b = bar(session_date, m // 60, m % 60, spec["open"], spec["high"],
                    spec["low"], spec["close"], spec.get("volume", volume), contract)
            c = spec["close"]
        out.append(b)
        px0 = c
        m += 1
    return out


def warmup_sessions(sym: str, contract: str, end: date | None = None) -> tuple[list[dict], float]:
    """`WARMUP_SESSIONS` prior weekday held-session aggregates with a constant
    daily range -> ATR(20) = range exactly. Returns (sessions, atr20)."""
    end = end or WARMUP_END
    rng = 0.0010 if sym == "6E" else 0.0020
    base = 1.10010 if sym == "6E" else 1.30010
    sessions = [{"session_date": d, "open": base, "high": round(base + rng / 2, 10),
                 "low": round(base - rng / 2, 10), "close": base, "volume": 1000,
                 "contract": contract, "last_bar_ct": "16:00"}
                for d in weekday_dates(end, WARMUP_SESSIONS)]
    return sessions, rng


def panel(sym: str, contract: str, sessions: list[dict], bars: list[dict],
          calendar: dict | None = None) -> dict:
    return {"schema": "adapt_fx_eb/synthetic_panel@1", "provenance": "SYNTHETIC",
            "symbol": sym, "contract": contract,
            "sessions": sessions, "bars": bars, "calendar": calendar or {}}
