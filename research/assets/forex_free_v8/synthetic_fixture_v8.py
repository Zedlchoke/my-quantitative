#!/usr/bin/env python3
"""Deterministic SYNTHETIC fixture for FOREX-FREE-V8 tests + diagnostic smoke.

Builds into <target_dir>:
  staged/{T10YIE,T5YIE,DGS10}.json   staged-vintaged-format series
                                     (rows: date/realtime_start/realtime_end/
                                     value; T-legs bind same-day, DGS10 binds
                                     next weekday -- the census lag classes)
  {PAIR}_1h_<span>_a.json            one H1 bar per weekday stamped exactly at
                                     16:00 America/New_York (DST-correct),
                                     forex_free_v1 provider format
  ledger.jsonl                       policy-rate vintages for all financing
                                     areas (V5 ledger format, one static
                                     vintage per area, available pre-S0)

Determinism: a fixed LCG (no numpy); identical bytes on every run.
Span: 2018-04-04..2020-07-31 (weekday grid; enough binding clocks for the
252-clock warmup + anchor trading and the 504-clock neighbour window).

The fixture drives MECHANICS tests only.  It encodes no production outcome
data and computes no PnL (booking happens only in the gated scored path).
"""
from __future__ import annotations

import json
import math
import os
import sys
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

NY_TZ = ZoneInfo("America/New_York")
UTC = timezone.utc
PAIRS = ["EURUSD", "USDJPY", "USDCAD", "AUDUSD", "NZDUSD", "USDCHF", "GBPUSD"]
AREAS = ["EMU", "US", "GB", "JP", "CA", "AU", "NZ", "CH"]
START = date(2018, 4, 4)
END = date(2020, 7, 31)

_LCG_STATE = 20260908


def _lcg() -> float:
    global _LCG_STATE
    _LCG_STATE = (1103515245 * _LCG_STATE + 12345) % (1 << 31)
    return _LCG_STATE / float(1 << 31)


def weekdays():
    d, out = START, []
    while d <= END:
        if d.weekday() < 5:
            out.append(d)
        d += timedelta(days=1)
    return out


def next_weekday(d: date) -> date:
    d += timedelta(days=1)
    while d.weekday() >= 5:
        d += timedelta(days=1)
    return d


def staged_rows(obs, value_fn, rt_fn):
    rows = []
    for i, d in enumerate(obs):
        rows.append({"date": d.isoformat(),
                     "realtime_start": rt_fn(i, d).isoformat(),
                     "realtime_end": "2030-01-01",
                     "value": f"{value_fn(i):.4f}"})
    return rows


def main(target):
    days = weekdays()
    os.makedirs(os.path.join(target, "staged"), exist_ok=True)
    # pre-S0 observations (bound at the fixture's vintage-window start) so the
    # first grid clock already carries a current observation
    pre = [date(2018, 4, 2), date(2018, 4, 3)]
    obs = pre + days

    def rt_same(i, d):
        return date(2018, 1, 2) if i < len(pre) else d

    def rt_next(i, d):
        return date(2018, 1, 2) if i < len(pre) else next_weekday(d)

    t10 = [2.00 + 0.50 * math.sin(2 * math.pi * i / 120.0)
           for i in range(len(obs))]
    t5 = [1.50 + 0.20 * math.sin(2 * math.pi * i / 120.0 + 1.0)
          for i in range(len(obs))]
    dgs = [2.40 + 0.30 * math.sin(2 * math.pi * i / 200.0)
           for i in range(len(obs))]

    for name, vals, rt in (("T10YIE", t10, rt_same), ("T5YIE", t5, rt_same),
                           ("DGS10", dgs, rt_next)):
        with open(os.path.join(target, "staged", f"{name}.json"), "w") as f:
            json.dump(staged_rows(obs, lambda i, v=vals: v[i], rt), f)

    # H1 snapshot: one bar per weekday at exactly 16:00 America/New_York
    span = f"{START.isoformat()}_{END.isoformat()}"
    for pi, pair in enumerate(PAIRS):
        base = 1.10 + 0.05 * pi
        beta = 0.02 + 0.004 * pi        # signed USD sensitivity varies by pair
        rows = []
        px = base
        for i, d in enumerate(days):
            usd = 0.4 * math.sin(2 * math.pi * i / 90.0 + pi)
            px = base * (1.0 + beta * usd / 100.0
                         + 0.0004 * (_lcg() - 0.5))
            ts = datetime(d.year, d.month, d.day, 16, 0,
                          tzinfo=NY_TZ).astimezone(UTC)
            rows.append({"datetime": ts.strftime("%Y-%m-%d %H:%M:%S"),
                         "close": round(px, 6)})
        with open(os.path.join(target, f"{pair}_1h_{span}_a.json"), "w") as f:
            json.dump({"status": "ok",
                       "meta": {"symbol": pair.replace("/", ""), "interval": "1h"},
                       "values": rows}, f)

    # financing ledger (V5 format): one static vintage per area, pre-S0
    with open(os.path.join(target, "ledger.jsonl"), "w") as f:
        for i, area in enumerate(AREAS):
            f.write(json.dumps({
                "area": area,
                "effective_time_utc": "2018-01-01T00:00:00+00:00",
                "announcement": {"operative_available_time_utc":
                                 "2018-01-01T00:00:00+00:00"},
                "new_value": 0.25 + 0.25 * i,
            }) + "\n")

    print(json.dumps({"fixture": target, "weekdays": len(days),
                      "obs": len(obs), "pairs": len(PAIRS)}))


if __name__ == "__main__":
    main(sys.argv[1])
