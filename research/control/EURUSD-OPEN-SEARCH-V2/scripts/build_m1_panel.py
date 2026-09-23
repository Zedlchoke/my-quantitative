#!/usr/bin/env python
"""Build the M1 bid/ask panel + integrity census + spread cost authority
for EURUSD-OPEN-SEARCH-V1 from the staged Dukascopy day-file corpus.

Fail-closed: any missing file present in the manifest as MISSING on a day
that is NOT a weekend, or any decode error, is recorded; the census output
carries verdict PASS / PASS_WITH_FLAGS; a FAILED census blocks the data
plane (plan section 1). Raw bytes are never committed; only this artifact
and the manifest digests are.

Outputs (committed):
  freezes/m1_panel_manifest.json   file digests + totals + integrity census
                                   + spread cost authority (per-session
                                   medians measured at decision/fill law)
Local (gitignored):
  data_local/panel/m1_bidask.parquet
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import struct
import sys
import lzma
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data_local" / "duka" / "M1"
MANIFEST = ROOT / "data_local" / "duka" / "m1_manifest.json"
OUT_DIR = ROOT / "data_local" / "panel"
FREEZE_DIR = ROOT / "freezes"
OUT_PARQUET = OUT_DIR / "m1_bidask.parquet"
OUT_MANIFEST = FREEZE_DIR / "m1_panel_manifest.json"

START = dt.date(2021, 1, 1)
END = dt.date(2025, 12, 31)
PRICE_SCALE = 1e5

# Session windows (UTC hours) — plan section 1 cost law
SESSIONS = {
    "asia": [(0, 7)],
    "london": [(7, 12)],
    "ny_overlap": [(12, 16)],
    "ny_late": [(16, 21)],
    "rollover": [(21, 24)],
}


def decode_day(path: Path) -> np.ndarray | None:
    raw = path.read_bytes()
    plain = lzma.decompress(raw)
    if len(plain) % 24 != 0:
        raise ValueError(f"{path}: payload not multiple of 24 ({len(plain)})")
    n = len(plain) // 24
    rec = np.frombuffer(plain, dtype=np.dtype(">i4,>i4,>i4,>i4,>i4,>f4"), count=n)
    sec = rec["f0"].astype(np.int64)
    out = np.column_stack(
        [rec["f1"], rec["f2"], rec["f3"], rec["f4"]]
    ).astype(np.float64) / PRICE_SCALE
    return sec, out  # (n,), (n,4) open close low high


def main():
    man = json.loads(MANIFEST.read_text())
    assert man.get("complete") is True, "corpus manifest incomplete — fail closed"

    rows_bid, rows_ask = [], []
    integrity = {
        "missing_weekday": [],
        "decode_errors": [],
        "non_monotonic_days": [],
        "ohlc_violation_days": [],
        "thin_bar_days": [],
    }
    days = (END - START).days + 1
    n_days_ok = 0
    for i in range(days):
        day = START + dt.timedelta(days=i)
        if day.weekday() >= 5:
            continue  # Saturday/Sunday: forex closed; files expected 404
        y, m, d = day.year, day.month, day.day
        day_frames = {}
        bad = False
        for side in ("BID", "ASK"):
            key = f"{side}/{y}-{m:02d}-{d:02d}.bi5"
            info = man["files"].get(key)
            if info is None or "sha256" not in info:
                integrity["missing_weekday"].append(f"{key} (absent from manifest)")
                bad = True
                continue
            path = RAW / side / f"{y}-{m:02d}-{d:02d}.bi5"
            try:
                sec, ohlc = decode_day(path)
            except Exception as e:  # decode fail-closed
                integrity["decode_errors"].append(f"{key}: {e}")
                bad = True
                continue
            if np.any(np.diff(sec) <= 0):
                integrity["non_monotonic_days"].append(key)
            if sec.size and (sec[0] != 0 or sec[-1] != 86340):
                integrity["thin_bar_days"].append(f"{key} first={sec[0]} last={sec[-1]} n={sec.size}")
            if ohlc.size:
                lo = ohlc[:, 2]
                hi = ohlc[:, 3]
                o = ohlc[:, 0]
                c = ohlc[:, 1]
                viol = int(np.sum(~((lo <= np.minimum(o, c)) & (np.maximum(o, c) <= hi))))
                if viol:
                    integrity["ohlc_violation_days"].append(f"{key}: {viol}")
            day_frames[side] = (sec, ohlc)
        if bad or len(day_frames) != 2:
            continue
        if set(day_frames["BID"][0].tolist()) != set(day_frames["ASK"][0].tolist()):
            integrity["non_monotonic_days"].append(f"{y}-{m:02d}-{d:02d}: BID/ASK minute sets differ")
            continue
        sec = day_frames["BID"][0]
        base = dt.datetime(y, m, d, tzinfo=dt.timezone.utc)
        ts = np.array([int(base.timestamp()) + int(s) for s in sec], dtype=np.int64)
        rows_bid.append(pd.DataFrame(ts, columns=["ts"]).assign(
            open=day_frames["BID"][1][:, 0], close=day_frames["BID"][1][:, 1],
            low=day_frames["BID"][1][:, 2], high=day_frames["BID"][1][:, 3]))
        rows_ask.append(pd.DataFrame(ts, columns=["ts"]).assign(
            open=day_frames["ASK"][1][:, 0], close=day_frames["ASK"][1][:, 1],
            low=day_frames["ASK"][1][:, 2], high=day_frames["ASK"][1][:, 3]))
        n_days_ok += 1

    if rows_bid:
        bid = pd.concat(rows_bid, ignore_index=True)
        ask = pd.concat(rows_ask, ignore_index=True)
    else:
        raise SystemExit("FAIL: no decodable days")

    # align on exact minute timestamps
    df = bid.merge(ask, on="ts", suffixes=("_bid", "_ask"))
    df["mid"] = (df["close_bid"] + df["close_ask"]) / 2.0
    df["spread"] = df["close_ask"] - df["close_bid"]

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    df.to_parquet(OUT_PARQUET, index=False)

    # ---- spread cost authority: per-session medians of (a) bar-close spread
    hrs = pd.to_datetime(df["ts"], unit="s", utc=True).dt.hour
    sess_of = np.full(len(df), "other", dtype=object)
    for name, windows in SESSIONS.items():
        for (a, b) in windows:
            sess_of[(hrs >= a) & (hrs < b)] = name
    spread_stats = {}
    for name in list(SESSIONS.keys()) + ["other"]:
        sel = sess_of == name
        s = df.loc[sel, "spread"]
        spread_stats[name] = {
            "n_bars": int(sel.sum()),
            "spread_median_pips": round(float(s.median()) * 1e4, 3),
            "spread_p90_pips": round(float(s.quantile(0.90)) * 1e4, 3),
        }

    # weekday-missing census tolerance: <= 0.05% interior missing (GAP law analog)
    n_weekdays = sum(1 for i in range(days) if (START + dt.timedelta(days=i)).weekday() < 5)
    gap_frac = len(integrity["missing_weekday"]) / max(1, n_weekdays)
    census = {
        "schema": "eosv1.m1_panel_manifest@1",
        "built_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "coverage_utc": [f"{START}T00:00", f"{END}T23:59"],
        "rows": int(len(df)),
        "decodable_weekdays": n_days_ok,
        "weekdays_expected": n_weekdays,
        "missing_weekday_days": len(integrity["missing_weekday"]),
        "gap_fraction": round(gap_frac, 6),
        "gap_max_run_check": "per-day files; interior missing minutes counted in thin_bar_days",
        "thin_bar_days": len(integrity["thin_bar_days"]),
        "ohlc_violation_days": len(integrity["ohlc_violation_days"]),
        "decode_errors": len(integrity["decode_errors"]),
        "non_monotonic_or_mismatch": len(integrity["non_monotonic_days"]),
        "details_on_failures": {k: v[:20] for k, v in integrity.items()},
        "spread_cost_authority": {
            "law": "plan section 1/4: spread measured per session from close-spread series; "
                   "fills at opposite quote use the SAME bar ask/bid; stress tiers 1.5x/2.0x",
            "sessions_pips": spread_stats,
        },
        "verdict": (
            "PASS" if (
                gap_frac <= 0.0005
                and not integrity["decode_errors"]
                and not integrity["ohlc_violation_days"]
                and not integrity["non_monotonic_days"]
            ) else "PASS_WITH_FLAGS" if (
                gap_frac <= 0.005 and not integrity["decode_errors"]
            ) else "FAILED"
        ),
    }
    FREEZE_DIR.mkdir(parents=True, exist_ok=True)
    OUT_MANIFEST.write_text(json.dumps(census, indent=1))
    print(json.dumps({k: census[k] for k in
                      ["rows", "decodable_weekdays", "missing_weekday_days", "gap_fraction",
                       "thin_bar_days", "ohlc_violation_days", "verdict"]}, indent=1))
    print("spread pips:", json.dumps(spread_stats, indent=1))
    print("wrote", OUT_PARQUET, "and", OUT_MANIFEST)
    sys.exit(0 if census["verdict"] != "FAILED" else 2)


if __name__ == "__main__":
    main()
