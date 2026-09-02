"""D2-A9-F field-existence + OI coverage audit (read-only).

Reads the staged snapshot and funding data READ-ONLY; writes nothing outside
research/audits/v11p/a9f_scratch/.
"""
from __future__ import annotations

import json
import statistics
from pathlib import Path

import pyarrow.parquet as pq

CATALOG = Path("/Users/hoangminhlong/my-quantitative/catalog_live_crypto")
FUNDING_DIRS = {
    "20240820_20260821": Path("/Users/hoangminhlong/my-quantitative/funding_data/20240820_20260821"),
    "scan_2026": Path("/Users/hoangminhlong/my-quantitative/funding_data/scan_2026"),
}
DAY_NS = 86_400_000_000_000
BAR_NS = 900_000_000_000
PRICE_SCALE = 10**16

out: dict = {"catalog_files": sorted(str(p.relative_to(CATALOG)) for p in CATALOG.rglob("*") if p.is_file())}

bar_dirs = sorted((CATALOG / "data" / "binance_bar").iterdir())
perp_dirs = sorted((CATALOG / "data" / "crypto_perpetual").iterdir())

bars: dict[str, dict] = {}
for d in bar_dirs:
    sym = d.name.split("-15-MINUTE")[0]
    files = sorted(d.rglob("*.parquet"))
    t = pq.read_table([str(f) for f in files])
    ts = t.column("ts_event").to_pylist()
    vol = t.column("volume").to_pylist()
    qv = t.column("quote_volume").to_pylist()
    close = t.column("close").to_pylist()
    vol_f = [int.from_bytes(v, "little", signed=True) / PRICE_SCALE for v in vol]
    close_f = [int.from_bytes(c, "little", signed=True) / PRICE_SCALE for c in close]
    n = len(ts)
    first, last = min(ts), max(ts)
    expected = (last - first) // BAR_NS + 1
    missing = expected - n
    # gap census at bar cadence
    gaps = []
    prev = None
    for x in ts:
        if prev is not None and x - prev > BAR_NS:
            gaps.append({"from": prev, "to": x, "missing_bars": (x - prev) // BAR_NS - 1})
        prev = x
    zero_vol = sum(1 for v in vol_f if v <= 0)
    # window cut: bars up to 2026-08-21T00:00Z
    cut = 1787270400 * 10**9  # 2026-08-21T00:00:00Z epoch s -> ns (verified)
    n_in_window = sum(1 for x in ts if x <= cut)
    days = {}
    for x, v in zip(ts, qv):
        day = x // DAY_NS
        days[day] = days.get(day, 0.0) + float(v)
    zero_vol_days = sum(1 for v in days.values() if v <= 0)
    # last bar before cut staleness
    before = [x for x in ts if x <= cut]
    last_before_cut = max(before) if before else None
    bars[sym] = {
        "rows": n,
        "first_ts_ns": first,
        "last_ts_ns": last,
        "first_iso": _iso(first) if False else None,
        "expected_slots": expected,
        "missing_bars_internal": missing,
        "gap_count": len(gaps),
        "gaps_over_1h": [g for g in gaps if g["missing_bars"] >= 4][:10],
        "zero_volume_bars": zero_vol,
        "zero_dollar_volume_days": zero_vol_days,
        "rows_through_2026_08_21": n_in_window,
        "last_bar_through_cut_ns": last_before_cut,
        "stale_bars_at_cut": (cut - last_before_cut) // BAR_NS if last_before_cut else None,
    }

instrument: dict[str, dict] = {}
for d in perp_dirs:
    files = sorted(d.rglob("*.parquet"))
    t = pq.read_table([str(f) for f in files])
    row = t.to_pylist()[0]
    info = json.loads(row["info"])
    instrument[row["id"]] = {
        "rows": t.num_rows,
        "price_increment": row["price_increment"],
        "size_increment": row["size_increment"],
        "taker_fee": row["taker_fee"],
        "maker_fee": row["maker_fee"],
        "min_notional": row["min_notional"],
        "onboard_date_ms": info.get("onboardDate"),
        "status": info.get("status"),
        "tick_size_from_filter": next(
            (f.get("tickSize") for f in info.get("filters", []) if f.get("filterType") == "PRICE_FILTER"),
            None,
        ),
        "ts_event_ns": row["ts_event"],
        "ts_init_ns": row["ts_init"],
    }

funding: dict[str, dict] = {}
for label, root in FUNDING_DIRS.items():
    per = {}
    for d in sorted(root.iterdir()):
        if not d.is_dir():
            continue
        fp = d / "funding.json"
        if not fp.exists():
            continue
        j = json.load(open(fp))
        rows = j["rows"]
        times = sorted(int(r["fundingTime"]) for r in rows)
        marks = sum(1 for r in rows if r.get("markPrice") not in (None, ""))
        ivs = [(b - a) / 3_600_000.0 for a, b in zip(times, times[1:])]
        per[d.name] = {
            "rows": len(rows),
            "captured_at": j.get("captured_at"),
            "requested_start_ms": j.get("requested_start_ms"),
            "requested_end_ms": j.get("requested_end_ms"),
            "first_funding_ms": times[0] if times else None,
            "last_funding_ms": times[-1] if times else None,
            "mark_price_present_rows": marks,
            "median_interval_h": statistics.median(ivs) if ivs else None,
            "max_gap_h": max(ivs) if ivs else None,
            "gaps_over_12h": sum(1 for v in ivs if v > 12.0),
        }
    funding[label] = per

# OI census: any file with open-interest-like schema anywhere in catalog
oi_census: dict[str, str] = {}
for f in CATALOG.rglob("*.parquet"):
    t = pq.ParquetFile(str(f))
    cols = set(t.schema_arrow.names)
    if any("open_interest" in c.lower() or c.lower() == "oi" for c in cols):
        oi_census[str(f)] = "HAS_OI"
    elif "open" in cols and "close" in cols:
        oi_census[str(f)] = "ohlcv_bar"
    elif "price_increment" in cols:
        oi_census[str(f)] = "instrument_def_static"
    else:
        oi_census[str(f)] = "other:" + ",".join(sorted(cols))[:80]

out["bars"] = bars
out["instrument_defs"] = instrument
out["funding"] = funding
out["oi_census"] = oi_census

import sys

json.dump(out, open(sys.argv[1], "w"), indent=1, default=str)
print("symbols bar:", len(bars), "instrument:", len(instrument))
print("funding scan symbols:", len(funding["scan_2026"]), "2024 dir:", len(funding["20240820_20260821"]))
print("oi files:", {v: sum(1 for x in oi_census.values() if x == v) for v in set(oi_census.values())})
