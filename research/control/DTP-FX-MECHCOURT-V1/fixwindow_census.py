#!/usr/bin/env python
"""fixwindow_census.py — DTP-FX-MECHCOURT-V1 Lane D preregistered fix-window spread census.

Preregistration: plans/PLAN_dtp_fx_mechcourt_v1.md section 6 (verbatim), frozen
BEFORE this script was run. This script computes ONLY the open-spread cost
quantity s_open (= a_open - b_open at bar open) in pips, bucketed by:

  * London-local hour of bar open (Europe/London via stdlib zoneinfo; BST/GMT
    handled by the tz database) in {13,14,15,16,17},
  * day-set in {ME1, ME2, MID}:
      - ME1  = last trading day of each month, per pair, per corpus
               (the last calendar day having ANY bar of that month),
      - ME2  = last TWO trading days of each month (same definition),
      - MID  = control days 13,14,15,16 of each month,
  * plus one reference bucket per pair: rollover = bars opening 21:00-21:59 UTC
    (all days),
  * plus the FIXCERT-fill-hour composite per pair:
      - entry F-1h window: bars opening London 14:00-15:59 on ME1/ME2 days,
      - exit at fix instant: the 16:00-London bar-open on ME1/ME2 days.

Statistics per bucket: n, p25, p50, p75, p90, p99 of s_open (pips) and the
count of s_open <= 0. NOTHING else: no prices, no returns, no premiums, no PnL.

Self-contained, deterministic (quantiles via fixed linear-interpolation
definition, sorted values), no network. Reads the three bars15.parquet inputs
read-only. Percentile convention: numpy-default 'linear'
  q-th: h = (n-1)*q; result = v[floor(h)] + (h-floor(h))*(v[floor(h)+1]-v[floor(h)])
on the sorted sample (documented in `notes` so A7 can recompute exactly).

Output: fixwindow_spread_census.json (schema dtpfx1/fixwindow_spread_census@1).
"""

import hashlib
import json
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import pandas as pd
from pyarrow import parquet as pq

SCHEMA = "dtpfx1/fixwindow_spread_census@1"
LONDON = ZoneInfo("Europe/London")

INPUTS = {
    "EURUSD": "/Users/hoangminhlong/my-quantitative/.worktrees/fx-rangefade-2m-shadow-v1/research/control/FX-RANGEFADE-2M-SHADOW-V1/data_local/EURUSD/derived/bars15.parquet",
    "GBPUSD": "/Users/hoangminhlong/my-quantitative/.worktrees/fx-majors-search-v1/integration/research/control/FX-MAJORS-SEARCH-V1/data_local/GBPUSD/derived/bars15.parquet",
    "USDJPY": "/Users/hoangminhlong/my-quantitative/.worktrees/fx-majors-search-v1/integration/research/control/FX-MAJORS-SEARCH-V1/data_local/USDJPY/derived/bars15.parquet",
}
PIP = {"EURUSD": 1e-4, "GBPUSD": 1e-4, "USDJPY": 1e-2}
HOURS = [13, 14, 15, 16, 17]
DAYSETS = ["ME1", "ME2", "MID"]
QUANTILES = [(0.25, "p25"), (0.50, "p50"), (0.75, "p75"), (0.90, "p90"), (0.99, "p99")]


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def pct(sorted_vals, q: float) -> float:
    """Linear-interpolation percentile (numpy default 'linear'), on sorted input."""
    n = len(sorted_vals)
    if n == 0:
        return None
    if n == 1:
        return float(sorted_vals[0])
    h = (n - 1) * q
    lo = int(h // 1)
    hi = min(lo + 1, n - 1)
    frac = h - lo
    return float(sorted_vals[lo] + frac * (sorted_vals[hi] - sorted_vals[lo]))


def stats(values):
    """Exactly the preregistered statistic set: n, p25, p50, p75, p90, p99, n_nonpos."""
    v = sorted(values)
    n = len(v)
    if n == 0:
        return {"n": 0, "p25": None, "p50": None, "p75": None,
                "p90": None, "p99": None, "n_nonpos": 0}
    out = {"n": n}
    for q, name in QUANTILES:
        out[name] = round(pct(v, q), 4)
    out["n_nonpos"] = sum(1 for x in v if x <= 0)
    return out


def daysets_for_frame(df: pd.DataFrame):
    """Per-pair per-corpus day-sets.

    Returns (me1, me2, mid) as sets of datetime.date, plus month coverage.
    Trading day = calendar day having ANY bar of that month in the corpus.
    """
    d = df["ts"].dt.tz_convert(LONDON)
    days = d.dt.date
    months = pd.MultiIndex.from_arrays([d.dt.year, d.dt.month])
    day_to_month = {}
    me1, me2 = set(), set()
    mid = set(days[(d.dt.day >= 13) & (d.dt.day <= 16)].unique())
    # group trading days by (year, month)
    by_month = {}
    for day, (y, m) in zip(days, months):
        by_month.setdefault((y, m), set()).add(day)
    n_months = 0
    for (y, m), dset in by_month.items():
        ordered = sorted(dset)
        n_months += 1
        me1.add(ordered[-1])
        me2.update(ordered[-2:])
    return me1, me2, mid, n_months


def main():
    generated_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    buckets = {}
    inputs_meta = []
    dayset_coverage = {}

    for pair, path in INPUTS.items():
        pf = pq.ParquetFile(path)
        df = pq.read_table(path).to_pandas()
        rows = len(df)
        first_ts = str(df["ts"].iloc[0])
        last_ts = str(df["ts"].iloc[-1])
        inputs_meta.append({
            "pair": pair, "path": path, "sha256": sha256_file(path),
            "rows": int(rows), "first_ts": first_ts, "last_ts": last_ts,
            "columns": [f.name for f in pf.schema_arrow],
        })

        s_pips = (df["s_open"] / PIP[pair]).to_numpy()
        loc = df["ts"].dt.tz_convert(LONDON)
        loc_hour = loc.dt.hour.to_numpy()
        loc_day = loc.dt.date.to_numpy()
        utc_hour = df["ts"].dt.hour.to_numpy()

        me1, me2, mid, n_months = daysets_for_frame(df)
        dayset_coverage[pair] = {
            "months_covered": int(n_months),
            "ME1_days": len(me1), "ME2_days": len(me2), "MID_days": len(mid),
        }

        pb = {}
        for h in HOURS:
            hb = {}
            for ds_name, ds in (("ME1", me1), ("ME2", me2), ("MID", mid)):
                mask = (loc_hour == h) & pd.Series(
                    [d in ds for d in loc_day])
                hb[ds_name] = stats(s_pips[mask.to_numpy()])
            pb[f"h{h:02d}"] = hb

        # reference bucket: rollover 21:00-21:59 UTC, all days
        pb["rollover_21_22UTC"] = stats(s_pips[utc_hour == 21])

        # FIXCERT fill-hour composite (ME1/ME2 days only)
        me_days = me1 | me2
        mask_me = pd.Series([d in me_days for d in loc_day]).to_numpy()
        entry = mask_me & (loc_hour >= 14) & (loc_hour <= 15)
        exitfix = mask_me & (loc_hour == 16)
        pb["fixcert"] = {
            "entry_F-1h_london14_15_ME1ME2": {
                "n": stats(s_pips[entry])["n"],
                "p50": stats(s_pips[entry])["p50"],
                "p90": stats(s_pips[entry])["p90"],
                "n_nonpos": stats(s_pips[entry])["n_nonpos"],
            },
            "exit_fix_16london_ME1ME2": stats(s_pips[exitfix]),
        }
        buckets[pair] = pb

    out = {
        "schema": SCHEMA,
        "generated_utc": generated_utc,
        "labels": [
            "SINGLE_SOURCE_PANEL",
            "PAPER_TIER",
            "FILL_QUALITY_UNMEASURABLE_ON_M1_BIDASK",
        ],
        "inputs": inputs_meta,
        "dayset_coverage": dayset_coverage,
        "buckets": buckets,
        "notes": [
            "Quantity: s_open = a_open - b_open at 15m bar open, converted to pips "
            "(EURUSD/GBPUSD pip=0.0001, USDJPY pip=0.01). No prices, returns, "
            "premiums or PnL computed anywhere in this census.",
            "Timestamps are UTC (parquet ts, tz=UTC); London hour is the bar-open "
            "instant converted to Europe/London via stdlib zoneinfo (BST/GMT "
            "handled by the tz database, correct across all DST transitions "
            "2021-2026 in-corpus).",
            "Day-sets per pair per corpus: trading day = calendar day with ANY bar "
            "of that month; ME1 = last such day of month, ME2 = last two, "
            "MID = days 13-16 of each month (calendar, not re-based on bars).",
            "Percentile convention: linear interpolation on the sorted sample "
            "(numpy default 'linear'): h=(n-1)q; "
            "v = v[floor(h)] + (h-floor(h))*(v[floor(h)+1]-v[floor(h)]). "
            "Values reported in pips rounded to 4 decimals.",
            "n_nonpos = count of s_open <= 0 in the bucket (non-positive spread).",
            "rollover_21_22UTC = bars opening 21:00-21:59 UTC, all days "
            "(reference bucket per plan section 6).",
            "fixcert composite per pair: entry_F-1h = bars opening London 14:00-"
            "15:59 on ME1|ME2 days; exit_fix = bars opening 16:00 London on "
            "ME1|ME2 days. Cost law: spread per DISTRIBUTION OF FILL x k in "
            "{1.0,1.5,2.0}; commission/slippage remain DECLARED_UNMEASURED.",
            "Verdict-law note (plan section 6): this census measures the "
            "fix-window/month-end cost bucket that FIXCERT was killed against "
            "via session-bucket proxies; it sharpens the owner packet and does "
            "NOT rescue mechanism A (kill is ancestry/class + frontier, not "
            "cost-only).",
            "Sources are Dukascopy M1 bid/ask derived 15m bars (single-source "
            "panel, paper tier): EURUSD from FX-RANGEFADE-2M-SHADOW-V1 shadow "
            "worktree, GBPUSD/USDJPY from FX-MAJORS-SEARCH-V1 worktree "
            "(read-only public data). Fill quality on M1 bid/ask is "
            "unmeasurable: no volume/depth/tape.",
        ],
    }

    out_path = "/Users/hoangminhlong/my-quantitative/.worktrees/dtp-fx-mechcourt-v1/integration/research/control/DTP-FX-MECHCOURT-V1/fixwindow_spread_census.json"
    with open(out_path, "w") as f:
        json.dump(out, f, indent=1, ensure_ascii=False)
        f.write("\n")
    print("wrote", out_path)

    # console summary: ME1/ME2 vs MID at London 14-16 (headline ask)
    for pair in buckets:
        print(f"\n== {pair} (London hours 14-16, ME1/ME2 vs MID, p50/p90 pips) ==")
        for h in (14, 15, 16):
            row = []
            for ds in ("ME1", "ME2", "MID"):
                s = buckets[pair][f"h{h:02d}"][ds]
                row.append(f"{ds}: n={s['n']} p50={s['p50']} p90={s['p90']}")
            print(f"  h{h:02d}L  " + " | ".join(row))
        fx = buckets[pair]["fixcert"]
        e = fx["entry_F-1h_london14_15_ME1ME2"]
        x = fx["exit_fix_16london_ME1ME2"]
        print(f"  fixcert entry(F-1h 14-15L, ME1|ME2): n={e['n']} p50={e['p50']} p90={e['p90']}")
        print(f"  fixcert exit(16L bar-open, ME1|ME2): n={x['n']} p50={x['p50']} p90={x['p90']}")


if __name__ == "__main__":
    main()
