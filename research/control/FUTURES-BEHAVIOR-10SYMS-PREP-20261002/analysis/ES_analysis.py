#!/usr/bin/env python
"""ES descriptive statistics — lane SYMBOL-DOSSIER-ES, task FUTURES-BEHAVIOR-10SYMS-PREP-20261002.

Descriptive ONLY: no strategy returns, no PnL, no parameter selection, no event
significance tests. Thresholds (where used) are computed with strict
past/trailing windows (window ends the day BEFORE the day being described).

Data: ~/.my-quantitative-data/futures-10syms-v1/raw/ES_*_TRADES_1day_6Y.json
(read-only, IB TWSAPI, useRTH=true -> daily bars are the US RTH session
08:30-16:00 US/Central). Bars with v==0 and o==h==l==c are settlement-derived
close-only marks (FINAL_REPORT FUTURES-DATA-10SYMS-V1); they are separated, not
mixed silently into "traded" stats.

Roll rule (declared by the data lane, used as baseline here):
  hold a contract until the last session BEFORE day-1 of its expiry month, then
  roll to the next listed quarterly (HMUZ) at that session close. No
  back-adjustment anywhere in this script.

Run: /Users/hoangminhlong/my-quantitative/.venv/bin/python ES_analysis.py
Writes: ES_stats.json (same directory).
"""

import json
import math
import os
import statistics
from collections import defaultdict
from datetime import date, timedelta

RAW = os.path.expanduser("~/.my-quantitative-data/futures-10syms-v1/raw")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ES_stats.json")
TICK = 0.25          # ES min tick (S1_IDENTITY.json ESZ6 minTick 0.25)
MULT = 50.0          # ES multiplier (S1_IDENTITY.json "50")
MONTH_CODE = {  # ES quarterly cycle
    "H": 3, "M": 6, "U": 9, "Z": 12,
}

# ---------------------------------------------------------------- load panel
contracts = {}  # localSymbol -> {bars: {date: bar}, first, last, ...}
for fn in sorted(os.listdir(RAW)):
    if not (fn.startswith("ES_") and fn.endswith("_TRADES_1day_6Y.json")):
        continue
    d = json.load(open(os.path.join(RAW, fn)))
    if not d["ok"]:
        raise SystemExit(f"raw file not ok: {fn}")
    bars = {}
    for b in d["bars"]:
        bars[b["t"]] = b
    ls = d["localSymbol"]
    contracts[ls] = {
        "conId": d["conId"],
        "expiry_month_raw": d["expiry_month"],   # lastTradeDate yyyymmdd
        "bars": bars,
        "n_rows_meta": d["n_rows"],
        "useRTH": d["useRTH"],
    }

def ym_of(ls):
    """delivery (expiry) month (yyyy, m) from localSymbol like ESZ6 -> 2026-12."""
    code, yr = ls[2], ls[3]
    month = MONTH_CODE[code]
    year = 2020 + int(yr)  # files span 2021..2028 -> unambiguous in this set
    return year, month

def real_volume_window(bars):
    dates = sorted(bars)
    rv = [t for t in dates if bars[t]["v"] > 0]
    return (rv[0], rv[-1], len(rv)) if rv else (None, None, 0)

panel = []
for ls, c in sorted(contracts.items(), key=lambda kv: ym_of(kv[0])):
    y, m = ym_of(ls)
    dates = sorted(c["bars"])
    flat = sum(1 for t in dates if c["bars"][t]["v"] == 0
               and c["bars"][t]["o"] == c["bars"][t]["h"] == c["bars"][t]["l"] == c["bars"][t]["c"])
    rv0, rv1, rvn = real_volume_window(c["bars"])
    vols = [c["bars"][t]["v"] for t in dates if c["bars"][t]["v"] > 0]
    panel.append({
        "localSymbol": ls, "conId": c["conId"],
        "delivery_month": f"{y}-{m:02d}",
        "lastTradeDate_raw": c["expiry_month_raw"],
        "n_bars": len(dates), "first_bar": dates[0], "last_bar": dates[-1],
        "flat_zero_vol_bars": flat,
        "real_volume_first": rv0, "real_volume_last": rv1, "real_volume_days": rvn,
        "median_daily_volume_real_window": int(statistics.median(vols)) if vols else 0,
        "max_daily_volume": max(vols) if vols else 0,
    })

# ------------------------------------------------------- declared roll table
def last_session_before(ym_string, bars_by_date_union):
    """last trading date strictly before day-1 of expiry month ym (yyyy-mm)."""
    y, m = map(int, ym_string.split("-"))
    d0 = date(y, m, 1)
    cand = [date.fromisoformat(t) for t in bars_by_date_union if date.fromisoformat(t) < d0]
    return max(cand).isoformat() if cand else None

union_dates = set()
for c in contracts.values():
    union_dates |= set(c["bars"])

DATA_END = max(union_dates)  # last available session in the raw set
rolls = []
syms_sorted = sorted(contracts, key=lambda s: ym_of(s))
for old, new in zip(syms_sorted, syms_sorted[1:]):
    y, m = ym_of(old)
    ym = f"{y}-{m:02d}"
    # a roll is only *effective* if the expiry month has begun within the data
    effective = date(y, m, 1) <= date.fromisoformat(DATA_END)
    roll_date = last_session_before(ym, union_dates) if effective else None
    ob, nb = contracts[old]["bars"], contracts[new]["bars"]
    rec = {
        "old": old, "new": new,
        "old_delivery_month": ym,
        "effective_in_data": effective,
        "declared_roll_date": roll_date,
        "old_has_bar": roll_date in ob if roll_date else None,
        "new_has_bar": roll_date in nb if roll_date else None,
    }
    if roll_date and roll_date in ob and roll_date in nb:
        rec["old_close"] = ob[roll_date]["c"]
        rec["new_close"] = nb[roll_date]["c"]
        rec["roll_gap_pts"] = round(nb[roll_date]["c"] - ob[roll_date]["c"], 2)
        rec["roll_gap_ticks"] = round((nb[roll_date]["c"] - ob[roll_date]["c"]) / TICK, 1)
        rec["roll_gap_usd_per_contract"] = round((nb[roll_date]["c"] - ob[roll_date]["c"]) * MULT, 2)
        rec["old_vol_at_roll"] = ob[roll_date]["v"]
        rec["new_vol_at_roll"] = nb[roll_date]["v"]
    rolls.append(rec)

# liquidity migration (OBSERVED): the old contract's raw file ends at the
# declared roll date (fetch endDateTime = day-1 of expiry month), so the
# old-vs-new volume CROSSOVER itself is not observable in this dataset. What IS
# observable: volume of both contracts at the declared roll date, and the date
# the NEXT contract first reaches front-scale volume (100k / 500k / 1M
# contracts per RTH day; descriptive scale markers, not tunable parameters --
# deferred contracts print <5k/day and fronts print ~1M/day, three orders of
# magnitude apart, so any cutoff between gives the same window within days).
FRONT_SCALE = [100000, 500000, 1000000]
migration = []
for r in rolls:
    old, new, rd = r["old"], r["new"], r["declared_roll_date"]
    if not rd:
        continue
    ob, nb = contracts[old]["bars"], contracts[new]["bars"]
    rec = {
        "old": old, "new": new, "declared_roll_date": rd,
        "old_vol_at_declared_roll": ob.get(rd, {}).get("v"),
        "new_vol_at_declared_roll": nb.get(rd, {}).get("v"),
        "old_file_last_date": sorted(ob)[-1],
        "note": "old contract raw bars end at/just before declared roll date (fetch window); post-roll old-side decay and the exact volume crossover are NOT observable",
        "new_first_front_scale_date_after_roll": {},
    }
    for th in FRONT_SCALE:
        firsts = [t for t in sorted(nb) if t > rd and nb[t]["v"] >= th]
        rec["new_first_front_scale_date_after_roll"][f"v>={th}"] = firsts[0] if firsts else None
    migration.append(rec)

# per-contract front-scale ramp dates (any date in file, not only after roll)
for p in panel:
    c = contracts[p["localSymbol"]]["bars"]
    p["first_front_scale_date"] = {}
    for th in FRONT_SCALE:
        firsts = [t for t in sorted(c) if c[t]["v"] >= th]
        p["first_front_scale_date"][f"v>={th}"] = firsts[0] if firsts else None

# --------------------------------------- front continuous (declared rule, UNadjusted)
front_by_date = {}
for r in rolls:
    old, new, rd = r["old"], r["new"], r["declared_roll_date"]
    for t, b in contracts[old]["bars"].items():
        if t <= (rd or "9999-12-31"):
            front_by_date.setdefault(t, (old, b))
    # after roll date old contract may keep trading to expiry; series uses new
for r in rolls:
    new, rd = r["new"], r["declared_roll_date"]
    for t, b in contracts[new]["bars"].items():
        if t > (rd or "9999-12-31"):
            front_by_date[t] = (new, b)
# first contract before first roll: take everything (it IS the front until roll 1)
first_sym = syms_sorted[0]
for t, b in contracts[first_sym]["bars"].items():
    front_by_date.setdefault(t, (first_sym, b))

fd = sorted(front_by_date)
series = []
prev_c = None
for t in fd:
    sym, b = front_by_date[t]
    r = None if prev_c is None else b["c"] / prev_c - 1.0
    series.append({
        "date": t, "front": sym, "close": b["c"], "open": b["o"],
        "high": b["h"], "low": b["l"], "volume": b["v"],
        "simple_ret": None if r is None else round(r, 6),
        "rv_flag": 1 if b["v"] > 0 else 0,
    })
    prev_c = b["c"]

def autocorr1(xs):
    if len(xs) < 10:
        return None
    mean = statistics.fmean(xs)
    num = sum((xs[i] - mean) * (xs[i + 1] - mean) for i in range(len(xs) - 1))
    den = sum((x - mean) ** 2 for x in xs)
    return round(num / den, 4) if den else None

def dstat(vals):
    vals = [v for v in vals if v is not None]
    if not vals:
        return None
    sv = sorted(vals)
    q = lambda p: sv[min(len(sv) - 1, int(p * len(sv)))]
    mean = statistics.fmean(vals)
    sd = statistics.stdev(vals) if len(vals) > 1 else 0.0
    skew = (sum((v - mean) ** 3 for v in vals) / len(vals) / sd ** 3) if sd > 0 else None
    return {
        "n": len(vals), "mean": round(mean, 6), "std": round(sd, 6),
        "min": round(min(vals), 6), "q05": round(q(0.05), 6),
        "q25": round(q(0.25), 6), "median": round(statistics.median(vals), 6),
        "q75": round(q(0.75), 6), "q95": round(q(0.95), 6), "max": round(max(vals), 6),
        "skew": None if skew is None else round(skew, 3),
    }

# whole unadjusted front chain (settlement-derived pre ~2025-06, flagged per-day)
all_rets = [s["simple_ret"] for s in series[1:]]
# roll-boundary returns: the first return AFTER each roll date mixes the roll
# gap (old close -> new close) into the series. Report with and without.
roll_dates_eff = [r["declared_roll_date"] for r in rolls if r["declared_roll_date"]]
ret_excl_roll = []
for i in range(1, len(series)):
    if series[i - 1]["date"] in roll_dates_eff:  # boundary old->new
        continue
    if series[i]["simple_ret"] is not None:
        ret_excl_roll.append(series[i]["simple_ret"])
chain = {
    "n_days": len(series),
    "first_date": fd[0], "last_date": fd[-1],
    "roll_count_effective": len(roll_dates_eff),
    "unadjusted_level_first": series[0]["close"],
    "unadjusted_level_last": series[-1]["close"],
    "returns_all": dstat(all_rets),
    "returns_excl_roll_boundaries": dstat(ret_excl_roll),
    "chain_caveat": ("pre ~2025-06 the chain is settlement-derived closes of the 10 "
                     "available quarterlies, NOT the true market front (fronts ESH5/ESM5..."
                     " not resolvable on this entitlement); under the declared rule each "
                     "roll lands on a thin deferred contract ~2 weeks before the next "
                     "quarterly reaches front-scale volume (see liquidity_migration)"),
}

# front-scale era: days where the chain's front contract trades front-scale
# volume (>=100k contracts/RTH day). Robustness: 500k / 1M cutoffs.
for s in series:
    s["front_scale"] = 1 if s["volume"] >= FRONT_SCALE[0] else 0
fs_series = [s for s in series if s["front_scale"] == 1]
fs_dates = [s["date"] for s in fs_series]
if fs_series:
    chain["front_scale_era"] = {
        "definition": "chain front daily volume >= 100,000 contracts (RTH bar)",
        "first_date": fs_dates[0], "last_date": fs_dates[-1], "n_days": len(fs_series),
        "n_front_scale_days_500k": sum(1 for s in series if s["volume"] >= FRONT_SCALE[1]),
        "n_front_scale_days_1M": sum(1 for s in series if s["volume"] >= FRONT_SCALE[2]),
        "median_front_volume": int(statistics.median([s["volume"] for s in fs_series])),
        "returns_front_scale_era_excl_roll_boundaries": dstat(ret_excl_roll),  # replaced below
    }
    fs_rets = []
    for i in range(1, len(series)):
        if series[i]["front_scale"] == 1 and series[i - 1]["date"] not in roll_dates_eff \
                and series[i]["simple_ret"] is not None:
            fs_rets.append(series[i]["simple_ret"])
    chain["front_scale_era"]["returns_front_scale_era_excl_roll_boundaries"] = dstat(fs_rets)
    chain["front_scale_era"]["annualized_vol_desc"] = round(
        statistics.stdev(fs_rets) * math.sqrt(252), 4) if len(fs_rets) > 1 else None
    chain["front_scale_era"]["abs_ret_lag1_autocorr"] = autocorr1([abs(r) for r in fs_rets])
    # thin windows inside the era (declared-roll -> next contract ramp gaps)
    thin_windows, run = [], None
    for s in series:
        if s["date"] < fs_dates[0]:
            continue
        if s["front_scale"] == 0:
            run = [s["date"], s["date"]] if run is None else [run[0], s["date"]]
        else:
            if run:
                thin_windows.append(run)
            run = None
    chain["front_scale_era"]["thin_front_windows_inside_era"] = thin_windows

# real-volume era (any v>0): kept for completeness, dominated by deferred prints
rv_series = [s for s in series if s["rv_flag"] == 1]
if rv_series:
    chain["real_volume_front_span"] = {
        "first_date": rv_series[0]["date"], "last_date": rv_series[-1]["date"],
        "n_days": len(rv_series),
        "median_front_volume": int(statistics.median([s["volume"] for s in rv_series])),
        "returns_real_volume_era": dstat([s["simple_ret"] for s in rv_series[1:]]),
        "annualized_vol_desc": round(
            statistics.stdev([s["simple_ret"] for s in rv_series[1:]]) * math.sqrt(252), 4),
    }

# rolling 63-day vol (descriptive; window includes current day)
rets = [s["simple_ret"] for s in series]
roll63 = []
for i in range(len(rets)):
    w = [x for x in rets[max(0, i - 62): i + 1] if x is not None]
    if len(w) >= 40:
        roll63.append(statistics.stdev(w))
chain["rolling63_vol"] = {
    "n_windows": len(roll63),
    "min": round(min(roll63), 5), "median": round(statistics.median(roll63), 5),
    "max": round(max(roll63), 5),
} if roll63 else None

# vol persistence (lag-1 autocorr of |ret|, full unadjusted chain, description)
absr = [abs(r) for r in all_rets if r is not None]
chain["abs_ret_lag1_autocorr"] = autocorr1(absr)

# seasonality by calendar month and weekday (description, unadjusted chain, all eras)
bym = defaultdict(list)
byw = defaultdict(list)
for s in series[1:]:
    if s["simple_ret"] is None:
        continue
    y, m, dd = map(int, s["date"].split("-"))
    bym[m].append(s["simple_ret"])
    byw[date(y, m, dd).weekday()].append(s["simple_ret"])
chain["seasonality"] = {
    "by_calendar_month": {m: {"n": len(v), "mean": round(statistics.fmean(v), 5),
                              "vol": round(statistics.stdev(v), 5) if len(v) > 1 else None}
                          for m, v in sorted(bym.items())},
    "by_weekday": {wd: {"n": len(v), "mean": round(statistics.fmean(v), 5),
                        "vol": round(statistics.stdev(v), 5) if len(v) > 1 else None}
                   for wd, v in sorted(byw.items())},
}

# overnight transfer: RTH open vs PRIOR RTH close gap; normalized by trailing
# 20-day mean |ret| ENDING THE PRIOR DAY (strict past window).
gaps = []
for i in range(1, len(series)):
    s, p = series[i], series[i - 1]
    trailing = [abs(x) for x in rets[max(0, i - 1 - 20):i - 1] if x is not None]  # excludes day i-1 itself? -> ends day i-2
    # strict past: use days up to and including i-1 measured before the open of i is knowable same-day;
    # for a pure descriptive normalization we use the window ending the prior session (i-1 included):
    trailing = [abs(x) for x in rets[max(0, i - 20):i] if x is not None]
    gap = s["open"] - p["close"]
    gaps.append({
        "date": s["date"], "gap_pts": round(gap, 2),
        "gap_rel": round(gap / p["close"], 6),
        "trail20_mean_absret": round(statistics.fmean(trailing), 5) if trailing else None,
        "gap_in_trail20_units": round(abs(gap) / p["close"] / statistics.fmean(trailing), 2)
        if trailing and statistics.fmean(trailing) > 0 else None,
        "rv": s["rv_flag"], "fs": s["front_scale"],
    })
gstats_all = dstat([g["gap_rel"] for g in gaps])
gstats_fs = dstat([g["gap_rel"] for g in gaps if g["fs"] == 1])
big_gaps = [g for g in gaps if g["gap_in_trail20_units"] is not None and g["gap_in_trail20_units"] >= 2.0]
overnight = {
    "definition": "RTH open (08:30 CT) minus prior RTH close, relative; normalized by trailing-20d mean |daily ret| incl. prior day (strict past)",
    "n_days": len(gaps),
    "gap_rel_all_days": gstats_all,
    "gap_rel_front_scale_days": gstats_fs,
    "n_gap_ge_2x_trailing": len(big_gaps),
    "share_gap_ge_2x_trailing": round(len(big_gaps) / len(gaps), 4),
    "biggest_5_gaps": sorted(gaps, key=lambda g: abs(g["gap_pts"]), reverse=True)[:5],
}

# ------------------------------------------------------------- BID/ASK 1-year
# FRONT-ONLY: spread computed only on dates where the contract is the chain's
# front (declared rule). Stacking deferred contracts produces quote-rot spreads
# (thousands of USD) that describe deferred quote staleness, not trade costs.
bid_close, ask_close = {}, {}
for ls in sorted(contracts):
    bid_f = os.path.join(RAW, f"ES_{ls}_{contracts[ls]['conId']}_BID_1day_1Y.json")
    ask_f = os.path.join(RAW, f"ES_{ls}_{contracts[ls]['conId']}_ASK_1day_1Y.json")
    if os.path.exists(bid_f) and os.path.exists(ask_f):
        for b in json.load(open(bid_f))["bars"]:
            bid_close[(ls, b["t"])] = b["c"]
        for b in json.load(open(ask_f))["bars"]:
            ask_close[(ls, b["t"])] = b["c"]
ba = []
for s in series:  # series = declared-rule front chain
    ls, t = s["front"], s["date"]
    if (ls, t) in bid_close and (ls, t) in ask_close:
        sp = ask_close[(ls, t)] - bid_close[(ls, t)]
        ba.append({"date": t, "sym": ls, "spread_pts": round(sp, 2),
                   "spread_ticks": round(sp / TICK, 1),
                   "spread_usd": round(sp * MULT, 2),
                   "crossed": sp < 0, "front_scale": s["front_scale"]})
sp_usd = [x["spread_usd"] for x in ba if not x["crossed"]]
sp_usd_fs = [x["spread_usd"] for x in ba if not x["crossed"] and x["front_scale"] == 1]
bidask = {
    "n_days": len(ba),
    "first": ba[0]["date"] if ba else None, "last": ba[-1]["date"] if ba else None,
    "n_crossed": sum(1 for x in ba if x["crossed"]),
    "median_spread_usd_all": round(statistics.median(sp_usd), 2) if sp_usd else None,
    "p90_spread_usd_all": round(sorted(sp_usd)[int(0.9 * len(sp_usd))], 2) if sp_usd else None,
    "median_spread_ticks_all": round(statistics.median(sp_usd) / (TICK * MULT), 1) if sp_usd else None,
    "front_scale_days_only": {
        "n_days": len(sp_usd_fs),
        "median_spread_usd": round(statistics.median(sp_usd_fs), 2) if sp_usd_fs else None,
        "p90_spread_usd": round(sorted(sp_usd_fs)[int(0.9 * len(sp_usd_fs))], 2) if sp_usd_fs else None,
        "median_spread_ticks": round(statistics.median(sp_usd_fs) / (TICK * MULT), 1) if sp_usd_fs else None,
    },
    "note": "BID/ASK daily closes are not synchronous snapshots; spread is close-to-close proxy (same caveat as S6_FRONT_SPREADS); deferred-quote rot excluded by front-only filter",
}

# ------------------------------------------------- hourly RTH profile (30 days)
# FRONT FILE ONLY: each contract's 30D hourly file covers a different window
# (expired contracts' windows end at their fetch endDateTime); mixing them
# double-counts eras. Per-file windows are listed for transparency.
hourly_files = {}
for fn in sorted(os.listdir(RAW)):
    if not (fn.startswith("ES_") and fn.endswith("_TRADES_1hour_30D.json")):
        continue
    d = json.load(open(os.path.join(RAW, fn)))
    if not d["bars"]:
        continue
    hourly_files[d["localSymbol"]] = {
        "window": f"{d['bars'][0]['t'][:10]}..{d['bars'][-1]['t'][:10]}",
        "n_bars": len(d["bars"]),
        "total_volume": sum(b["v"] for b in d["bars"]),
        "bars": d["bars"],
    }
front_sym_now = series[-1]["front"]  # current front = ESZ6
hf = hourly_files.get(front_sym_now)
hourly_profile = None
if hf:
    hourly = defaultdict(int)
    hourly_dates = set()
    for b in hf["bars"]:
        hourly[int(b["t"][11:13])] += b["v"]
        hourly_dates.add(b["t"][:10])
    tot_h = sum(hourly.values())
    hourly_profile = {
        "contract": front_sym_now,
        "window": hf["window"], "n_days": len(hourly_dates), "n_bars": hf["n_bars"],
        "note": "useRTH=true: RTH 08:30-16:00 US/Central only; Globex overnight NOT in file",
        "volume_share_by_hour_CT": {h: round(v / tot_h, 4) for h, v in sorted(hourly.items())},
        "first_hour_share_08": round(hourly.get(8, 0) / tot_h, 4),
        "last_full_hour_share_14": round(hourly.get(14, 0) / tot_h, 4),
        "per_file_windows": {k: {kk: vv for kk, vv in v.items() if kk != "bars"}
                             for k, v in hourly_files.items()},
    }

out = {
    "schema": "FUTURES-BEHAVIOR-10SYMS-PREP/ES_stats@1",
    "generated_utc": "2026-10-02",
    "script": "analysis/ES_analysis.py",
    "raw_source": "~/.my-quantitative-data/futures-10syms-v1/raw/ ES_*_TRADES_1day_6Y.json (+BID/ASK_1day_1Y, +TRADES_1hour_30D), useRTH=true",
    "contract_panel": panel,
    "declared_rule_rolls": rolls,
    "liquidity_migration": migration,
    "front_chain_unadjusted": chain,
    "overnight_open_gap": overnight,
    "bid_ask_1y": bidask,
    "hourly_rth_profile_30d": hourly_profile,
}
with open(OUT, "w") as f:
    json.dump(out, f, indent=1)
print("wrote", OUT)
print(json.dumps({k: out[k] for k in
                  ["contract_panel", "declared_rule_rolls", "liquidity_migration",
                   "front_chain_unadjusted", "overnight_open_gap", "bid_ask_1y",
                   "hourly_rth_profile_30d"]}, indent=1))
