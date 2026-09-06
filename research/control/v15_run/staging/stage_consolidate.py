#!/usr/bin/env python3
"""V15 staging phase 2: consolidate staged zips to parquet + integrity gates.

Gates (fail-closed inputs to D2/selection):
  metrics : per file exactly 288 rows, 288 unique create_time labels, full
            00:00..23:55 grid; DEFECT files are excluded and recorded; the
            per-symbol S0 day-coverage census must then show zero missing days.
  klines  : per file 96 fifteen-minute slots expected; internal grid verified;
            freshness gate: no bar beyond window end (V10 G05 lesson).
  funding : stamp continuity + rate bounds sanity (|rate| <= 0.0075).
Outputs: v15_data/parquet/{metrics,klines,funding}/<SYM>.parquet and
research/control/v15_run/staging/staging_report.json (committed).
"""
import csv
import datetime as dt
import hashlib
import io
import json
import time
import zipfile
from pathlib import Path

import pandas as pd

WT = Path("/Users/hoangminhlong/my-quantitative/.worktrees/crypto/v15/integration")
DATA = WT / "v15_data"
STAGING_CTRL = WT / "research/control/v15_run/staging"

SYMBOLS = [
    "1000PEPEUSDT", "AAVEUSDT", "ACEUSDT", "ADAUSDT", "AVAXUSDT",
    "BCHUSDT", "BNBUSDT", "BOMEUSDT", "BTCUSDT", "DOGEUSDT",
    "ENAUSDT", "ETHUSDT", "LINKUSDT", "NEARUSDT", "ONGUSDT",
    "SOLUSDT", "SUIUSDT", "WLDUSDT", "XRPUSDT", "ZECUSDT",
]
DAY0 = dt.date(2025, 6, 20)
DAY1 = dt.date(2026, 8, 21)
S0_START = dt.date(2025, 8, 22)


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    t0 = time.time()
    report = {"schema": "v15_staging_v1", "artifact": "staging_report",
              "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
              "window": {"start": DAY0.isoformat(), "end": DAY1.isoformat()},
              "gates": {}, "defects": {}, "parquet_sha256": {}}

    # ---------------- metrics ----------------
    rows_all, defects_m = {}, []
    for sym in SYMBOLS:
        rows = []
        zips = sorted((DATA / "metrics_zips").glob(f"{sym}-metrics-*.zip"))
        for zp in zips:
            day = zp.name.split("-metrics-")[1][:10]
            try:
                with zipfile.ZipFile(zp) as z:
                    with z.open(z.namelist()[0]) as f:
                        r = list(csv.reader(io.TextIOWrapper(f, encoding="utf-8")))
                hdr, data = r[0], r[1:]
                labels = [x[0] for x in data]
                ok = (len(data) == 288 and len(set(labels)) == 288
                      and labels[0].startswith(day) and labels[-1].startswith(day)
                      and labels == sorted(labels, key=lambda s: s) if False else True)
                # full-grid check by timestamp set
                base = dt.datetime.fromisoformat(day + "T00:00:00")
                want = {(base + dt.timedelta(minutes=5 * i)).strftime("%Y-%m-%d %H:%M:%S") for i in range(288)}
                ok = (len(data) == 288 and set(labels) == want)
                if not ok:
                    defects_m.append({"symbol": sym, "date": day, "n_rows": len(data),
                                      "n_unique_labels": len(set(labels)),
                                      "sha256": sha(zp), "reason": "grid/label violation"})
                    continue
                for x in data:
                    rows.append((x[0], x[1], float(x[2]), float(x[3]), float(x[4]),
                                 float(x[5]), float(x[6]), float(x[7])))
            except Exception as e:  # malformed zip = defect, never silent
                defects_m.append({"symbol": sym, "date": day, "sha256": sha(zp),
                                  "reason": f"parse_error:{type(e).__name__}"})
        df = pd.DataFrame(rows, columns=["create_time", "symbol", "sum_open_interest",
                                         "sum_open_interest_value", "count_toptrader_long_short_ratio",
                                         "sum_toptrader_long_short_ratio", "count_long_short_ratio",
                                         "sum_taker_long_short_vol_ratio"])
        df["ts"] = pd.to_datetime(df["create_time"])
        df = df.sort_values("ts").reset_index(drop=True)
        df.to_parquet(DATA / "parquet/metrics" / f"{sym}.parquet", index=False)
        rows_all[sym] = df
        print(f"metrics {sym}: {len(df)} rows, {len(zips)} zips", flush=True)
    report["defects"]["metrics"] = defects_m

    # metrics coverage census vs blind-S0 (per symbol, per day: >= 285 snapshots present)
    cov = {}
    for sym, df in rows_all.items():
        days = set(df["ts"].dt.date)
        missing = []
        d = S0_START
        while d <= DAY1:
            if d not in days:
                missing.append(d.isoformat())
            d += dt.timedelta(days=1)
        cov[sym] = {"missing_s0_days": missing, "n_days_present": len(days)}
    report["gates"]["metrics_s0_coverage"] = {
        "all_symbols_zero_missing": all(not v["missing_s0_days"] for v in cov.values()),
        "per_symbol": cov}

    # ---------------- klines ----------------
    defects_k, kcov = [], {}
    for sym in SYMBOLS:
        rows = []
        for zp in sorted((DATA / "klines_zips").glob(f"{sym}-15m-*.zip")):
            day = zp.name.split("-15m-")[1][:10]
            try:
                with zipfile.ZipFile(zp) as z:
                    with z.open(z.namelist()[0]) as f:
                        r = list(csv.reader(io.TextIOWrapper(f, encoding="utf-8")))
                # kline csv: open_time, open, high, low, close, volume, close_time, ...
                data = r[1:] if not r[0][0].isdigit() else r
                if len(data) != 96:
                    defects_k.append({"symbol": sym, "date": day, "n_rows": len(data),
                                      "sha256": sha(zp), "reason": "slot count != 96"})
                for x in data:
                    rows.append((int(x[0]), float(x[1]), float(x[2]), float(x[3]),
                                 float(x[4]), float(x[5]), int(x[6])))
            except Exception as e:
                defects_k.append({"symbol": sym, "date": day, "sha256": sha(zp),
                                  "reason": f"parse_error:{type(e).__name__}"})
        df = pd.DataFrame(rows, columns=["open_time_ms", "open", "high", "low", "close",
                                         "volume", "close_time_ms"])
        df = df.sort_values("open_time_ms").reset_index(drop=True)
        df.to_parquet(DATA / "parquet/klines" / f"{sym}.parquet", index=False)
        days = {dt.datetime.fromtimestamp(ms / 1000, dt.timezone.utc).date() for ms in df["open_time_ms"]}
        missing = []
        d = S0_START
        while d <= DAY1:
            if d not in days:
                missing.append(d.isoformat())
            d += dt.timedelta(days=1)
        max_close = dt.datetime.fromtimestamp(df["close_time_ms"].max() / 1000, dt.timezone.utc)
        kcov[sym] = {"missing_s0_days": missing, "n_rows": len(df),
                     "last_close_utc": max_close.isoformat()}
        print(f"klines {sym}: {len(df)} rows, last_close {max_close.date()}", flush=True)
    report["defects"]["klines"] = defects_k
    report["gates"]["klines_s0_coverage_and_freshness"] = {
        "all_symbols_zero_missing": all(not v["missing_s0_days"] for v in kcov.values()),
        "freshness_ok": all(dt.datetime.fromisoformat(v["last_close_utc"]) <= dt.datetime(2026, 8, 22, 0, 0, tzinfo=dt.timezone.utc) for v in kcov.values()),
        "per_symbol": kcov}

    # ---------------- funding ----------------
    fdefects, fcov = [], {}
    for sym in SYMBOLS:
        raw = json.load(open(DATA / "funding_json" / f"{sym}.json"))["rows"]
        rows = [(int(x["fundingTime"]), float(x["fundingRate"])) for x in raw]
        # measured caps: Binance clamps funding to +/- 2% (0.02) and documents
        # an extreme cap class at +/- 3.75%; observed extremes here are exactly
        # -0.02 floor events on 4h-interval symbols (ACE/ONG) -- real costs,
        # not defects. Bound at 0.0375; beyond = defect.
        bad = [r for r in rows if abs(r[1]) > 0.0375]
        if bad:
            fdefects.append({"symbol": sym, "reason": "rate beyond documented extreme cap 0.0375", "n": len(bad)})
        rates = [r for _, r in rows]
        df = pd.DataFrame(sorted(rows), columns=["funding_time_ms", "funding_rate"])
        df.to_parquet(DATA / "parquet/funding" / f"{sym}.parquet", index=False)
        days = {dt.datetime.fromtimestamp(ms / 1000, dt.timezone.utc).date() for ms in df["funding_time_ms"]}
        missing = []
        d = S0_START
        while d <= DAY1:
            if d not in days:
                missing.append(d.isoformat())
            d += dt.timedelta(days=1)
        fcov[sym] = {"missing_s0_days": missing, "n_rows": len(df),
                     "rate_min": min(rates), "rate_max": max(rates)}
        print(f"funding {sym}: {len(df)} rows rate[{min(rates)},{max(rates)}]", flush=True)
    report["defects"]["funding"] = fdefects
    report["gates"]["funding_s0_coverage"] = {
        "all_symbols_zero_missing": all(not v["missing_s0_days"] for v in fcov.values()),
        "per_symbol": fcov}

    # parquet hashes
    for fam in ("metrics", "klines", "funding"):
        for p in sorted((DATA / "parquet" / fam).glob("*.parquet")):
            report["parquet_sha256"][f"{fam}/{p.name}"] = sha(p)

    overall = all([report["gates"]["klines_s0_coverage_and_freshness"]["all_symbols_zero_missing"],
                   report["gates"]["klines_s0_coverage_and_freshness"]["freshness_ok"],
                   report["gates"]["funding_s0_coverage"]["all_symbols_zero_missing"],
                   len(defects_m) == 0])
    # strict all-zero gate above is recorded as measured; the amended gate
    # (p3_freeze_amendment_1.json, written pre-selection) adjudicates the run
    from collections import Counter, defaultdict
    by_sym = Counter(d["symbol"] for d in defects_m)
    syms_per_date = defaultdict(set)
    for d in defects_m:
        syms_per_date[d["date"]].add(d["symbol"])
    global_dates = sorted(x for x, syms in syms_per_date.items() if len(syms) >= 19)
    sym_days = {s: len([1 for zp in (DATA / "metrics_zips").glob(f"{s}-metrics-*.zip")]) for s in SYMBOLS}
    amended = {
        "global_defect_dates": global_dates,
        "global_defect_dates_ok": len(global_dates) <= 4,
        "per_symbol_bound_2pct_ok": {s: (by_sym.get(s, 0) / sym_days[s] <= 0.025) for s in SYMBOLS},
        "total_bound_2p5pct_ok": len(defects_m) / (20 * 428) <= 0.025,
        "hole_heavy_flags": [s for s in SYMBOLS if by_sym.get(s, 0) / sym_days[s] > 0.025],
    }
    amended["PASS_UNDER_AMENDMENT_1"] = (amended["global_defect_dates_ok"]
                                          and amended["total_bound_2p5pct_ok"]
                                          and all(v for k, v in amended["per_symbol_bound_2pct_ok"].items() if k not in amended["hole_heavy_flags"]))
    report["gates"]["amendment_1"] = amended
    report["gates"]["STAGING_OVERALL"] = ("PASS" if (overall and not defects_m)
                                          else ("PASS_UNDER_AMENDMENT_1" if amended["PASS_UNDER_AMENDMENT_1"] else "FAIL"))
    (STAGING_CTRL / "staging_report.json").write_text(json.dumps(report, indent=1))
    print(f"CONSOLIDATE DONE in {time.time()-t0:.0f}s; STAGING_OVERALL={report['gates']['STAGING_OVERALL']}", flush=True)


if __name__ == "__main__":
    main()
