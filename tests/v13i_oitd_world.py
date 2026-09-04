"""Hand-computable synthetic worlds for the A13-V13-A8-OITD test evidence.

All values are HAND-DESIGNED so every signal score, rank, book leg, weight,
book return and cost in the v13i OITD tests is verifiable on paper:

* 18 tradeable names ``SYM00..SYM17`` (>= the frozen 12-name breadth floor,
  terciles exactly 6/6/6 like the frozen 19-name universe's 6/7/6);
* decision stamps are real ``stamp_calendar()`` Mondays (midnight UTC grid,
  so the pinned next-allowed-fill convention applies unchanged);
* OI: 9 daily stamps per symbol at 23:55 UTC ending the day before the
  stamp (all inside the trailing 10-day span, so the latest 7 -- the
  frozen OI7 -- average to the symbol's constant by construction);
* mark: one snapshot one hour before the stamp (inside the frozen 24h
  pairing tolerance);
* turnover: constant per symbol per day over the whole 56-day neighbour
  window, so ``TO(T, W)`` equals the constant for W in {28, 56}.

World A (mechanical-exposure world): OI = 100 and MK = 10 for every symbol,
turnover strictly increasing in the symbol index ->
``D_i = 1000 / (1_000_000 + 1000 i) = 1 / (1000 + i)`` -- strictly DECREASING
in i.  The anchor (ascending D) therefore ranks SYM17 first, and on this
world the anchor book EQUALS the causal control book (pure turnover flow).

World B (differentiating world): three turnover/OI groups -- H = SYM00..05
(turnover 1_000_000, OI 900), M = SYM06..11 (500_000, 30), L = SYM12..17
(250_000, 3); MK = 10.  Hand durations: D_H = 9000/1e6 = 0.009,
D_M = 300/5e5 = 0.0006, D_L = 30/2.5e5 = 0.00012.  Anchor (ascending D):
long L, short H, buffer M.  Control (descending turnover): long H, short L
-- the EXACT inverse book, proving the OI stock (not the flow) moves the
anchor.  With group forward returns -0.03 / 0 / +0.03 the anchor weekly
book return is EXACTLY +0.03 and the control's EXACTLY -0.03.

No real data is read; no scored metric is computed.
"""

from __future__ import annotations

from typing import Any, Mapping

from research.v11.families.oilever_delev.strategy import Bar
from research.v13.families.oitd.strategy import (
    BAR_INTERVAL_NS,
    stamp_calendar,
)

DAY_NS = 86_400_000_000_000
HOUR_NS = 3_600_000_000_000
BAR_NS = int(BAR_INTERVAL_NS)

#: The first frozen decision stamp (2025-08-25T00:00:00Z, a Monday midnight).
T1_NS = int(stamp_calendar()[0])
T1_DAY = T1_NS // DAY_NS
#: The second chained decision stamp (one full holding week later).
T2_NS = T1_NS + 7 * DAY_NS
T2_DAY = T2_NS // DAY_NS
T3_NS = T1_NS + 14 * DAY_NS
T3_DAY = T3_NS // DAY_NS
T4_NS = T1_NS + 21 * DAY_NS

SYMBOLS: tuple[str, ...] = tuple(f"SYM{i:02d}" for i in range(18))
GROUP_H = tuple(f"SYM{i:02d}" for i in range(0, 6))
GROUP_M = tuple(f"SYM{i:02d}" for i in range(6, 12))
GROUP_L = tuple(f"SYM{i:02d}" for i in range(12, 18))

OI_STAMP_TIME_NS = 23 * HOUR_NS + 55 * 60 * 1_000_000_000  # 23:55 UTC
#: 9 daily OI stamps ending the day before the stamp (latest 7 used).
N_OI_STAMPS = 9
#: Forward weekly returns per hand-designed group (world B).
GROUP_FORWARD_RETURNS = {"H": -0.03, "M": 0.0, "L": 0.03}
#: World B hand durations (D = OI7 x MK / TO).
WORLD_B_DURATIONS = {"H": 0.009, "M": 0.0006, "L": 0.00012}


def oi_series(day_index: int, value_by_symbol: Mapping[str, float]) -> dict[str, tuple[tuple[int, float], ...]]:
    """Nine daily OI stamps at 23:55 UTC for the ``N_OI_STAMPS`` days BEFORE
    ``day_index`` (the anchor row sits strictly before the stamp day's
    midnight, so every row is available at the stamp)."""
    out: dict[str, tuple[tuple[int, float], ...]] = {}
    for sym, value in value_by_symbol.items():
        rows = tuple(
            (
                (day_index - d) * DAY_NS + OI_STAMP_TIME_NS,
                float(value),
            )
            for d in sorted(range(1, N_OI_STAMPS + 1), reverse=True)
        )
        out[sym] = rows
    return out


def mark_series(stamp_ns: int, value_by_symbol: Mapping[str, float]) -> dict[str, tuple[tuple[int, float], ...]]:
    """One mark snapshot one hour before the stamp (fresh, within 24h)."""
    return {
        sym: ((int(stamp_ns) - HOUR_NS, float(value)),)
        for sym, value in value_by_symbol.items()
    }


def turnover_days(day_index_lo: int, day_index_hi: int, value_by_symbol: Mapping[str, float]) -> dict[str, dict[int, float]]:
    """Constant daily turnover for every completed day bucket in range."""
    return {
        sym: {d: float(value) for d in range(day_index_lo, day_index_hi + 1)}
        for sym, value in value_by_symbol.items()
    }


def world_a(turnover_days_count: int = 56) -> dict[str, Any]:
    """Mechanical-exposure world: D_i = 1 / (1000 + i), hand-exact."""
    oi = {sym: 100.0 for sym in SYMBOLS}
    mk = {sym: 10.0 for sym in SYMBOLS}
    to = {sym: 1_000_000.0 + 1_000.0 * i for i, sym in enumerate(SYMBOLS)}
    return {
        "name": "A_constant_oi",
        "day_turnover_by_symbol": turnover_days(
            T1_DAY - turnover_days_count, T1_DAY - 1, to
        ),
        "oi_by_symbol": oi_series(T1_DAY, oi),
        "mark_by_symbol": mark_series(T1_NS, mk),
        "stamp_ns": T1_NS,
        "universe": list(SYMBOLS),
        "expected_scores": {
            sym: 1.0 / (1000.0 + i) for i, sym in enumerate(SYMBOLS)
        },
    }


def world_b_turnover() -> dict[str, float]:
    out: dict[str, float] = {}
    for sym in GROUP_H:
        out[sym] = 1_000_000.0
    for sym in GROUP_M:
        out[sym] = 500_000.0
    for sym in GROUP_L:
        out[sym] = 250_000.0
    return out


def world_b_oi(overrides: Mapping[str, float] | None = None) -> dict[str, float]:
    out: dict[str, float] = {}
    for sym in GROUP_H:
        out[sym] = 900.0
    for sym in GROUP_M:
        out[sym] = 30.0
    for sym in GROUP_L:
        out[sym] = 3.0
    for sym, value in dict(overrides or {}).items():
        out[sym] = float(value)
    return out


def world_b(
    *,
    day_index: int,
    stamp_ns: int,
    oi_overrides: Mapping[str, float] | None = None,
    drop_turnover_days_for: Mapping[str, list[int]] | None = None,
    turnover_days_count: int = 56,
) -> dict[str, Any]:
    """Differentiating world at one stamp; hand durations in WORLD_B_DURATIONS."""
    oi = oi_series(day_index, world_b_oi(oi_overrides))
    mk = mark_series(stamp_ns, {sym: 10.0 for sym in SYMBOLS})
    to = turnover_days(
        day_index - turnover_days_count, day_index - 1, world_b_turnover()
    )
    for sym, dropped in dict(drop_turnover_days_for or {}).items():
        for d in dropped:
            to[sym].pop(int(d), None)
    return {
        "name": "B_differentiating",
        "day_turnover_by_symbol": to,
        "oi_by_symbol": oi,
        "mark_by_symbol": mk,
        "stamp_ns": int(stamp_ns),
        "universe": list(SYMBOLS),
        "forward_returns": {
            sym: GROUP_FORWARD_RETURNS["H" if sym in GROUP_H else "M" if sym in GROUP_M else "L"]
            for sym in SYMBOLS
        },
    }


def execution_bars(stamp_ns: int, *, open_at_stamp: float = 100.0, fill_open: float = 101.0, delayed_open: float = 102.0) -> list[Bar]:
    """Completed 15m bars around one midnight stamp for the fill convention.

    * bar closing AT the stamp opens one slot earlier (its OPEN is the
      valuation mark at the stamp via the covering-bar fallback);
    * bar ``[T+15m, T+30m)`` -- slot-open == order release; the base fill;
    * bar ``[T+30m, T+45m)`` -- the +1-event-delay fill;
    * a late bar well after the window proves non-selection.
    Opens and closes differ so any open/close mix-up breaks the tests.
    """
    t = int(stamp_ns)
    return [
        Bar(ts_event_ns=t + BAR_NS, open=float(open_at_stamp), high=1.0 + float(open_at_stamp), low=float(open_at_stamp) - 1.0, close=float(open_at_stamp) + 0.5),
        Bar(ts_event_ns=t + 2 * BAR_NS, open=float(fill_open), high=1.0 + float(fill_open), low=float(fill_open) - 1.0, close=float(fill_open) + 0.25),
        Bar(ts_event_ns=t + 3 * BAR_NS, open=float(delayed_open), high=1.0 + float(delayed_open), low=float(delayed_open) - 1.0, close=float(delayed_open) + 0.125),
        Bar(ts_event_ns=t + 8 * BAR_NS, open=999.0, high=1000.0, low=998.0, close=999.5),
    ]


def merged_world(stamps, *, oi_overrides_by_stamp=None, drop_turnover_days_for=None):
    """One world whose maps cover EVERY stamp's trailing windows.

    Turnover: one constant-per-day value per symbol for every day bucket
    from ``min(stamp_day) - 56`` through ``max(stamp_day) - 1``.  OI: 9
    daily stamps before EACH stamp (per-stamp segments concatenated, so
    the latest 7 <= any stamp are that stamp's segment).  Mark: one
    snapshot one hour before each stamp.  This is the fixture the chained
    (hysteresis) and determinism tests run on.
    """
    day_index = [int(s) // DAY_NS for s in stamps]
    to = turnover_days(
        min(day_index) - 56, max(day_index) - 1, world_b_turnover()
    )
    for sym, dropped in dict(drop_turnover_days_for or {}).items():
        for d in dropped:
            to[sym].pop(int(d), None)
    overrides_by_stamp = list(oi_overrides_by_stamp or [None] * len(stamps))
    # segments overlap when stamps sit closer than the 9-stamp OI span, so
    # merge per timestamp (the LATER stamp's segment wins) then sort
    oi: dict[str, dict[int, float]] = {sym: {} for sym in SYMBOLS}
    for stamp, day, overrides in zip(stamps, day_index, overrides_by_stamp):
        segment = oi_series(day, world_b_oi(overrides))
        for sym, rows in segment.items():
            for ts, value in rows:
                oi[sym][ts] = value
    mk = {
        sym: tuple(
            sorted((int(stamp) - HOUR_NS, 10.0) for stamp in stamps)
        )
        for sym in SYMBOLS
    }
    return {
        "name": "B_merged",
        "day_turnover_by_symbol": to,
        "oi_by_symbol": {
            sym: tuple(sorted(rows.items())) for sym, rows in oi.items()
        },
        "mark_by_symbol": mk,
        "stamp_ns": int(stamps[-1]),
        "universe": list(SYMBOLS),
        "forward_returns": {
            sym: GROUP_FORWARD_RETURNS["H" if sym in GROUP_H else "M" if sym in GROUP_M else "L"]
            for sym in SYMBOLS
        },
    }


def hysteresis_world(week2_overrides):
    """A two-week world for the chained hysteresis hand-traces.

    Week 1 OI segment: the 9 base-value daily rows before stamp 1 (so the
    stamp-1 book is the plain world-B book).  Week 2 OI segment: the 7
    daily rows of days T1_DAY..T2_DAY-1 with ``week2_overrides`` applied --
    these are EXACTLY the latest 7 rows at stamp 2, so the stamp-2 book
    reads only the new week's values.  Turnover stays constant per day
    across both windows and the mark stays 10.0.
    """
    day_index = [T1_DAY, T2_DAY]
    to = turnover_days(T1_DAY - 56, T2_DAY - 1, world_b_turnover())
    base = world_b_oi()
    week2 = world_b_oi(dict(week2_overrides or {}))
    oi: dict[str, list[tuple[int, float]]] = {sym: [] for sym in SYMBOLS}
    for sym in SYMBOLS:
        seg1 = [
            ((T1_DAY - d) * DAY_NS + OI_STAMP_TIME_NS, float(base[sym]))
            for d in range(1, N_OI_STAMPS + 1)
        ]
        seg2 = [
            ((T1_DAY + d) * DAY_NS + OI_STAMP_TIME_NS, float(week2[sym]))
            for d in range(0, 7)
        ]
        oi[sym] = sorted(seg1 + seg2)
    mk = {
        sym: ((T1_NS - HOUR_NS, 10.0), (T2_NS - HOUR_NS, 10.0))
        for sym in SYMBOLS
    }
    return {
        "name": "B_hysteresis",
        "day_turnover_by_symbol": to,
        "oi_by_symbol": {sym: tuple(rows) for sym, rows in oi.items()},
        "mark_by_symbol": mk,
        "stamp_ns": T2_NS,
        "universe": list(SYMBOLS),
        "forward_returns": {
            sym: GROUP_FORWARD_RETURNS["H" if sym in GROUP_H else "M" if sym in GROUP_M else "L"]
            for sym in SYMBOLS
        },
    }


BENCHMARK = "BTCUSDT"


def bars_by_symbol(symbols, stamp_ns) -> dict[str, tuple[Bar, ...]]:
    """Completed execution bars per symbol (the context-only leg included)."""
    all_symbols = tuple(sorted(set(symbols) | {BENCHMARK}))
    return {sym: tuple(execution_bars(int(stamp_ns))) for sym in all_symbols}


def plugin(arm_id: str, world: Mapping[str, Any], *, with_bars: bool = True):
    """An OitdPlugin on a synthetic world (control refuses OI/mark bundles)."""
    from research.v13.families.oitd.plugin import OitdPlugin

    is_control = arm_id == "CTL-FLOW-ONLY"
    return OitdPlugin(
        arm_id=arm_id,
        day_turnover_by_symbol=dict(world["day_turnover_by_symbol"]),
        bars_by_symbol=(
            bars_by_symbol(world["universe"], int(world["stamp_ns"]))
            if with_bars
            else None
        ),
        oi_by_symbol=None if is_control else dict(world["oi_by_symbol"]),
        mark_by_symbol=None if is_control else dict(world["mark_by_symbol"]),
        tick_sizes={sym: 0.01 for sym in world["universe"]},
    )


__all__ = [
    "BAR_NS",
    "DAY_NS",
    "GROUP_FORWARD_RETURNS",
    "GROUP_H",
    "GROUP_L",
    "GROUP_M",
    "HOUR_NS",
    "N_OI_STAMPS",
    "OI_STAMP_TIME_NS",
    "SYMBOLS",
    "T1_DAY",
    "T1_NS",
    "T2_DAY",
    "T2_NS",
    "T3_NS",
    "T4_NS",
    "WORLD_B_DURATIONS",
    "execution_bars",
    "mark_series",
    "oi_series",
    "plugin",
    "turnover_days",
    "world_a",
    "world_b",
    "world_b_oi",
    "world_b_turnover",
]
