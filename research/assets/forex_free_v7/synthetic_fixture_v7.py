#!/usr/bin/env python3
"""Deterministic synthetic fixture for the V7 diagnostic-smoke proof.

Builds into <target_dir>:
  {PAIR}_1h_<span>_a.json     weekday 1h bars (seeded pseudo-random walk)
  {PAIR}_1day_<span>_a.json   one daily bar per weekday (the 22:00Z bar)
  clocks_v7.json              GB (DAY-precision) + CA (INSTANT) clocks
  ledger.jsonl                policy-rate vintages for all financing areas

Determinism: numpy default_rng(7); identical bytes on every run.
Span: 2021-01-04..2022-06-30 (enough history for the 20/65-day warmups,
three fold bands, and financing vintages across the whole span).
"""
import json
import math
import os
import sys
from datetime import date, datetime, timedelta, timezone

import numpy as np

UTC = timezone.utc
PAIRS = ["EURUSD", "GBPUSD", "USDJPY", "USDCAD", "AUDUSD", "NZDUSD", "USDCHF"]
START = date(2021, 1, 4)
END = date(2022, 6, 30)
HOURS = [f"{h:02d}:00:00" for h in range(23)]
AREAS = ["EMU", "US", "GB", "JP", "CA", "AU", "NZ", "CH"]


def weekdays():
    d, out = START, []
    while d <= END:
        if d.weekday() < 5:
            out.append(d)
        d += timedelta(days=1)
    return out


def main(target):
    os.makedirs(target, exist_ok=True)
    rng = np.random.default_rng(7)
    days = weekdays()

    daily = {}
    hourly = {}
    for pair in PAIRS:
        level = 1.10 + 0.05 * PAIRS.index(pair)
        dp = []
        hp = {}
        px = level
        hpx = level
        for d in days:
            # daily step
            px *= float(1 + rng.normal(0, 0.004))
            dp.append(px)
            # 24 hourly bars ending at the day's close
            drift = (px / hpx) ** (1 / 24.0)
            bars = []
            for h_i, h in enumerate(HOURS):
                hpx *= float(drift * (1 + rng.normal(0, 0.0008)))
                ts = datetime(d.year, d.month, d.day, h_i, tzinfo=UTC)
                bars.append((ts, hpx))
            hp[d] = bars
        daily[pair] = dp
        hourly[pair] = hp

    span = f"{START.isoformat()}_{END.isoformat()}"
    for pair in PAIRS:
        hrows = [{"datetime": ts.strftime("%Y-%m-%d %H:%M:%S"), "close": c}
                 for d in days for ts, c in hourly[pair][d]]
        with open(os.path.join(target, f"{pair}_1h_{span}_a.json"), "w") as f:
            json.dump({"status": "ok", "meta": {"symbol": pair, "interval": "1h"},
                       "values": hrows}, f)
        drows = [{"datetime": f"{d.isoformat()} 00:00:00", "close": c}
                 for d, c in zip(days, daily[pair])]
        with open(os.path.join(target, f"{pair}_1day_{span}_a.json"), "w") as f:
            json.dump({"status": "ok", "meta": {"symbol": pair, "interval": "1day"},
                       "values": drows}, f)

    # clocks: 12 GB (DAY 23:59:59Z) + 12 CA (INSTANT 13:35Z) spread evenly
    clocks = []
    for i, d in enumerate(days[30::30][:12]):
        clocks.append({
            "clock_id": f"SYN:GB:{d.isoformat()}:EURUSD",
            "economy": "GB",
            "nonrep_pair": "EURUSD",
            "decision_date": d.isoformat(),
            "event_available_time_utc": f"{d.isoformat()}T23:59:59Z",
            "precision_class": "DAY",
        })
    for i, d in enumerate(days[45::30][:12]):
        clocks.append({
            "clock_id": f"SYN:CA:{d.isoformat()}:GBPUSD",
            "economy": "CA",
            "nonrep_pair": "GBPUSD",
            "decision_date": d.isoformat(),
            "event_available_time_utc": f"{d.isoformat()}T13:35:00Z",
            "precision_class": "INSTANT_TRUE_UTC_V3",
        })
    with open(os.path.join(target, "clocks_v7.json"), "w") as f:
        json.dump({"schema": "forex_free_v7_conditioning_clocks_v1",
                   "clocks": clocks}, f)

    # ledger: one static vintage per area available from 2020-01-01
    with open(os.path.join(target, "ledger.jsonl"), "w") as f:
        for i, area in enumerate(AREAS):
            f.write(json.dumps({
                "area": area,
                "effective_time_utc": "2020-01-01T00:00:00+00:00",
                "announcement": {"operative_available_time_utc":
                                 "2020-01-01T00:00:00+00:00"},
                "new_value": 0.5 + 0.25 * i,
            }) + "\n")

    print(json.dumps({"fixture": target, "days": len(days),
                      "clocks": len(clocks), "pairs": len(PAIRS)}))


if __name__ == "__main__":
    main(sys.argv[1])
