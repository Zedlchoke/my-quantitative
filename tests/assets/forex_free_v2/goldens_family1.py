"""Hand-computed goldens for the family1 (FXFV2-A4-P1) evidence tests.

SYNTHETIC_TEST_ONLY.  Every expected number below is a literal with the
arithmetic written beside it.  Base geometry (fixtures_family1):

* Tokyo envelope for range R around P = 1.1000: lo = P - R/2, hi = P + R/2,
  so range = hi - lo exactly, T_H = hi, T_L = lo, M = (hi+lo)/2.
* All decision days are BST days (2025-06-xx): the London morning window is
  the bar-open UTC stamps {07, 08, 09, 10}Z; the 07Z/08Z bars lie inside the
  Tokyo window [00:00,09:00)Z and therefore can never strictly breach T_H/T_L
  (their own extremes are part of the range) -- they are the A9-F "dead bars"
  and are fixed strictly inside the range in every scenario.
* 16:00 America/New_York bar-open stamps: 20:00Z in EDT weeks, 21:00Z in EST
  weeks (zoneinfo; asserted by the DST test).
"""
from __future__ import annotations

import datetime as _dt

from tests.assets.forex_free_v2.fixtures_family1 import (
    BASE_P,
    DaySpec,
    default_world,
    envelope,
    weekday_dates,
)

D = _dt.date

# --- envelope literals ---------------------------------------------------------- #
R_DEFAULT = 0.0050                     # default day Tokyo range
R_TRADE = 0.0030                       # decision-day Tokyo range (compressed)
R_GOLDEN = 0.0044                      # neighbour-only day Tokyo range
R_WIDE = 0.0060                        # 2025-06-02 (NOT compressed)

LO_DEFAULT, HI_DEFAULT = envelope(R_DEFAULT)   # 1.1000 -/+ 0.0025 -> 1.0975 / 1.1025
LO_TRADE, HI_TRADE = envelope(R_TRADE)         # 1.1000 -/+ 0.0015 -> 1.0985 / 1.1015
LO_GOLDEN, HI_GOLDEN = envelope(R_GOLDEN)      # 1.1000 -/+ 0.0022 -> 1.0978 / 1.1022
LO_WIDE, HI_WIDE = envelope(R_WIDE)            # 1.1000 -/+ 0.0030 -> 1.0970 / 1.1030

assert (LO_DEFAULT, HI_DEFAULT) == (1.0975, 1.1025)
assert (LO_TRADE, HI_TRADE) == (1.0985, 1.1015)
assert (LO_GOLDEN, HI_GOLDEN) == (1.0978, 1.1022)
assert (LO_WIDE, HI_WIDE) == (1.0970, 1.1030)

T_H = 1.1015                           # T_H of a trade day = hi of R_TRADE envelope
T_L = 1.0985                           # T_L of a trade day
MID = 1.1000                           # M = (1.1015 + 1.0985) / 2
CALM = (1.1000, 1.1002, 1.0998, 1.1000)  # calm afternoon bar: M -/+ 2 ticks
INSIDE = (1.1000, 1.1008, 1.0992, 1.1000)  # dead London bar: h < T_H, l > T_L

# --- explicit day tables (hour -> (open, high, low, close), UTC stamps) ---------- #
JUN3_LONG = {                          # 2025-06-03 (Tue, BST): LONG, invalidation exit
    7: INSIDE,
    8: INSIDE,
    9: (1.1010, 1.1020, 1.1005, 1.1018),   # DECISION: h 1.1020 > T_H 1.1015 (strict); l 1.1005 > T_L
    10: (1.1016, 1.1022, 1.1014, 1.1019),  # ENTRY at open 1.1016
    11: (1.1019, 1.1021, 1.1015, 1.1017),  # c 1.1017 >= T_H -> no invalidation
    12: (1.1017, 1.1018, 1.1010, 1.1016),  # c 1.1016 >= T_H -> no invalidation
    13: (1.1016, 1.1017, 1.1005, 1.1010),  # c 1.1010 < T_H 1.1015 -> INVALIDATION trigger
    14: (1.1012, 1.1014, 1.1008, 1.1013),  # EXIT at open 1.1012
    15: CALM, 16: CALM, 17: CALM, 18: CALM, 19: CALM,
    20: CALM,                              # 20:00Z = 16:00 New York EDT (flat bar present)
}

JUN5_SHORT = {                         # 2025-06-05 (Thu, BST): SHORT, invalidation exit
    7: INSIDE,
    8: INSIDE,
    9: (1.0990, 1.0995, 1.0980, 1.0982),   # DECISION: l 1.0980 < T_L 1.0985 (strict); h 1.0995 < T_H
    10: (1.0982, 1.0983, 1.0978, 1.0981),  # ENTRY (short) at open 1.0982
    11: (1.0981, 1.0982, 1.0977, 1.0981),  # c 1.0981 <= T_L -> no invalidation
    12: (1.0981, 1.0984, 1.0980, 1.0983),  # c 1.0983 <= T_L -> no invalidation
    13: (1.0983, 1.0988, 1.0982, 1.0987),  # c 1.0987 > T_L 1.0985 -> INVALIDATION trigger
    14: (1.0989, 1.0991, 1.0987, 1.0988),  # EXIT at open 1.0989
    15: CALM, 16: CALM, 17: CALM, 18: CALM, 19: CALM, 20: CALM,
}

JUN10_GOLDEN: dict[int, tuple] = {}    # 2025-06-10: calm afternoon (range 0.0044 day)

# long forced-flat day (no invalidation: every close stays >= T_H)
LONG_FF: dict[int, tuple] = {
    7: INSIDE,
    8: INSIDE,
    9: (1.1010, 1.1020, 1.1005, 1.1018),       # decision bar
    10: (1.1016, 1.1022, 1.1014, 1.1019),      # entry at 1.1016
    11: (1.1019, 1.1021, 1.1015, 1.1020),      # GMT days: in window but after the decision
    12: (1.1019, 1.1021, 1.1015, 1.1020),
    13: (1.1019, 1.1021, 1.1015, 1.1020),
    14: (1.1019, 1.1021, 1.1015, 1.1020),
    15: (1.1019, 1.1021, 1.1015, 1.1020),
    16: (1.1019, 1.1021, 1.1015, 1.1020),
    17: (1.1019, 1.1021, 1.1015, 1.1020),
    18: (1.1019, 1.1021, 1.1015, 1.1020),
    19: (1.1019, 1.1021, 1.1015, 1.1020),
    20: (1.1020, 1.1022, 1.1018, 1.1021),      # 16:00 NY EDT flat bar, exit at open 1.1020
    21: (1.1021, 1.1023, 1.1019, 1.1022),      # 16:00 NY EST flat bar, exit at open 1.1021
}

# second same-day break must NOT re-enter (governor: 1 entry/pair/UTC-day)
SECOND_BREAK = {
    7: INSIDE,
    8: INSIDE,
    9: (1.1010, 1.1020, 1.1005, 1.1018),       # first (and only allowed) decision
    10: (1.1016, 1.1022, 1.1014, 1.1019),      # entry
    11: (1.1018, 1.1019, 1.1005, 1.1010),      # c 1.1010 < T_H -> invalidation
    12: (1.1012, 1.1014, 1.1008, 1.1013),      # exit at 1.1012
    13: (1.1015, 1.1020, 1.1012, 1.1018),      # SECOND break (h 1.1020 > T_H) -- ignored
    14: CALM, 15: CALM, 16: CALM, 17: CALM, 18: CALM, 19: CALM, 20: CALM,
}

# control-vs-anchor-vs-neighbour day: the control M trigger fires on the
# FIRST window bar (every ordinary bar crosses M); the anchor on 09Z.
ARMS_JUN3 = {
    # straddles M with close < M: CONTROL decision (both M breaches, tie-break
    # sign(close-M) = -1) at 07Z; anchor no-fire (h 1.1008 < T_H, l 1.0992 > T_L)
    7: (1.1000, 1.1008, 1.0992, 1.0995),
    # CONTROL entry at open 1.1005; its close 1.1010 > M triggers the control
    # invalidation; anchor no-fire (h 1.1012 < T_H, l 1.1004 > T_L)
    8: (1.1005, 1.1012, 1.1004, 1.1010),
    9: (1.1012, 1.1020, 1.1008, 1.1018),       # anchor/neighbour decision (h > T_H);
                                               # CONTROL exit at open 1.1012 (invalidation fill)
    10: (1.1016, 1.1022, 1.1014, 1.1019),      # anchor/neighbour entry at 1.1016
    11: (1.1019, 1.1021, 1.1015, 1.1017),      # anchor: c >= T_H no; control already flat
    12: (1.1017, 1.1018, 1.1010, 1.1016),
    13: (1.1016, 1.1017, 1.1005, 1.1010),      # anchor/neighbour invalidation (c 1.1010 < T_H)
    14: (1.1012, 1.1014, 1.1008, 1.1013),      # anchor/neighbour exit at 1.1012
    15: CALM, 16: CALM, 17: CALM, 18: CALM, 19: CALM,
    20: (1.1040, 1.1041, 1.1039, 1.1040),      # 16:00 NY EDT flat bar (control already flat)
}

ARMS_JUN10 = {                         # 2025-06-10: neighbour-only day (range 0.0044)
    7: INSIDE,
    8: INSIDE,
    9: (1.1018, 1.1025, 1.1010, 1.1022),       # h 1.1025 > T_H 1.1022 (neighbour compressed, anchor not)
    10: (1.1022, 1.1024, 1.1021, 1.1023),      # neighbour entry at 1.1022
    11: (1.1023, 1.1025, 1.1022, 1.1024),
    12: (1.1023, 1.1025, 1.1022, 1.1024),
    13: (1.1023, 1.1025, 1.1022, 1.1024),
    14: (1.1023, 1.1025, 1.1022, 1.1024),
    15: (1.1023, 1.1025, 1.1022, 1.1024),
    16: (1.1023, 1.1025, 1.1022, 1.1024),
    17: (1.1023, 1.1025, 1.1022, 1.1024),
    18: (1.1023, 1.1025, 1.1022, 1.1024),
    19: (1.1023, 1.1025, 1.1022, 1.1024),
    20: (1.1030, 1.1031, 1.1029, 1.1030),      # forced flat at open 1.1030
}


def _day(day: _dt.date, lo: float, hi: float, overrides, last_hour: int = 20) -> DaySpec:
    return DaySpec(day, lo, hi, overrides, last_hour=last_hour)


def e2e_world() -> list[dict]:
    """Anchor end-to-end world: exactly one LONG and one SHORT anchor trade.

    42 calendar days ending 2025-06-10 (BST week): 30 weekdays, of which the
    28 non-trade days are NOT compressed.  Trailing-20 windows (hand-checked):
      Jun 3 <- May 6..Jun 2  (20 sessions): 19x0.0050 + 1x0.0060 -> median 0.0050
      Jun 5 <- May 8..Jun 4  (20 sessions): 18x0.0050 + 0.0060 + 0.0030 -> median 0.0050
      Jun10 <- May13..Jun 9  (20 sessions): 17x0.0050 + 0.0060 + 2x0.0030 -> median 0.0050, Q20 0.0050
    """
    days = {d: DaySpec(d, LO_DEFAULT, HI_DEFAULT) for d in weekday_dates(D(2025, 6, 10), 42)}
    days[D(2025, 6, 2)] = DaySpec(D(2025, 6, 2), LO_WIDE, HI_WIDE)
    days[D(2025, 6, 3)] = _day(D(2025, 6, 3), LO_TRADE, HI_TRADE, JUN3_LONG)
    days[D(2025, 6, 5)] = _day(D(2025, 6, 5), LO_TRADE, HI_TRADE, JUN5_SHORT)
    days[D(2025, 6, 10)] = _day(D(2025, 6, 10), LO_GOLDEN, HI_GOLDEN, JUN10_GOLDEN)
    from tests.assets.forex_free_v2.fixtures_family1 import build_rows
    return build_rows(list(days.values()))


def forced_flat_world(with_flat_bar: bool = True) -> list[dict]:
    """World ending 2025-06-03: one compressed day, no invalidation ->
    forced flat.  with_flat_bar=False removes the 20:00Z bar (early forced
    flat via the immediately preceding existing 19:00Z bar)."""
    overrides = {h: bar for h, bar in LONG_FF.items() if h <= (20 if with_flat_bar else 19)}
    days = {d: DaySpec(d, LO_DEFAULT, HI_DEFAULT) for d in weekday_dates(D(2025, 6, 3), 42)}
    days[D(2025, 6, 3)] = _day(D(2025, 6, 3), LO_TRADE, HI_TRADE, overrides,
                               last_hour=20 if with_flat_bar else 19)
    from tests.assets.forex_free_v2.fixtures_family1 import build_rows
    return build_rows(list(days.values()))


def flat_unavailable_world() -> list[dict]:
    """Compressed entry day whose day ends at the entry bar: no 16:00-NY bar
    and no existing bar after the entry => no flat exit available => NO_TRADE."""
    overrides = {h: LONG_FF[h] for h in (7, 8, 9, 10)}
    days = {d: DaySpec(d, LO_DEFAULT, HI_DEFAULT) for d in weekday_dates(D(2025, 6, 3), 42)}
    days[D(2025, 6, 3)] = _day(D(2025, 6, 3), LO_TRADE, HI_TRADE, overrides, last_hour=10)
    from tests.assets.forex_free_v2.fixtures_family1 import build_rows
    return build_rows(list(days.values()))


def dst_world(last_day: _dt.date) -> list[dict]:
    """Default run ending at ``last_day`` with one compressed LONG day at
    ``last_day`` breaking at 09Z and holding to the forced-flat bar."""
    est_flat = last_day == D(2025, 3, 7) or last_day == D(2025, 11, 3)
    overrides = {h: bar for h, bar in LONG_FF.items() if h <= (21 if est_flat else 20)}
    days = {d: DaySpec(d, LO_DEFAULT, HI_DEFAULT) for d in weekday_dates(last_day, 42)}
    days[last_day] = _day(last_day, LO_TRADE, HI_TRADE, overrides,
                          last_hour=21 if est_flat else 20)
    from tests.assets.forex_free_v2.fixtures_family1 import build_rows
    return build_rows(list(days.values()))


def governor_week_world() -> list[dict]:
    """Week Mon 2025-06-02 .. Fri 2025-06-06 compressed every day: 3 trades,
    Thu/Fri signals dropped by the weekly cap (still decisions)."""
    days = {d: DaySpec(d, LO_DEFAULT, HI_DEFAULT) for d in weekday_dates(D(2025, 6, 6), 42)}
    for d in (D(2025, 6, 2), D(2025, 6, 3), D(2025, 6, 4), D(2025, 6, 5), D(2025, 6, 6)):
        days[d] = _day(d, LO_TRADE, HI_TRADE, LONG_FF)
    from tests.assets.forex_free_v2.fixtures_family1 import build_rows
    return build_rows(list(days.values()))


def second_break_world() -> list[dict]:
    """One compressed day: trade exits at 12Z; a second 13Z break must not
    re-enter (max 1 entry/pair/UTC-day)."""
    days = {d: DaySpec(d, LO_DEFAULT, HI_DEFAULT) for d in weekday_dates(D(2025, 6, 3), 42)}
    days[D(2025, 6, 3)] = _day(D(2025, 6, 3), LO_TRADE, HI_TRADE, SECOND_BREAK)
    from tests.assets.forex_free_v2.fixtures_family1 import build_rows
    return build_rows(list(days.values()))


def arms_differ_world() -> list[dict]:
    """All three arms fire; the trade sets (and therefore digests) differ.

    anchor   : Jun 3 only  (entry 10Z 1.1016, invalidation exit 14Z 1.1012)
    neighbour: Jun 3 + Jun 10 (identical law to anchor where anchor fires)
    control  : Jun 3 only, but the M trigger fires one bar earlier
               (entry 09Z 1.1012, forced-flat exit 20Z 1.1040)
    """
    days = {d: DaySpec(d, LO_DEFAULT, HI_DEFAULT) for d in weekday_dates(D(2025, 6, 10), 42)}
    days[D(2025, 6, 3)] = _day(D(2025, 6, 3), LO_TRADE, HI_TRADE, ARMS_JUN3)
    days[D(2025, 6, 10)] = _day(D(2025, 6, 10), LO_GOLDEN, HI_GOLDEN, ARMS_JUN10)
    from tests.assets.forex_free_v2.fixtures_family1 import build_rows
    return build_rows(list(days.values()))


# --- golden expected schedules --------------------------------------------------- #
E2E_ANCHOR_LONG = {
    "trade_id": "family1|anchor|EUR/USD|2025-06-03T10:00:00Z",
    "pair": "EUR/USD",
    "side": 1,
    "notional_usd": 10000,
    "entry_price": 1.1016,             # open of the 10:00Z bar
    "entry_ts": "2025-06-03T10:00:00Z",
    "decision_ts": "2025-06-03T09:00:00Z",
    "exit_price": 1.1012,              # open of the 14:00Z bar
    "exit_ts": "2025-06-03T14:00:00Z",
    "exit_reason": "invalidation",     # 13Z close 1.1010 < T_H 1.1015 -> next open
}

E2E_ANCHOR_SHORT = {
    "trade_id": "family1|anchor|EUR/USD|2025-06-05T10:00:00Z",
    "pair": "EUR/USD",
    "side": -1,
    "notional_usd": 10000,
    "entry_price": 1.0982,             # open of the 10:00Z bar
    "entry_ts": "2025-06-05T10:00:00Z",
    "decision_ts": "2025-06-05T09:00:00Z",
    "exit_price": 1.0989,              # open of the 14:00Z bar
    "exit_ts": "2025-06-05T14:00:00Z",
    "exit_reason": "invalidation",     # 13Z close 1.0987 > T_L 1.0985 -> next open
}

# Accounting hand-math (frozen identity pnl = dir * 10000 * (exit/entry - 1);
# cost/side = 10000 * (1.5 * 1.0) / 10000 = 1.50 USD exactly):
LONG_PNL = -3.631082062454105       # 10000 * (1.1012/1.1016 - 1) = 10000 * (-4/1.1016) x 1e-4
LONG_NET = -6.631082062454105       # -3.631082062454105 - 1.50 - 1.50
SHORT_PNL = -6.374066654524224      # -10000 * (1.0989/1.0982 - 1) = -10000 * (7/1.0982) x 1e-4
SHORT_NET = -9.374066654524224      # -6.374066654524224 - 1.50 - 1.50
TOTAL_GROSS = -10.00514871697833    # -3.631082062454105 + -6.374066654524224
TOTAL_COST = 6.00                   # 4 fills x 1.50
TOTAL_NET = -16.00514871697833      # -10.00514871697833 - 6.00

# state goldens (world: e2e_world)
GOLDEN_JUN3_STATE = {
    "tokyo_range": 0.0030,             # max(high)=1.1015 - min(low)=1.0985
    "t_high": 1.1015,
    "t_low": 1.0985,
    "mid": 1.1000,                     # (1.1015 + 1.0985) / 2
    "median20": 0.0050,                # 19x0.0050 + 1x0.0060 -> order stats 10/11 = 0.0050
    "q20": 0.0050,                     # sorted 20: [0.0050 x19, 0.0060] -> [4] = 0.0050
    "compressed_anchor": True,         # 0.0030 < 0.75 * 0.0050 = 0.00375
}
GOLDEN_JUN10_STATE = {
    "tokyo_range": 0.0044,             # 1.1022 - 1.0978
    "median20": 0.0050,                # 17x0.0050 + 0.0060 + 2x0.0030 -> median 0.0050
    "q20": 0.0050,                     # sorted: [0.0030, 0.0030, 0.0050 x17, 0.0060] -> [4]
    "compressed_anchor": False,        # 0.0044 >= 0.00375
    "compressed_neighbour": True,      # 0.0044 < Q20 0.0050
    "compressed_control": False,       # control holds the anchor ratio state
}

# forced-flat goldens (world: forced_flat_world / flat_unavailable_world)
FF_EXIT_EDT = ("2025-06-03T20:00:00Z", 1.1020, "forced_flat")   # 16:00 NY EDT = 20:00Z
FF_EXIT_EARLY = ("2025-06-03T19:00:00Z", 1.1019, "forced_flat")  # 19:00Z open (bar before flat)

# DST goldens: (world end day, decision_ts, entry_ts, entry open, exit_ts, exit open)
DST_CASES = [
    # 2025-03-07 Fri: London GMT (window 08-11Z), NY EST (flat 21:00Z)
    (D(2025, 3, 7), "2025-03-07T09:00:00Z", "2025-03-07T10:00:00Z", 1.1016,
     "2025-03-07T21:00:00Z", 1.1021),
    # 2025-03-10 Mon: US switched to EDT (Mar 9), London still GMT
    (D(2025, 3, 10), "2025-03-10T09:00:00Z", "2025-03-10T10:00:00Z", 1.1016,
     "2025-03-10T20:00:00Z", 1.1020),
    # 2025-03-31 Mon: London switched to BST (Mar 30) -> window 07-10Z; NY EDT
    (D(2025, 3, 31), "2025-03-31T09:00:00Z", "2025-03-31T10:00:00Z", 1.1016,
     "2025-03-31T20:00:00Z", 1.1020),
    # 2025-10-27 Mon: London back to GMT (Oct 26), US still EDT
    (D(2025, 10, 27), "2025-10-27T09:00:00Z", "2025-10-27T10:00:00Z", 1.1016,
     "2025-10-27T20:00:00Z", 1.1020),
    # 2025-11-03 Mon: US back to EST (Nov 2) -> flat 21:00Z
    (D(2025, 11, 3), "2025-11-03T09:00:00Z", "2025-11-03T10:00:00Z", 1.1016,
     "2025-11-03T21:00:00Z", 1.1021),
]

# governor goldens (world: governor_week_world): Mon/Tue/Wed trade, Thu/Fri capped
GOV_TRADES = 3
GOV_DECISIONS = 5
GOV_CAPPED_DAYS = 2
GOV_ENTRY_DAYS = ["2025-06-02", "2025-06-03", "2025-06-04"]

# second-break golden
SECOND_BREAK_TRADE = {
    "entry_ts": "2025-06-03T10:00:00Z",
    "exit_ts": "2025-06-03T12:00:00Z",
    "exit_price": 1.1012,
}

# arms-differ goldens
ARMS_EXPECTED = {
    "anchor": {
        "decisions": 1,
        "entries": ["2025-06-03T10:00:00Z"],
        "entry_price": 1.1016,
        "exit_price": 1.1012,
        "exit_reason": "invalidation",
    },
    "neighbour": {
        "decisions": 2,
        "entries": ["2025-06-03T10:00:00Z", "2025-06-10T10:00:00Z"],
        "jun10_entry_price": 1.1022,
        "jun10_exit_price": 1.1030,
        "jun10_exit_reason": "forced_flat",
    },
    # The control trigger is "high > M or low < M": EVERY ordinary window bar
    # crosses M, so the control decides on the FIRST window bar.  On the
    # golden day the 07Z bar dips (l 1.0986 < M 1.1000, h 1.0999 < M) ->
    # downside decision at 07Z, entry at the 08Z open, invalidated when the
    # 08Z close (1.1010) is back above M -> exit at the 09Z open.
    "control": {
        "decisions": 1,
        "decision_ts": "2025-06-03T07:00:00Z",
        "entries": ["2025-06-03T08:00:00Z"],
        "entry_price": 1.1005,
        "exit_price": 1.1012,
        "exit_reason": "invalidation",
    },
}

# tier-2 goldens (world: e2e_world, cost_tier=2.0): fills delayed one extra event
TIER2_LONG = {
    "entry_ts": "2025-06-03T11:00:00Z",    # 09Z decision -> +2 events
    "entry_price": 1.1019,                 # open of the 11:00Z bar
    "exit_ts": "2025-06-03T15:00:00Z",     # 13Z trigger + 2 events -> 15:00Z open (calm mid)
    "exit_price": 1.1000,
    "exit_reason": "invalidation",
}
TIER2_SHORT = {
    "entry_ts": "2025-06-05T11:00:00Z",
    "entry_price": 1.0981,                 # open of the 11:00Z bar
    "exit_ts": "2025-06-05T15:00:00Z",
    "exit_price": 1.1000,
    "exit_reason": "invalidation",
}

# decision counting (e2e world, anchor): 30 scanned weekdays
E2E_DATES = 30
E2E_ANCHOR_DECISIONS = 2             # Jun 3 (go) + Jun 5 (go); only compressed days evaluate
E2E_WARMUP_DAYS = 20                 # Apr 30..May 27: < 20 trailing sessions => state not evaluated
E2E_NOT_COMPRESSED = 8               # May 28..Jun 10 evaluable days minus the 2 traded days
