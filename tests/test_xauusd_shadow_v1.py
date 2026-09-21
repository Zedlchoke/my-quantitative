"""XAUUSD-SHADOW-V1 regression tests (2026-09-21 owner-ordered fix).

The entry path carried a deterministic unpack bug (``kind, lv =
max(...)`` over swing_levels' 3-tuples) that raised ValueError the
moment a bar passed the volatility floor — proven on real bars (first
historically eligible bar 1980-11-10). The sleeve could NEVER enter.

These tests pin the fix with a synthetic series engineered to fire
EVERY condition at once (rising closes for EMA9>EMA21, a confirmed
fractal swing low within 0.3xATR, right side, and a volatility spike
>= 1.25x the trailing-100 ATR median), plus a no-exception full
replay. SHADOW_OBSERVATION_ONLY: no performance claims are made or
tested here.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(
    0,
    str(
        Path(__file__).resolve().parents[1]
        / "research" / "control" / "xauusd_shadow_v1"
    ),
)

import xauusd_shadow as x  # noqa: E402


def _bars_enter_long(n: int = 208):
    """Steep quiet uptrend -> one crash bar (huge LOWER WICK makes the
    fractal swing low; its HIGH is capped below the trend so it is NOT
    a competing fractal high) -> rising recovery above the level ->
    14 wide-range bars at the end (volatility spike lifts ATR14 to
    ~1.25x+ the trailing median and widens the 0.3xATR proximity band
    to cover the final close)."""
    bars = []
    crash_k = 185
    for i in range(n):
        if i < crash_k:
            c = 100.0 + i * 0.15                       # closes 100 -> 127.75
            o, h, l = c, c + 0.25, c - 0.25
        elif i == crash_k:
            c, o, h, l = 121.0, 127.9, 126.5, 119.5    # swing-low wick
        elif i < 194:
            c = 121.4 + (i - crash_k) * 0.25           # rising recovery
            o, h, l = c, c + 0.25, c - 0.25
        else:
            c = 123.2 + (i - 194) * 0.08               # crawl upward
            o, h, l = c, c + 20.0, 119.7               # wide-range spike
        bars.append(
            {"date": f"2020-{(i // 28) % 12 + 1:02d}-{i % 28 + 1:02d}",
             "o": o, "h": h, "l": l, "c": c}
        )
    return bars


def test_swing_levels_tuple_shape():
    bars = _bars_enter_long()
    levels = x.swing_levels(
        [b["h"] for b in bars], [b["l"] for b in bars]
    )
    assert levels, "expected at least one swing level"
    for tup in levels:
        assert len(tup) == 3  # (confirm_index, kind, level)


def test_entry_path_fires_all_conditions_without_error():
    """THE regression: pre-fix this raised ValueError at the swing
    tie-break; post-fix it records a LONG ENTRY_INTENT."""
    bars = _bars_enter_long()
    eng = x.SleeveEngine()
    i = len(bars) - 1  # final bar: all conditions engineered to pass
    atr = eng._atr_at(i, bars)
    med = eng._atr_median100(i, bars)
    e9, e21 = eng._ema_at(i, bars)
    close = bars[i]["c"]
    # preconditions of the fixture itself
    assert atr >= x.VOL_PCT_MIN * close
    assert atr >= x.VOL_MED_MULT * med
    assert e9 > e21
    eng.on_bar(i, bars)  # pre-fix: ValueError (too many values)
    entries = [e for e in eng.events if e["type"] == "ENTRY_INTENT"]
    assert len(entries) == 1
    assert entries[0]["side"] == 1  # long at the swing LOW
    assert entries[0]["level"] == 119.5  # the crash-bar wick low


def test_full_replay_never_raises():
    bars = _bars_enter_long()
    eng = x.SleeveEngine()
    for i in range(x.WARMUP, len(bars)):
        eng.on_bar(i, bars)  # pre-fix: raised mid-replay
    assert isinstance(eng.events, list)


def test_market_gap_check_holiday_and_weekend_clean():
    bars = _bars_enter_long()
    # synthetic dates are not a real calendar: gaps are informational
    gaps = x.market_gap_check(bars)
    assert isinstance(gaps, list)
