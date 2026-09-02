"""A4 audit evidence: derive the frozen NYSE/Nasdaq regular-session table 2010-2030.

Run (from lane cwd):
  /Users/hoangminhlong/my-quantitative/.venv/bin/python \
    research/audits/stocks/s1_a4/generate_frozen_table.py

Rules encoded (NYSE Rule 7.2 as published on the pinned reference
https://www.nyse.com/trade/hours-calendars, cross-checked against the
published calendars 2010-2026 and documented market history):

* New Year's Day: Jan 1.  Falls on Sunday -> observed Monday Jan 2.
  Falls on Saturday -> NOT observed (regular session on the preceding
  Friday Dec 31).  Precedents: Dec 31 2004 (open), Dec 31 2010 (open,
  S&P 500 2010 = 252 sessions), Dec 31 2021 (open, S&P 500 closed the
  year on Fri 2021-12-31 at 4766.18).
* MLK Day: 3rd Monday of January.
* Washington's Birthday: 3rd Monday of February.
* Good Friday: 2 days before Easter Sunday (Anonymous Gregorian computus).
* Memorial Day: last Monday of May.
* Juneteenth National Independence Day: June 19, effective 2022 only
  (federal law signed 2021-06-17; NYSE first observed Mon 2022-06-20).
  Saturday -> observed Friday; Sunday -> observed Monday.
* Independence Day: July 4.  Saturday -> observed Friday July 3
  (precedents 2015, 2020); Sunday -> observed Monday July 5
  (precedents 2010, 2021).  Early close 13:00 ET on July 3 only when
  July 4 falls Tuesday-Friday (so July 3 is the session immediately
  preceding the holiday); when July 4 is Saturday the Friday July 3 is
  the FULL observed holiday, never an early close.
* Labor Day: 1st Monday of September.
* Thanksgiving: 4th Thursday of November; the day after (Friday) is a
  13:00 ET early close every year.
* Christmas: Dec 25.  Saturday -> observed Friday Dec 24 (precedents
  2010, 2021); Sunday -> observed Monday Dec 26 (precedents 2011, 2016,
  2022).  Early close 13:00 ET on Dec 24 only when Dec 25 falls
  Tuesday-Friday.
* Documented unscheduled full closures 2010-2030:
    2012-10-29, 2012-10-30  Hurricane Sandy
    2018-12-05              national day of mourning, G.H.W. Bush
    2025-01-09              national day of mourning, J. Carter

This generator is EVIDENCE ONLY.  The outputs are frozen as literals in
research/assets/stocks/calendar.py; runtime never re-derives them.
Sanity counts printed at the end are pinned against documented annual
NYSE session counts.
"""

from __future__ import annotations

from datetime import date, timedelta

START_YEAR, END_YEAR = 2010, 2030
MON, TUE, WED, THU, FRI, SAT, SUN = range(7)


def easter(year: int) -> date:
    """Anonymous Gregorian computus (valid 1583-4099)."""
    a = year % 19
    b, c = divmod(year, 100)
    d, e = divmod(b, 4)
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = divmod(c, 4)
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = (h + l - 7 * m + 114) % 31 + 1
    return date(year, month, day)


def nth_weekday(year: int, month: int, weekday: int, n: int) -> date:
    d = date(year, month, 1)
    offset = (weekday - d.weekday()) % 7
    return d + timedelta(days=offset + 7 * (n - 1))


def last_weekday(year: int, month: int, weekday: int) -> date:
    d = date(year, month + 1, 1) - timedelta(days=1)
    return d - timedelta(days=(d.weekday() - weekday) % 7)


holidays: dict[date, str] = {}
special: dict[date, str] = {
    date(2012, 10, 29): "HURRICANE_SANDY",
    date(2012, 10, 30): "HURRICANE_SANDY",
    date(2018, 12, 5): "NATIONAL_MOURNING_GHW_BUSH",
    date(2025, 1, 9): "NATIONAL_MOURNING_J_CARTER",
}


def add(d: date, name: str) -> None:
    if d.weekday() >= SAT:
        raise ValueError(f"holiday landed on a weekend unshifted: {d} {name}")
    if d in holidays:
        raise ValueError(f"duplicate holiday {d}: {name} vs {holidays[d]}")
    holidays[d] = name


for y in range(START_YEAR, END_YEAR + 1):
    jan1 = date(y, 1, 1)
    if jan1.weekday() == SUN:
        add(jan1 + timedelta(days=1), "NEW_YEARS_DAY_OBSERVED")  # Monday Jan 2
    elif jan1.weekday() != SAT:  # Saturday Jan 1 is NOT observed
        add(jan1, "NEW_YEARS_DAY")
    add(nth_weekday(y, 1, MON, 3), "MARTIN_LUTHER_KING_JR_DAY")
    add(nth_weekday(y, 2, MON, 3), "WASHINGTONS_BIRTHDAY")
    add(easter(y) - timedelta(days=2), "GOOD_FRIDAY")
    add(last_weekday(y, 5, MON), "MEMORIAL_DAY")
    if y >= 2022:  # Juneteenth effective 2022
        jun19 = date(y, 6, 19)
        if jun19.weekday() == SAT:
            add(date(y, 6, 18), "JUNETEENTH_OBSERVED")
        elif jun19.weekday() == SUN:
            add(date(y, 6, 20), "JUNETEENTH_OBSERVED")
        else:
            add(jun19, "JUNETEENTH")
    jul4 = date(y, 7, 4)
    if jul4.weekday() == SAT:
        add(date(y, 7, 3), "INDEPENDENCE_DAY_OBSERVED")
    elif jul4.weekday() == SUN:
        add(date(y, 7, 5), "INDEPENDENCE_DAY_OBSERVED")
    else:
        add(jul4, "INDEPENDENCE_DAY")
    add(nth_weekday(y, 9, MON, 1), "LABOR_DAY")
    add(nth_weekday(y, 11, THU, 4), "THANKSGIVING_DAY")
    dec25 = date(y, 12, 25)
    if dec25.weekday() == SAT:
        add(date(y, 12, 24), "CHRISTMAS_DAY_OBSERVED")
    elif dec25.weekday() == SUN:
        add(date(y, 12, 26), "CHRISTMAS_DAY_OBSERVED")
    else:
        add(dec25, "CHRISTMAS_DAY")

half_days: set[date] = set()
for y in range(START_YEAR, END_YEAR + 1):
    jul3 = date(y, 7, 3)
    if jul3.weekday() <= THU and jul3 not in holidays:  # Jul 4 falls Tue..Fri
        half_days.add(jul3)
    tday = nth_weekday(y, 11, THU, 4)
    half_days.add(tday + timedelta(days=1))  # Friday after Thanksgiving
    dec24 = date(y, 12, 24)
    if dec24.weekday() <= THU and dec24 not in holidays:  # Dec 25 falls Tue..Fri
        half_days.add(dec24)

if half_days & holidays.keys() or half_days & special.keys():
    raise ValueError("half day collides with a closure")

for d in sorted(special):
    if d.weekday() >= SAT:
        raise ValueError(f"special closure on weekend: {d}")

print(f"# holidays: {len(holidays)}  half_days: {len(half_days)}  special: {len(special)}")
print()
print("_HOLIDAYS: frozenset[str] = frozenset({")
for d in sorted(holidays):
    print(f'    "{d.isoformat()}",  # {holidays[d]}')
print("})")
print()
print("_HALF_DAYS: frozenset[str] = frozenset({")
for d in sorted(half_days):
    print(f'    "{d.isoformat()}",  # 13:00 ET early close')
print("})")
print()
print("_SPECIAL_CLOSURES: dict[str, str] = {")
for d in sorted(special):
    print(f'    "{d.isoformat()}": "{special[d]}",')
print("}")
print()

# --- sanity: documented annual NYSE regular-session counts ----------------- #
DOCUMENTED_COUNTS = {
    2010: 252, 2012: 250, 2018: 251, 2019: 252, 2020: 253,
    2021: 252, 2022: 251, 2023: 250, 2024: 252, 2025: 250,
}
for y, expected in DOCUMENTED_COUNTS.items():
    d0, d1 = date(y, 1, 1), date(y, 12, 31)
    n = 0
    d = d0
    while d <= d1:
        if d.weekday() < 5 and d not in holidays and d not in special:
            n += 1
        d += timedelta(days=1)
    flag = "OK " if n == expected else "MISMATCH"
    print(f"# {flag} {y}: computed {n} sessions, documented {expected}")
