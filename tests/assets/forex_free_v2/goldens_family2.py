"""Hand-computed synthetic fixtures and golden literals for family2
(FXFV2-A4-P2 evidence tests).

Every fixture is built bar-by-bar (td_loader schema: naive-UTC
"YYYY-MM-DD HH:MM:SS" bar-open stamps) and every expected number in this file
is a hand-computed LITERAL with its arithmetic shown in comments.  No real
data, no PnL anywhere (PnL goldens are booked through the accounting kernel in
test_family2.py from these literals).

Fixture calendar (BST/EDT week, London = UTC+1, New York = UTC-4):
* weekend warmup: Sat 2025-05-31 + Sun 2025-06-01, 48 flat bars at 1.1000
  (indices 0..47; flat bars can never break a range: break needs strict
  ``high > L_H`` / ``low < L_L`` and 1.1000 == 1.1000 fails both).
* day1 Mon 2025-06-02: UP break + retest-hold firing BOTH anchor (L_B) and
  neighbour (E_B) on the same 12:00Z bar; invalidation exit.
* day2 Tue 2025-06-03: neighbour-only retest (touch between L_B and E_B),
  anchor voids at 15:00Z, control enters the void in the ORIGINAL UP direction
  and exits forced-flat at the 16:00-New-York bar (20:00Z).
* day3 Wed 2025-06-04: DOWN break + DOWN retest-hold (anchor only);
  invalidation exit.
* day4 Thu 2025-06-05: UP break voided immediately; control trades the void,
  exits by invalidation.
"""
from __future__ import annotations

import datetime as _dt
from zoneinfo import ZoneInfo

UTC = _dt.timezone.utc
LONDON = ZoneInfo("Europe/London")
NEW_YORK = ZoneInfo("America/New_York")


def U(y: int, mo: int, d: int, h: int, mi: int = 0) -> _dt.datetime:
    return _dt.datetime(y, mo, d, h, mi, tzinfo=UTC)


def bar(moment: _dt.datetime, o: float, h: float, l: float, c: float) -> dict:
    """One canonical H1 bar (bar-open UTC stamp, td_loader schema)."""
    return {"datetime": moment.strftime("%Y-%m-%d %H:%M:%S"),
            "open": o, "high": h, "low": l, "close": c}


# ---------------------------------------------------------------- warmup ------- #
def weekend_warmup(saturday: _dt.date, level: float = 1.1000) -> list[dict]:
    """48 flat H1 bars covering Saturday+Sunday (indices 0..47 = frozen warmup).

    Flat bars at ``level``: every range is [level, level] and the break test
    (strict > / strict <) can never fire -- warmup days are never evaluated
    anyway (the first evaluable day is the London-local date of bar 48).
    """
    rows = []
    for offset in range(48):
        day = saturday + _dt.timedelta(days=offset // 24)
        hour = offset % 24
        rows.append(bar(U(day.year, day.month, day.day, hour), level, level, level, level))
    return rows


# --------------------------------------------------- day1: golden UP trade ----- #
# London-AM range (07:00Z..10:00Z = London 08:00..11:00 BST):
#   L_H = max highs = 1.1020 (09:00Z bar)      L_L = min lows = 1.1000 (07:00Z bar)
#   midpoint = (1.1020 + 1.1000) / 2 = 1.1010
# break 11:00Z: high 1.1025 > L_H 1.1020 -> UP; low 1.1009 > L_L (single side)
#   L_B = 1.1020, E_B = break-bar high = 1.1025
# retest 12:00Z: low 1.1018 <= L_B 1.1020 AND close 1.1026 > 1.1020 -> anchor DECISION
#   neighbour: low 1.1018 <= E_B 1.1025 AND close 1.1026 > 1.1025 -> fires too
# entry 13:00Z open = 1.1024 (one-event lag; decision_ts = 12:00Z + 1h = 13:00Z)
# invalidation 14:00Z: close 1.1015 < L_H 1.1020 -> exit 15:00Z open = 1.1015
# forced-flat instant would be 16:00 NY EDT = 20:00Z (never reached: 15:00Z < 20:00Z)
GOLDEN_UP = {
    "pair": "EUR/USD",
    "side": 1,
    "notional_usd": 10000.0,
    "entry_price": 1.1024,
    "entry_ts": "2025-06-02T13:00:00Z",
    "decision_ts": "2025-06-02T13:00:00Z",
    "exit_price": 1.1015,
    "exit_ts": "2025-06-02T15:00:00Z",
    "exit_reason": "invalidation",
}


def day1_up_invalidation(day: _dt.date) -> list[dict]:
    """The golden UP day (prices fixed, date parameterized for reuse)."""
    y, m, d = day.year, day.month, day.day
    rows = [
        # London 08:00-11:00 (BST) = 07:00Z..10:00Z: range bars (all 4 required)
        bar(U(y, m, d, 7), 1.1002, 1.1010, 1.1000, 1.1005),
        bar(U(y, m, d, 8), 1.1005, 1.1015, 1.1001, 1.1012),
        bar(U(y, m, d, 9), 1.1012, 1.1020, 1.1005, 1.1018),
        bar(U(y, m, d, 10), 1.1018, 1.1019, 1.1008, 1.1010),
        # London 12:00 = 11:00Z: initial break UP (high 1.1025 > L_H 1.1020)
        bar(U(y, m, d, 11), 1.1010, 1.1025, 1.1009, 1.1022),
        # London 13:00 = 12:00Z: retest-hold fires for anchor AND neighbour
        bar(U(y, m, d, 12), 1.1022, 1.1030, 1.1018, 1.1026),
        # London 14:00 = 13:00Z: ENTRY bar (open 1.1024)
        bar(U(y, m, d, 13), 1.1024, 1.1028, 1.1021, 1.1025),
        # London 15:00 = 14:00Z: invalidating close 1.1015 < L_H 1.1020
        bar(U(y, m, d, 14), 1.1025, 1.1027, 1.1019, 1.1015),
        # London 16:00 = 15:00Z: EXIT bar (open 1.1015)
        bar(U(y, m, d, 15), 1.1015, 1.1016, 1.1005, 1.1008),
        bar(U(y, m, d, 16), 1.1008, 1.1012, 1.1002, 1.1006),
        bar(U(y, m, d, 17), 1.1006, 1.1009, 1.1000, 1.1003),
        bar(U(y, m, d, 18), 1.1003, 1.1007, 1.0998, 1.1001),
        bar(U(y, m, d, 19), 1.1001, 1.1004, 1.0996, 1.1000),
        # London 21:00 = 20:00Z = 16:00 America/New_York EDT (forced-flat bar)
        bar(U(y, m, d, 20), 1.1000, 1.1003, 1.0995, 1.1002),
    ]
    return rows


# ----------------------- day2: neighbour-only fire; anchor VOID; control UP ---- #
# Range: L_H = 1.1030 (09:00Z), L_L = 1.1010 (07:00Z), mid = 1.1020
# break 11:00Z: high 1.1040 > 1.1030 -> UP; low 1.1015 > L_L (single side)
#   L_B = 1.1030, E_B = 1.1040
# 12:00Z: low 1.1036 <= E_B 1.1040 AND close 1.1042 > 1.1040 -> NEIGHBOUR fires;
#   anchor: low 1.1036 > L_B 1.1030 (no touch of the broken range extreme)
# 13:00Z: neighbour ENTRY (open 1.1041); anchor: low 1.1033 > 1.1030, no void
# 14:00Z: anchor: low 1.1031 > 1.1030; close 1.1035 > L_H, no void
# 15:00Z: VOID fires (close 1.1028 < L_H 1.1030, before any anchor retest)
#   neighbour invalidation: close 1.1028 < L_H -> exit 16:00Z open 1.1030
# 16:00Z: neighbour EXIT (1.1030); CONTROL entry (void decision bar 15:00Z + 1h),
#   ORIGINAL break direction = UP, entry open 1.1030
# control invalidation (UP entry: close < L_L 1.1010): closes 1.1026/1.1022/
#   1.1018/1.1013/1.1014 all > 1.1010 -> never hits
# 20:00Z (16:00 New York): control FORCED FLAT at open 1.1012
GOLDEN_NEIGHBOUR_DAY2 = {
    "side": 1, "entry_price": 1.1041, "entry_ts": "2025-06-03T13:00:00Z",
    "decision_ts": "2025-06-03T13:00:00Z",
    "exit_price": 1.1030, "exit_ts": "2025-06-03T16:00:00Z",
    "exit_reason": "invalidation",
}
GOLDEN_CONTROL_DAY2 = {
    "side": 1, "entry_price": 1.1030, "entry_ts": "2025-06-03T16:00:00Z",
    "decision_ts": "2025-06-03T16:00:00Z",
    "exit_price": 1.1012, "exit_ts": "2025-06-03T20:00:00Z",
    "exit_reason": "forced_flat",
}


def day2_neighbour_void(day: _dt.date) -> list[dict]:
    y, m, d = day.year, day.month, day.day
    return [
        bar(U(y, m, d, 7), 1.1012, 1.1022, 1.1010, 1.1018),   # L_H=1.1030 L_L=1.1010
        bar(U(y, m, d, 8), 1.1018, 1.1028, 1.1015, 1.1025),
        bar(U(y, m, d, 9), 1.1025, 1.1030, 1.1020, 1.1028),
        bar(U(y, m, d, 10), 1.1028, 1.1029, 1.1021, 1.1024),
        bar(U(y, m, d, 11), 1.1024, 1.1040, 1.1015, 1.1035),  # break UP, E_B=1.1040
        bar(U(y, m, d, 12), 1.1038, 1.1045, 1.1036, 1.1042),  # neighbour retest only
        bar(U(y, m, d, 13), 1.1041, 1.1044, 1.1033, 1.1039),  # neighbour entry 1.1041
        bar(U(y, m, d, 14), 1.1039, 1.1041, 1.1031, 1.1035),
        bar(U(y, m, d, 15), 1.1035, 1.1037, 1.1026, 1.1028),  # VOID (< L_H 1.1030)
        bar(U(y, m, d, 16), 1.1030, 1.1032, 1.1022, 1.1026),  # neigh exit / ctrl entry
        bar(U(y, m, d, 17), 1.1026, 1.1029, 1.1019, 1.1022),
        bar(U(y, m, d, 18), 1.1022, 1.1024, 1.1015, 1.1018),
        bar(U(y, m, d, 19), 1.1018, 1.1020, 1.1011, 1.1013),
        bar(U(y, m, d, 20), 1.1012, 1.1016, 1.1008, 1.1014),  # ctrl forced flat 1.1012
    ]


# ------------------------------------------------- day3: golden DOWN trade ----- #
# Range: L_H = 1.2080 (07:00Z), L_L = 1.2060 (10:00Z), mid = 1.2070
# break 11:00Z: low 1.2055 < L_L 1.2060 -> DOWN (high 1.2072 < L_H, single side)
#   L_B = 1.2060, E_B = break-bar low = 1.2055
# retest 12:00Z (DOWN): high 1.2062 >= L_B 1.2060 AND close 1.2056 < 1.2060 -> fires
#   neighbour: close 1.2056 < E_B 1.2055? NO (1.2056 > 1.2055) -> does not fire
# entry 13:00Z open 1.2057, side = -1 (SHORT)
# invalidation (short: close > L_L 1.2060): 13:00Z close 1.2058 no;
#   14:00Z close 1.2063 > 1.2060 YES -> exit 15:00Z open 1.2064
GOLDEN_DOWN = {
    "pair": "EUR/USD",
    "side": -1,
    "notional_usd": 10000.0,
    "entry_price": 1.2057,
    "entry_ts": "2025-06-04T13:00:00Z",
    "decision_ts": "2025-06-04T13:00:00Z",
    "exit_price": 1.2064,
    "exit_ts": "2025-06-04T15:00:00Z",
    "exit_reason": "invalidation",
}


def day3_down(day: _dt.date) -> list[dict]:
    y, m, d = day.year, day.month, day.day
    return [
        bar(U(y, m, d, 7), 1.2072, 1.2080, 1.2070, 1.2075),   # L_H=1.2080
        bar(U(y, m, d, 8), 1.2075, 1.2079, 1.2068, 1.2072),
        bar(U(y, m, d, 9), 1.2072, 1.2076, 1.2062, 1.2065),
        bar(U(y, m, d, 10), 1.2065, 1.2072, 1.2060, 1.2068),  # L_L=1.2060
        bar(U(y, m, d, 11), 1.2068, 1.2072, 1.2055, 1.2058),  # break DOWN, E_B=1.2055
        bar(U(y, m, d, 12), 1.2058, 1.2062, 1.2054, 1.2056),  # anchor retest only
        bar(U(y, m, d, 13), 1.2057, 1.2060, 1.2055, 1.2058),  # entry SHORT 1.2057
        bar(U(y, m, d, 14), 1.2058, 1.2065, 1.2056, 1.2063),  # invalidating 1.2063>1.2060
        bar(U(y, m, d, 15), 1.2064, 1.2066, 1.2058, 1.2062),  # exit 1.2064
        bar(U(y, m, d, 16), 1.2062, 1.2064, 1.2057, 1.2060),
        bar(U(y, m, d, 17), 1.2060, 1.2063, 1.2056, 1.2059),
        bar(U(y, m, d, 18), 1.2059, 1.2061, 1.2055, 1.2058),
        bar(U(y, m, d, 19), 1.2058, 1.2060, 1.2053, 1.2057),
        bar(U(y, m, d, 20), 1.2057, 1.2059, 1.2052, 1.2056),
    ]


# ----------------------------- day4: immediate void; control trades the void --- #
# Range: L_H = 1.1022 (09:00Z), L_L = 1.1008 (07:00Z)
# break 11:00Z: high 1.1030 > 1.1022 -> UP; low 1.1010 > L_L (single side)
#   L_B = 1.1022, E_B = 1.1030
# 12:00Z: close 1.1018 < L_H 1.1022 -> VOID immediately (no retest: 1.1018 is
#   neither > L_B 1.1022 nor > E_B 1.1030)
# control entry 13:00Z open 1.1018 (UP, original break direction)
# control invalidation (close < L_L 1.1008): 14:00Z 1.1012 no; 15:00Z 1.1010 no;
#   16:00Z close 1.1006 < 1.1008 YES -> exit 17:00Z open 1.1006
GOLDEN_CONTROL_DAY4 = {
    "side": 1, "entry_price": 1.1018, "entry_ts": "2025-06-05T13:00:00Z",
    "decision_ts": "2025-06-05T13:00:00Z",
    "exit_price": 1.1006, "exit_ts": "2025-06-05T17:00:00Z",
    "exit_reason": "invalidation",
}


def day4_void(day: _dt.date) -> list[dict]:
    y, m, d = day.year, day.month, day.day
    return [
        bar(U(y, m, d, 7), 1.1010, 1.1018, 1.1008, 1.1012),   # L_H=1.1022 L_L=1.1008
        bar(U(y, m, d, 8), 1.1012, 1.1020, 1.1010, 1.1016),
        bar(U(y, m, d, 9), 1.1016, 1.1022, 1.1012, 1.1018),
        bar(U(y, m, d, 10), 1.1018, 1.1019, 1.1010, 1.1012),
        bar(U(y, m, d, 11), 1.1012, 1.1030, 1.1010, 1.1026),  # break UP
        bar(U(y, m, d, 12), 1.1026, 1.1028, 1.1016, 1.1018),  # immediate VOID
        bar(U(y, m, d, 13), 1.1018, 1.1020, 1.1012, 1.1014),  # control entry 1.1018
        bar(U(y, m, d, 14), 1.1014, 1.1016, 1.1009, 1.1012),
        bar(U(y, m, d, 15), 1.1012, 1.1014, 1.1006, 1.1010),
        bar(U(y, m, d, 16), 1.1010, 1.1012, 1.1004, 1.1006),  # ctrl invalidation
        bar(U(y, m, d, 17), 1.1006, 1.1008, 1.1000, 1.1003),  # ctrl exit 1.1006
        bar(U(y, m, d, 18), 1.1003, 1.1006, 1.0998, 1.1000),
        bar(U(y, m, d, 19), 1.1000, 1.1003, 1.0995, 1.0998),
        bar(U(y, m, d, 20), 1.0998, 1.1000, 1.0992, 1.0995),
    ]


# ---------------------------------------------------------------- universes ---- #
def four_day_week(pair: str = "EUR/USD") -> dict[str, list[dict]]:
    """Warmup + the four golden days 2025-06-02..05 (one pair)."""
    rows = weekend_warmup(_dt.date(2025, 5, 31))
    rows += day1_up_invalidation(_dt.date(2025, 6, 2))
    rows += day2_neighbour_void(_dt.date(2025, 6, 3))
    rows += day3_down(_dt.date(2025, 6, 4))
    rows += day4_void(_dt.date(2025, 6, 5))
    return {pair: rows}


# both-sides-in-one-bar goldens (state-machine level; L_H=1.1020, L_L=1.1000,
# midpoint = (1.1020+1.1000)/2 = 1.1010; break bar spans BOTH sides:
# high 1.1030 > L_H and low 1.0990 < L_L)
BOTH_SIDES_RANGE = [(1.1002, 1.1010, 1.1000, 1.1005),
                    (1.1005, 1.1015, 1.1001, 1.1012),
                    (1.1012, 1.1020, 1.1005, 1.1018),
                    (1.1018, 1.1019, 1.1008, 1.1010)]
BOTH_SIDES_MIDPOINT = 1.1010
BOTH_SIDES_UP_CLOSE = 1.1015      # 1.1015 > midpoint 1.1010 -> side UP (+1)
BOTH_SIDES_DOWN_CLOSE = 1.1005    # 1.1005 < midpoint 1.1010 -> side DOWN (-1)
BOTH_SIDES_TIE_CLOSE = 1.1010     # close == midpoint exactly -> TIE (no trade)


def both_sides_day(day: _dt.date, close: float) -> list[dict]:
    """One day whose 12:00-London bar breaks BOTH sides; ``close`` picks the
    sign(close - 1.1010) rule (1.1010 exactly = tie)."""
    y, m, d = day.year, day.month, day.day
    rows = [bar(U(y, m, d, 7), *BOTH_SIDES_RANGE[0]),
            bar(U(y, m, d, 8), *BOTH_SIDES_RANGE[1]),
            bar(U(y, m, d, 9), *BOTH_SIDES_RANGE[2]),
            bar(U(y, m, d, 10), *BOTH_SIDES_RANGE[3])]
    rows.append(bar(U(y, m, d, 11), 1.1010, 1.1030, 1.0990, close))
    return rows


# --------------------------------------------------- DST-day template ---------- #
def london_hours_day(day: _dt.date, hold_flat: bool) -> list[dict]:
    """Golden UP day built from London WALL hours 08:00..21:00 (zoneinfo) so the
    same price script lands on the DST-correct UTC instants in any regime.

    London 08..11 = range; 12 = break UP; 13 = retest (anchor+neighbour);
    14 = entry; 15 = invalidating close (unless ``hold_flat``); 16..21 tail.
    The forced-flat bar (16:00 America/New_York) is always London 20:00 (GMT
    weeks) or 21:00 (BST weeks), so it is always inside the generated set.
    With ``hold_flat`` every close from London 15:00 onward stays above L_H
    (1.1020) so no invalidation fires and the exit is the forced flat.
    """
    prices = {  # hour -> (o, h, l, c); L_H = 1.1020, L_L = 1.1000
        8: (1.1002, 1.1010, 1.1000, 1.1005),
        9: (1.1005, 1.1015, 1.1001, 1.1012),
        10: (1.1012, 1.1020, 1.1005, 1.1018),
        11: (1.1018, 1.1019, 1.1008, 1.1010),
        12: (1.1010, 1.1025, 1.1009, 1.1022),   # break UP (E_B = 1.1025)
        13: (1.1022, 1.1030, 1.1018, 1.1026),   # retest (1.1018 <= 1.1020 < 1.1026)
        14: (1.1024, 1.1028, 1.1021, 1.1025),   # entry 1.1024
        15: (1.1025, 1.1027, 1.1019, 1.1015),   # invalidating close 1.1015 < 1.1020
        16: (1.1015, 1.1016, 1.1005, 1.1008),   # exit 1.1015
        17: (1.1008, 1.1012, 1.1002, 1.1006),
        18: (1.1006, 1.1009, 1.1000, 1.1003),
        19: (1.1003, 1.1007, 1.0998, 1.1001),
        20: (1.1001, 1.1004, 1.0996, 1.1000),
        21: (1.1000, 1.1003, 1.0995, 1.1002),
    }
    if hold_flat:  # keep every post-entry close > L_H 1.1020 -> no invalidation
        prices.update({
            15: (1.1025, 1.1029, 1.1021, 1.1027),
            16: (1.1027, 1.1031, 1.1023, 1.1029),
            17: (1.1029, 1.1033, 1.1025, 1.1031),
            18: (1.1031, 1.1034, 1.1026, 1.1030),
            19: (1.1030, 1.1033, 1.1024, 1.1028),
            20: (1.1028, 1.1031, 1.1022, 1.1026),
            21: (1.1026, 1.1029, 1.1020, 1.1024),
        })
    rows = []
    for hour in range(8, 22):
        moment = _dt.datetime.combine(day, _dt.time(hour), tzinfo=LONDON)
        rows.append(bar(moment.astimezone(UTC), *prices[hour]))
    return rows


# Expected UTC instants (hand-computed zoneinfo arithmetic, cross-checked
# against `Z-suffix` tables):
#   2025-03-10: US on EDT since 03-09, EU still GMT until 03-30 (DESYNC):
#     London 08:00 GMT = 08:00Z; 16:00 New York EDT = 20:00Z
#   2025-03-31: EU on BST since 03-30, US on EDT:
#     London 08:00 BST = 07:00Z; 16:00 New York EDT = 20:00Z
#   2025-10-27: EU on GMT since 10-26, US still EDT until 11-02 (DESYNC):
#     London 08:00 GMT = 08:00Z; 16:00 New York EDT = 20:00Z
#   2025-11-03: EU on GMT, US on EST since 11-02:
#     London 08:00 GMT = 08:00Z; 16:00 New York EST = 21:00Z
DST_CASES = [
    # (trading Monday, london08_utc_hour, entry "HH:MM:SS"Z, invalidation exit, flat "HH:MM:SS"Z)
    (_dt.date(2025, 3, 10), 8, "2025-03-10T14:00:00Z", "2025-03-10T16:00:00Z", "2025-03-10T20:00:00Z"),
    (_dt.date(2025, 3, 31), 7, "2025-03-31T13:00:00Z", "2025-03-31T15:00:00Z", "2025-03-31T20:00:00Z"),
    (_dt.date(2025, 10, 27), 8, "2025-10-27T14:00:00Z", "2025-10-27T16:00:00Z", "2025-10-27T20:00:00Z"),
    (_dt.date(2025, 11, 3), 8, "2025-11-03T14:00:00Z", "2025-11-03T16:00:00Z", "2025-11-03T21:00:00Z"),
]

# The four NAMED transition dates themselves (Sundays; no London-AM session
# exists on a Sunday, so the trading evidence uses the following Monday above
# while the clock evidence below pins the transitions exactly):
DST_TRANSITION_FLAT_INSTANTS = {
    _dt.date(2025, 3, 9): "2025-03-09T20:00:00Z",    # US spring forward -> EDT (UTC-4)
    _dt.date(2025, 11, 2): "2025-11-02T21:00:00Z",   # US fall back -> EST (UTC-5)
    _dt.date(2025, 3, 30): "2025-03-30T20:00:00Z",   # EU spring forward (NY already EDT)
    _dt.date(2025, 10, 26): "2025-10-26T20:00:00Z",  # EU fall back (NY still EDT)
}


# --------------------------------------------- Friday forced-flat fixtures ----- #
def friday_early_flat_day(day: _dt.date | None = None, drop_after_hour: int | None = None,
                          hold_flat: bool = True) -> list[dict]:
    """Friday 2025-06-06 with the 16:00-New-York bar (20:00Z) ABSENT (the
    weekly close lands exactly at 16:00 NY, so that bar never exists).

    ``hold_flat`` keeps post-entry closes above L_H (no invalidation) so the
    exit must come from the forced-flat fallback: the latest existing bar
    strictly between the entry (13:00Z) and the flat instant (20:00Z).
    ``drop_after_hour`` additionally removes every bar after that London-hour
    UTC stamp (18:00Z..20:00Z when 17) to make the flat exit UNRESOLVABLE.
    """
    day = day or _dt.date(2025, 6, 6)
    rows = london_hours_day(day, hold_flat=hold_flat)
    if drop_after_hour is not None:
        # stamps are "%Y-%m-%d %H:%M:%S" strings: lexicographic == chronological
        cutoff = f"{day.isoformat()} {drop_after_hour:02d}:00:00"
        rows = [b for b in rows if b["datetime"] <= cutoff]
    return rows


# ------------------------------------------- governor-binding fixture ---------- #
def governor_week(pair: str = "GBP/USD") -> dict[str, list[dict]]:
    """Five anchor-fireable days: Mon-Thu 2025-06-02..05 (one UTC week) plus
    Mon 2025-06-09 (next week).  Week [2025-06-02 00:00Z, 2025-06-09 00:00Z):
    days 1-3 book (RT #1..#3 = the frozen cap), day 4 must be dropped
    (WEEKLY_CAP), the next Monday books again (fresh week)."""
    rows = weekend_warmup(_dt.date(2025, 5, 31))
    for day in (_dt.date(2025, 6, 2), _dt.date(2025, 6, 3),
                _dt.date(2025, 6, 4), _dt.date(2025, 6, 5)):
        rows += day1_up_invalidation(day)
    rows += day1_up_invalidation(_dt.date(2025, 6, 9))
    return {pair: rows}


# --------------------------------------------- golden booked-PnL literals ------ #
# UP trade (day1): entry 1.1024, exit 1.1015
#   pnl = +1 * 10000 * (1.1015 / 1.1024 - 1)
#       = 10000 * (-0.0009 / 1.1024) = 10000 * (-8.16057979...e-4) = -8.16057979... USD
#   cost/side (tier 1.0) = 10000 * 1.5 / 10000 = 1.50 USD; round trip = 3.00 USD
#   net = -8.16057979... - 3.00 = -11.16057979... USD
# DOWN trade (day3): entry 1.2057, exit 1.2064
#   pnl = -1 * 10000 * (1.2064 / 1.2057 - 1)
#       = 10000 * (0.0007 / 1.2057) = 10000 * (5.80590461...e-4) = +5.80590461... USD
#   net = +5.80590461... - 3.00 = +2.80590461... USD
GOLDEN_UP_PNL_EXPR = lambda: 10000.0 * (1.1015 / 1.1024 - 1.0)       # noqa: E731
GOLDEN_DOWN_PNL_EXPR = lambda: -10000.0 * (1.2064 / 1.2057 - 1.0)    # noqa: E731
GOLDEN_COST_PER_SIDE_TIER1 = 10000.0 * 1.5 / 10000.0                 # exactly 1.5 USD
