#!/usr/bin/env python3
"""Deterministic SYNTHETIC fixture for FOREX-FREE-V9 tests + diagnostic smoke.

Builds into <target_dir> (deterministic bytes on every run; fixed LCG, no
numpy, no wall clock, no network):

  {PAIR}.json                              daily spot snapshot, Twelve Data
                                           time_series 1day provider format
                                           (values newest-first), one bar per
                                           grid weekday 2018-04-04..2019-12-31
  cpi/GB/ons_d7bt_cpi_allitems.csv         ONS D7BT table format (metadata
                                           header + annual rows + "YYYY MON"
                                           monthly rows), 2014-01..2019-12
  cpi/CA/canada_allitems_nsa_2002_100_monthly.csv   StatCan tidy format
  cpi/fred_vintaged/AUSCPIALLQINMEI.json   ALFRED nested quarterly archives
  cpi/fred_vintaged/NZLCPIALLQINMEI.json   (mass vintage 2018-05-15 + per-
                                           quarter first-bindings thereafter
                                           -- the census vintage classes)
  cpi/US/fred_cpiaucsl_rt.json             flat-list monthly vintaged archive
                                           (history vintage + mid-next-month
                                           first-bindings)
  cpi/calendars/gb_cal.json                pinned-calendar subset (2018-01..
  cpi/calendars/ca_cal_v3.json             2019-11; earlier prints fall back
                                           to the mid-next-month placeholder)
  ledger.jsonl                             V5-format static policy-rate
                                           vintages for GB/US/CA/AU/NZ

The home legs are exact sinusoids in log space: pi_e(i) = 0.02 + 2A sin(2pi
i/24 + phi_e) with A = 0.004 (pi = y/y log step, i = months since 2014-01),
so the surprise (pi minus its trailing-24 OLS trend, x100) swings +-0.8pp
through the frozen 0.25/0.15 thresholds, and the 63d momentum of the gap
swings through the 0.15/0.10 thresholds.  The US leg runs a 36-month
sinusoid so the control (home-only / level) path differs from the anchor.

The fixture drives MECHANICS tests only.  It encodes no production outcome
data and computes no PnL (booking happens only in the gated scored path).
"""
from __future__ import annotations

import json
import math
import os
import sys
from datetime import date, timedelta
PAIRS = ["GBPUSD", "USDCAD", "AUDUSD", "NZDUSD"]
AREAS = ["GB", "US", "CA", "AU", "NZ"]
START = date(2018, 4, 4)
END = date(2019, 12, 31)
CPI_START = date(2014, 1, 1)
CPI_END = date(2019, 12, 1)
QCPI_START = date(2014, 4, 1)          # quarterly obs at quarter-first-months
QCPI_END = date(2019, 10, 1)
MASS_VINTAGE = date(2018, 5, 15)       # AU/NZ mass-binding vintage class

PHASE = {"GB": 0.0, "CA": 1.1, "AU": 2.2, "NZ": 3.3, "US": 0.7}
AMP_HOME = 0.004
AMP_US = 0.003
_US_PERIOD = 36.0
MON_ABBR = ("JAN", "FEB", "MAR", "APR", "MAY", "JUN",
            "JUL", "AUG", "SEP", "OCT", "NOV", "DEC")
MON_FULL = ("January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November",
            "December")

_LCG_STATE = 20260910


def _lcg() -> float:
    global _LCG_STATE
    _LCG_STATE = (1103515245 * _LCG_STATE + 12345) % (1 << 31)
    return _LCG_STATE / float(1 << 31)


def months(start: date, end: date):
    out, d = [], start
    while d <= end:
        out.append(d)
        d = date(d.year + (1 if d.month == 12 else 0),
                 1 if d.month == 12 else d.month + 1, 1)
    return out


def quarters(start: date, end: date):
    return [d for d in months(start, end) if d.month in (1, 4, 7, 10)]


def weekdays(start: date, end: date):
    d, out = start, []
    while d <= end:
        if d.weekday() < 5:
            out.append(d)
        d += timedelta(days=1)
    return out


def month_index(d: date) -> int:
    return (d.year - CPI_START.year) * 12 + (d.month - CPI_START.month)


def log_level(d: date, economy: str) -> float:
    """Frozen synthetic log index level.  With g(i) = c*i/12 + B*sin(2pi i/24
    + phi), the y/y log step is EXACTLY g(i) - g(i-12) = c + 2B sin(2pi i/24
    + phi) -- the closed-form pi of the module docstring (hand-checkable,
    no accumulated floating error).  The US leg runs a 36-month level
    sinusoid (y/y amplitude 2E sin(pi/3))."""
    i = month_index(d)
    if economy == "US":
        return 0.02 * i / 12.0 + AMP_US * math.sin(2 * math.pi * i
                                                   / _US_PERIOD + PHASE["US"])
    return (0.02 * i / 12.0
            + AMP_HOME * math.sin(2 * math.pi * i / 24.0 + PHASE[economy]))


def levels(economy: str, obs_dates) -> dict:
    return {d: math.exp(log_level(d, economy)) for d in obs_dates}


def main(target):
    days = weekdays(START, END)
    os.makedirs(os.path.join(target, "cpi", "GB"), exist_ok=True)
    os.makedirs(os.path.join(target, "cpi", "CA"), exist_ok=True)
    os.makedirs(os.path.join(target, "cpi", "fred_vintaged"), exist_ok=True)
    os.makedirs(os.path.join(target, "cpi", "US"), exist_ok=True)
    os.makedirs(os.path.join(target, "cpi", "calendars"), exist_ok=True)

    # ---- official monthly tables (GB ONS format, CA StatCan tidy) --------
    gb_levels = levels("GB", months(CPI_START, CPI_END))
    lines = [
        '"Title","CPI INDEX 00: ALL ITEMS 2015=100"',
        '"CDID","D7BT"',
        '"Source dataset ID","MM23"',
        '"PreUnit",""',
        '"Unit","Index, base year = 100"',
        '"Release date","19-08-2026"',
        '"Next release","16 September 2026"',
        '"Important notes",',
        '"2013","92.4"',                      # annual row -- skipped
    ]
    for d in sorted(gb_levels):
        lines.append(f'"{d.year} {MON_ABBR[d.month - 1]}",'
                     f'"{gb_levels[d]:.6f}"')
    with open(os.path.join(target, "cpi", "GB",
                           "ons_d7bt_cpi_allitems.csv"), "w") as f:
        f.write("\n".join(lines) + "\n")

    ca_levels = levels("CA", months(CPI_START, CPI_END))
    with open(os.path.join(target, "cpi", "CA",
                           "canada_allitems_nsa_2002_100_monthly.csv"),
              "w") as f:
        f.write("ref_month,index_2002_100\n")
        for d in sorted(ca_levels):
            f.write(f"{d.year}-{d.month:02d},{ca_levels[d]:.6f}\n")

    # ---- FRED vintaged archives (US flat list; AU/NZ nested ALFRED) ------
    def rt_mid_next(d: date) -> date:
        nxt = date(d.year + (1 if d.month == 12 else 0),
                   1 if d.month == 12 else d.month + 1, 14)
        return nxt

    def add_months_first(d: date, k: int) -> date:
        m0 = d.year * 12 + (d.month - 1) + k
        return date(m0 // 12, m0 % 12 + 1, 1)

    us_rows = []
    us_levels = levels("US", months(CPI_START, CPI_END))
    hist_cut = date(2017, 1, 1)
    for d in sorted(us_levels):
        if d < hist_cut:
            us_rows.append({"date": d.isoformat(),
                            "realtime_start": "2017-01-01",
                            "realtime_end": "2030-01-01",
                            "value": f"{us_levels[d]:.6f}"})
        else:
            us_rows.append({"date": d.isoformat(),
                            "realtime_start": rt_mid_next(d).isoformat(),
                            "realtime_end": "2030-01-01",
                            "value": f"{us_levels[d]:.6f}"})
    with open(os.path.join(target, "cpi", "US", "fred_cpiaucsl_rt.json"),
              "w") as f:
        json.dump(us_rows, f)

    for econ in ("AU", "NZ"):
        qlevels = levels(econ, quarters(QCPI_START, QCPI_END))
        obs = []
        for d in sorted(qlevels):
            if d <= date(2018, 1, 1):
                rt = MASS_VINTAGE          # mass-binding vintage class
            else:
                # quarterly release class: first-binding mid the month three
                # months after the quarter's first month (Q ends M+2)
                rt = add_months_first(d, 3).replace(day=15)
            obs.append({"realtime_start": rt.isoformat(),
                        "realtime_end": "2030-01-01", "date": d.isoformat(),
                        "value": f"{qlevels[d]:.6f}"})
        obs.sort(key=lambda r: (r["date"], r["realtime_start"]))
        name = "AUSCPIALLQINMEI" if econ == "AU" else "NZLCPIALLQINMEI"
        with open(os.path.join(target, "cpi", "fred_vintaged",
                               f"{name}.json"), "w") as f:
            json.dump({"realtime_start": "2018-05-15",
                       "realtime_end": "2030-01-01",
                       "observations": obs}, f)

    # ---- pinned-calendar subsets (GB / CA) --------------------------------
    gb_cal = []
    d = date(2018, 1, 1)
    while d <= date(2019, 11, 1):
        nxt = date(d.year + (1 if d.month == 12 else 0),
                   1 if d.month == 12 else d.month + 1, 13)
        gb_cal.append({"reference_period": f"{MON_FULL[d.month - 1].lower()}"
                                           f"{d.year}",
                       "class": "EVIDENCED",
                       "release_date_display":
                       f"{nxt.day} {MON_FULL[nxt.month - 1]} {nxt.year}"})
        d = date(d.year + (1 if d.month == 12 else 0),
                 1 if d.month == 12 else d.month + 1, 1)
    with open(os.path.join(target, "cpi", "calendars", "gb_cal.json"),
              "w") as f:
        json.dump(gb_cal, f)

    ca_cal = []
    d = date(2018, 3, 1)          # release in month M carries reference M-1
    while d <= date(2019, 12, 1):
        ca_cal.append({"release_date": f"{d.year}-{d.month:02d}-15",
                       "release_time_utc_display":
                           [f"{d.year}-{d.month:02d}-15T08:30"],
                       "cpi_products": ["18100004"], "class": "EVIDENCED"})
        d = date(d.year + (1 if d.month == 12 else 0),
                 1 if d.month == 12 else d.month + 1, 1)
    with open(os.path.join(target, "cpi", "calendars", "ca_cal_v3.json"),
              "w") as f:
        json.dump(ca_cal, f)

    # ---- daily spot snapshot (Twelve Data 1day format, newest-first) -----
    for pi, pair in enumerate(PAIRS):
        base = 1.10 + 0.05 * pi
        beta = 0.02 + 0.004 * pi
        rows = []
        for i, d in enumerate(days):
            usd = 0.4 * math.sin(2 * math.pi * i / 90.0 + pi)
            px = base * (1.0 + beta * usd / 100.0
                         + 0.0004 * (_lcg() - 0.5))
            rows.append({"datetime": d.isoformat(),
                         "open": f"{px * 0.9999:.6f}",
                         "high": f"{px * 1.0002:.6f}",
                         "low": f"{px * 0.9997:.6f}",
                         "close": f"{px:.6f}"})
        rows.reverse()                    # newest-first provider storage
        with open(os.path.join(target, f"{pair}.json"), "w") as f:
            json.dump({"status": "ok",
                       "meta": {"symbol": pair, "interval": "1day"},
                       "values": rows}, f)

    # ---- financing ledger (V5 format, static vintages, pre-S0) -----------
    with open(os.path.join(target, "ledger.jsonl"), "w") as f:
        for i, area in enumerate(sorted(AREAS)):
            f.write(json.dumps({
                "area": area,
                "effective_time_utc": "2018-01-01T00:00:00+00:00",
                "announcement": {"operative_available_time_utc":
                                 "2018-01-01T00:00:00+00:00"},
                "new_value": 0.25 + 0.25 * i,
            }) + "\n")

    print(json.dumps({"fixture": target, "weekdays": len(days),
                      "months": len(months(CPI_START, CPI_END)),
                      "quarters": len(quarters(QCPI_START, QCPI_END)),
                      "pairs": len(PAIRS)}))


if __name__ == "__main__":
    main(sys.argv[1])
