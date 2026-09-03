"""Hand-computed goldens and SYNTHETIC fixtures for family1 (FXFV1-A3-P1).

Every UTC instant below was computed BY HAND from the US/UK DST rules and
cross-checked against ``zoneinfo`` truth (US: DST begins the second Sunday
in March and ends the first Sunday in November; UK: last Sundays of March
and October at 01:00 UTC):

* EST = UTC-5, EDT = UTC-4; BST = UTC+1, GMT = UTC+0.
* US spring-forward 2026-03-08 07:00Z; US fall-back 2026-11-01 06:00Z.
* UK spring-forward 2026-03-29 01:00Z; UK fall-back 2026-10-25 01:00Z.
* Session clocks (frozen): London open 08:00 Europe/London,
  New York open 08:00 America/New_York, rollover 17:00 America/New_York.

Golden days (London open L, NY rollover R, flatten-bar end = R - 1h,
always 16:00 New York wall clock):

* Mon 2026-01-19 (GMT + EST):  L = 08:00Z, R = 22:00Z, flatten end 21:00Z.
* Fri 2026-03-06 (GMT + EST):  L = 08:00Z, R = 22:00Z, flatten end 21:00Z.
* Mon 2026-03-09 (GMT + EDT):  L = 08:00Z, R = 21:00Z, flatten end 20:00Z
  (US sprung forward, UK not yet: the mismatch week).
* Mon 2026-06-15 (BST + EDT):  L = 07:00Z, R = 21:00Z, flatten end 20:00Z.
* Fri 2026-10-30 (GMT + EDT):  L = 08:00Z, R = 21:00Z, flatten end 20:00Z
  (UK already fell back on Oct 25, US not yet: the other mismatch week).
* Mon 2026-11-02 (GMT + EST):  L = 08:00Z, R = 22:00Z, flatten end 21:00Z.

Cost goldens (frozen 1.5 bps/side x tier, every fill):

  tier 1.0 (S1): 1.5 bps/side, 3.0 bps round trip
  tier 1.5 (S2): 2.25 bps/side, 4.5 bps round trip
  tier 2.0 (S3): 3.0 bps/side, 6.0 bps round trip (+ one-event entry delay)

A scenario producing 3 consecutive trades therefore books, hand-computed:
  first 3 fills cumulative  = 3 x 1.5 x tier = 4.5 / 6.75 / 9.0 bps
  full 6-fill totals        = 6 x 1.5 x tier = 9.0 / 13.5 / 18.0 bps

ALL data produced by this module is SYNTHETIC_TEST_ONLY: no real provider
bars, no scored PnL, no bid/ask, no volume.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

UTC = timezone.utc
TICK = 0.0001

# --- golden instants (hand-computed, zoneinfo-cross-checked in tests) ------- #
GOLDEN_DAYS: dict[str, dict] = {
    # date iso: {regime, london_open_z, rollover_z, flatten_end_z, entry_fill_z (S1, anchor)}
    "2026-01-19": {"regime": "GMT+EST", "london_open_z": "08:00Z", "rollover_z": "22:00Z", "flatten_end_z": "21:00Z", "entry_fill_z": "12:00Z", "signal_ts_z": "11:00Z"},
    "2026-03-06": {"regime": "GMT+EST", "london_open_z": "08:00Z", "rollover_z": "22:00Z", "flatten_end_z": "21:00Z", "entry_fill_z": "12:00Z", "signal_ts_z": "11:00Z"},
    "2026-03-09": {"regime": "GMT+EDT (US mismatch)", "london_open_z": "08:00Z", "rollover_z": "21:00Z", "flatten_end_z": "20:00Z", "entry_fill_z": "12:00Z", "signal_ts_z": "11:00Z"},
    "2026-06-15": {"regime": "BST+EDT", "london_open_z": "07:00Z", "rollover_z": "21:00Z", "flatten_end_z": "20:00Z", "entry_fill_z": "11:00Z", "signal_ts_z": "10:00Z"},
    "2026-10-30": {"regime": "GMT+EDT (UK mismatch)", "london_open_z": "08:00Z", "rollover_z": "21:00Z", "flatten_end_z": "20:00Z", "entry_fill_z": "12:00Z", "signal_ts_z": "11:00Z"},
    "2026-11-02": {"regime": "GMT+EST", "london_open_z": "08:00Z", "rollover_z": "22:00Z", "flatten_end_z": "21:00Z", "entry_fill_z": "12:00Z", "signal_ts_z": "11:00Z"},
}

# First 3 London-anchor golden instants on a GMT day (e.g. 2026-01-19):
# c0 bar starts 07:00Z (closes 08:00Z); session bars start 08/09/10Z
# (c3 closes 11:00Z = signal_ts); entry bar starts 11:00Z (fill 12:00Z);
# flatten bar starts 20:00Z (ends 21:00Z EST).  On a BST day (2026-06-15)
# every one of those instants moves one hour earlier in UTC.
ANCHOR_BAR_ROLES_GMT_DAY = {
    "c0_start_z": "07:00Z",
    "session_starts_z": ("08:00Z", "09:00Z", "10:00Z"),
    "entry_start_z": "11:00Z",
    "flatten_start_z": "20:00Z",
}

# Rising-closes golden day (base 1.1000, step +0.0010 per bar, 14 bars):
# closes[i] = 1.1000 + i*0.0010 for bars ending 08:00Z .. 21:00Z (GMT day).
#   c0 = 1.1000, c3 = 1.1030  -> m = 1.1030/1.1000 - 1 = +0.000272727... > 0 -> +1
#   S1 entry close = 1.1040 (bar ends 12:00Z), S3 entry close = 1.1050 (13:00Z)
#   flatten close  = 1.1130 (bar ends 21:00Z)
RISING_BASE = 1.1000
RISING_STEP = 0.0010
RISING_N_BARS = 14
RISING_C0 = 1.1000
RISING_C3 = 1.1030
RISING_M = RISING_C3 / RISING_C0 - 1.0  # +0.00027272727...
RISING_ENTRY_S1 = 1.1040
RISING_ENTRY_S3 = 1.1050
RISING_FLATTEN = 1.1130

# Falling-closes golden day: closes[i] = 1.1000 - i*0.0010.
#   c0 = 1.1000, c3 = 1.0970 -> m = 1.0970/1.1000 - 1 < 0 -> -1
FALLING_C0 = 1.1000
FALLING_C3 = 1.0970

# 3-trade cost scenario: three consecutive rising weekdays
# (Tue 2026-01-20 .. Thu 2026-01-22), anchor at each tier.
COST_SCENARIO_DAYS = ("2026-01-20", "2026-01-21", "2026-01-22")
COST_SCENARIO_N_TRADES = 3
# Hand arithmetic (3 trades x 2 fills x 1.5 bps/side x tier):
COST_GOLDENS = {
    1.0: {"per_side_bps": 1.5, "round_trip_bps": 3.0, "three_fill_bps": 4.5, "total_bps": 9.0, "cost_frac_per_trade": 3.0 / 1e4},
    1.5: {"per_side_bps": 2.25, "round_trip_bps": 4.5, "three_fill_bps": 6.75, "total_bps": 13.5, "cost_frac_per_trade": 4.5 / 1e4},
    2.0: {"per_side_bps": 3.0, "round_trip_bps": 6.0, "three_fill_bps": 9.0, "total_bps": 18.0, "cost_frac_per_trade": 6.0 / 1e4},
}

# Dry-run fixture: every hour of every weekday from Mon 2026-03-02 through
# Tue 2026-03-24 => 17 weekdays x 24 H1 bars = 408 hours (~400), spanning the
# US spring-forward transition (Sun 2026-03-08 07:00Z).  UK stays on GMT
# until 2026-03-29, so the week of 2026-03-09 is a London-GMT / NY-EDT
# mismatch week -- exercised for every arm.
DRYRUN_FIRST_DAY = date(2026, 3, 2)
DRYRUN_LAST_DAY = date(2026, 3, 24)
DRYRUN_N_WEEKDAYS = 17
DRYRUN_N_BARS = 408  # 17 * 24
DRYRUN_SPAN_DAYS = 23  # 2026-03-02T00:00Z .. 2026-03-25T00:00Z
# Feasibility goldens (hand arithmetic, intraday-monotone path => every
# weekday produces a nonzero momentum => exactly 17 trades):
#   years              = 23 / 365.25                = 0.06297056810266941
#   decisions_per_year = 17 * 365.25 / 23           = 269.96739130434784
#   turnover units     = 2 * 17 = 34;  per year     = 34 * 365.25 / 23 = 539.9347826086957
#   cost drag S1       = 269.96739130434784 * 3.0   = 809.9021739130435 bps/yr
DRYRUN_YEARS = 23.0 / 365.25
DRYRUN_DECISIONS_PER_YEAR = 17.0 * 365.25 / 23.0
DRYRUN_TURNOVER_UNITS_PER_YEAR = 34.0 * 365.25 / 23.0
DRYRUN_COST_DRAG_BPS_PER_YEAR_S1 = DRYRUN_DECISIONS_PER_YEAR * 3.0


# --- fixture builders (SYNTHETIC_TEST_ONLY) -------------------------------- #


def iso_z(dt: datetime) -> str:
    return dt.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_z(stamp: str) -> datetime:
    text = stamp[:-1] + "+00:00" if stamp.endswith("Z") else stamp
    return datetime.fromisoformat(text).astimezone(UTC)


def build_bars(starts: list[datetime], closes: list[float], first_open: float | None = None) -> list[dict]:
    """Synthetic H1 rows: open = previous close; high/low straddle by TICK."""
    rows: list[dict] = []
    prev_close = closes[0] if first_open is None else first_open
    for start, close in zip(starts, closes):
        o = prev_close
        rows.append(
            {
                "timestamp": iso_z(start),
                "open": o,
                "high": max(o, close) + TICK,
                "low": min(o, close) - TICK,
                "close": close,
            }
        )
        prev_close = close
    return rows


def day_starts(day: date, first_hour_z: int, n_bars: int) -> list[datetime]:
    """Whole-hour UTC bar opens on ``day``, from first_hour_z for n_bars hours."""
    base = datetime(day.year, day.month, day.day, first_hour_z, tzinfo=UTC)
    return [base + i * timedelta(hours=1) for i in range(n_bars)]


def anchor_day_bars(day: date, closes: list[float], first_hour_z: int) -> list[dict]:
    """A complete London-anchor pair-day: bars from c0 through the flatten bar.

    With n = 14 closes the last bar ends at first_hour_z + 14 hours, which
    must equal the day's flatten-bar end: first_hour_z = 7 on EST days
    (bars 07:00Z..20:00Z starts, flatten ends 21:00Z) and first_hour_z = 6
    on EDT days (bars 06:00Z..19:00Z starts, flatten ends 20:00Z).  The c0
    requirement (a bar starting one hour before the London open) is
    satisfied on both GMT and BST days by these choices.
    """
    return build_bars(day_starts(day, first_hour_z, len(closes)), closes)


def rising_closes(n: int = RISING_N_BARS, base: float = RISING_BASE, step: float = RISING_STEP) -> list[float]:
    return [base + i * step for i in range(n)]


def falling_closes(n: int = RISING_N_BARS, base: float = RISING_BASE, step: float = RISING_STEP) -> list[float]:
    return [base - i * step for i in range(n)]


def flat_closes(n: int = RISING_N_BARS, base: float = RISING_BASE) -> list[float]:
    return [base] * n


def multi_day_rising_bars(days: tuple[str, ...] = COST_SCENARIO_DAYS) -> list[dict]:
    """Independent complete GMT-day fixtures (EST NY) for the given weekdays."""
    rows: list[dict] = []
    for day_iso in days:
        y, m, d = (int(part) for part in day_iso.split("-"))
        rows.extend(anchor_day_bars(date(y, m, d), rising_closes(), first_hour_z=7))
    return rows


def dryrun_pair_bars(base: float, step: float = 2.0 * TICK, *, first_day: date = DRYRUN_FIRST_DAY, last_day: date = DRYRUN_LAST_DAY) -> list[dict]:
    """Deterministic ~400-hour synthetic pair fixture spanning one US DST jump.

    Every hour of every weekday in [first_day, last_day]; the intraday path
    is strictly monotone (direction alternates by day), so every session's
    3-bar momentum is nonzero and the trade count is exactly the number of
    weekdays.  Base level varies deterministically per day.  Purely
    synthetic: no provider data of any kind.
    """
    rows: list[dict] = []
    day = first_day
    k = 0
    while day <= last_day:
        if day.weekday() < 5:
            up = k % 2 == 0
            day_base = base * (1.0 + 0.005 * ((k * 37) % 61) / 61.0)
            price = day_base
            hours = day_starts(day, 0, 24)
            for start in hours:
                o = price
                c = price * (1.0 + step) if up else price * (1.0 - step)
                rows.append(
                    {
                        "timestamp": iso_z(start),
                        "open": o,
                        "high": max(o, c) + TICK,
                        "low": min(o, c) - TICK,
                        "close": c,
                    }
                )
                price = c
            k += 1
        day += timedelta(days=1)
    return rows
