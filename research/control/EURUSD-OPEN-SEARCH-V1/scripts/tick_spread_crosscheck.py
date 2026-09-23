#!/usr/bin/env python
"""A1 bounded tick cross-check, day 2: tick-derived spread vs candle-derived
spread, on a low-liquidity Asia hour, a London hour and the NY-overlap hour
of 2022-08-15 (Monday), plus timestamp continuity.

Completes amendment A1's "≤2-day tick probe" requirement jointly with
probe_decode_20240304.py (layout + close/bracket, 2024-03-04).
Fail-closed on mismatch.
"""
import datetime as dt
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import duka_lib as dk

OUT = Path(__file__).resolve().parent.parent / "data_local" / "probe"
DAY = (2022, 8, 15)
HOURS = (3, 9, 14)  # asia / london / ny-overlap

ev = {"schema": "eosv1.tick_spread_crosscheck@1",
      "measured_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
      "day": DAY, "hours": HOURS, "sha256": {}, "checks": {}, "verdict": None}

y, m, d = DAY
bid_c = {r["sec"]: r for r in dk.decode_min_candles(dk.fetch_bytes(dk.candle_url(y, m, d, "BID")))}
ask_c = {r["sec"]: r for r in dk.decode_min_candles(dk.fetch_bytes(dk.candle_url(y, m, d, "ASK")))}

per_hour = {}
mismatch = 0
compared = 0
ts_cont_viol = 0
for h in HOURS:
    raw = dk.fetch_bytes(dk.tick_url(y, m, d, h))
    ev["sha256"][f"ticks_{h}h"] = hashlib.sha256(raw).hexdigest() if raw else None
    if raw is None:
        ev["checks"][f"h{h}"] = "TICK_404"
        continue
    by_min = {}
    last_ms = -1
    for ms, a, b, av, bv in dk.decode_ticks(raw):
        if ms <= last_ms:
            ts_cont_viol += 1
        last_ms = ms
        sec_min = h * 3600 + (ms // 1000) // 60 * 60
        by_min.setdefault(sec_min, []).append((ms, b, a))
    h_mismatch = 0
    h_comp = 0
    for sec_min, ticks in sorted(by_min.items()):
        cb, ca = bid_c.get(sec_min), ask_c.get(sec_min)
        if cb is None or ca is None:
            continue
        last = max(ticks)  # by (ms, bid, ask)
        tick_bid = last[1]
        tick_ask = last[2]
        candle_bid_close = cb["close"]
        candle_ask_close = ca["close"]
        tol = 10 * 1e-5 * 0.1  # 0.1 pip on 1e-5 scale = 1e-6... keep 1 point tolerance
        tol = 1.0 / dk.PRICE_SCALE * 1.0  # 1 point
        if abs(tick_bid - candle_bid_close) > tol or abs(tick_ask - candle_ask_close) > tol:
            h_mismatch += 1
        h_comp += 1
    mismatch += h_mismatch
    compared += h_comp
    per_hour[f"h{h}"] = {"minutes_in_file": len(by_min), "compared": h_comp, "mismatch": h_mismatch}

ev["checks"]["timestamp_continuity"] = {"violations": ts_cont_viol,
                                        "result": "PASS" if ts_cont_viol == 0 else "FAIL"}
ev["checks"]["close_last_tick_vs_candle"] = {
    "compared": compared, "mismatch": mismatch,
    "result": "PASS" if compared >= 100 and mismatch == 0 else "FAIL"}

# spread consistency: median |tick_spread - candle_spread| over compared minutes
# (recompute jointly; needs both sides matched — reuse loop data)
tick_spreads, candle_spreads = [], []
for h in HOURS:
    raw_bytes_path = OUT / f"ticks_{DAY[0]}{DAY[1]:02d}{DAY[2]:02d}_{h}h.bi5"
    raw = dk.fetch_bytes(dk.tick_url(y, m, d, h))
    if raw is None:
        continue
    by_min = {}
    for ms, a, b, av, bv in dk.decode_ticks(raw):
        sec_min = h * 3600 + (ms // 1000) // 60 * 60
        by_min.setdefault(sec_min, []).append((ms, b, a))
    for sec_min, ticks in sorted(by_min.items()):
        cb, ca = bid_c.get(sec_min), ask_c.get(sec_min)
        if cb is None or ca is None:
            continue
        last = max(ticks)
        tick_spreads.append(last[2] - last[1])
        candle_spreads.append(ca["close"] - cb["close"])

if tick_spreads:
    dt_spread = np.abs(np.array(tick_spreads) - np.array(candle_spreads))
    ev["checks"]["spread_agreement"] = {
        "n": int(len(dt_spread)),
        "median_abs_diff_pips": round(float(np.median(dt_spread)) * 1e4, 3),
        "p95_abs_diff_pips": round(float(np.quantile(dt_spread, 0.95)) * 1e4, 3),
        "corr": round(float(np.corrcoef(tick_spreads, candle_spreads)[0, 1]), 6),
        "result": "PASS" if np.corrcoef(tick_spreads, candle_spreads)[0, 1] > 0.95 else "FAIL",
    }

verdicts = [c.get("result") if isinstance(c, dict) else c for c in ev["checks"].values()]
ev["verdict"] = "CROSSCHECK_PASS" if all(v == "PASS" for v in verdicts) else "CROSSCHECK_FAIL"
(OUT / "tick_spread_crosscheck_evidence.json").write_text(json.dumps(ev, indent=1))
print(json.dumps(ev["checks"], indent=1))
print("VERDICT:", ev["verdict"])
sys.exit(0 if ev["verdict"] == "CROSSCHECK_PASS" else 2)
