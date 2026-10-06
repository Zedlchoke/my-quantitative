#!/usr/bin/env python
"""6A descriptive statistics — lane SYMBOL-DOSSIER-6A, task FUTURES-BEHAVIOR-10SYMS-PREP-20261002.

Descriptive ONLY: no strategy returns, no PnL, no parameter selection, no event
significance tests. Thresholds (where used) are descriptive scale markers with
strict past/trailing windows (window ends the day BEFORE the day described).

Methodology follows the sibling lanes (analysis/6E_descriptives.py structure;
GC serial-gap executability check per GC_DOSSIER §1).

Data: ~/.my-quantitative-data/futures-10syms-v1/raw/6A_*_TRADES_1day_6Y.json
(read-only, IB TWSAPI, useRTH=true -> daily bars cover only 08:30-16:00
US/Central of the ~23h Globex session; Sydney/Tokyo + London + the 08:30 ET
US-data part of each day is NOT in the bars; measurable only via open-vs-
prior-close gap). Bars with v==0 and o==h==l==c are settlement-derived
close-only marks (FINAL_REPORT FUTURES-DATA-10SYMS-V1); they are separated,
not mixed silently into "traded" stats.

Roll rule (data lane declared, baseline): hold until the last session BEFORE
day-1 of the expiry month, roll to the NEXT LISTED contract at that close.
For 6A this project applies it two ways and measures both:
  (a) LITERAL  — next listed contract by expiry (includes serial months);
  (b) QUARTERLY-ONLY adaptation — next HMUZ contract (the market's liquidity
      chain, because CME FX serial months trade 3-4 orders of magnitude less
      than quarterlies; measured below).
No back-adjustment anywhere in this script.

Run: /Users/hoangminhlong/my-quantitative/.venv/bin/python 6A_descriptives.py
Writes: 6A_descriptives.json (same directory).
"""

import json
import math
import os
import statistics
from collections import defaultdict
from datetime import date, timedelta

RAW = os.path.expanduser("~/.my-quantitative-data/futures-10syms-v1/raw")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "6A_descriptives.json")
TICK = 5e-05        # 6A min tick (S1_IDENTITY.json all resolved contracts minTick 5e-05)
MULT = 100000.0     # 6A multiplier AUD 100,000 (S1_IDENTITY.json "100000")
MONTH_CODE = {      # full CME month code map (6A lists serials too)
    "F": 1, "G": 2, "H": 3, "J": 4, "K": 5, "M": 6,
    "N": 7, "Q": 8, "U": 9, "V": 10, "X": 11, "Z": 12,
}
QUARTERLY = set("HMUZ")
# Descriptive front-scale volume markers (contracts per RTH day). Basis: serial
# months print 1-17/day and deferred quarterlies ~0-2k/day while the liquid
# quarterly front prints 28k-67k/day (measured below) — orders of magnitude
# apart, so any cutoff between 10k and 25k gives the same era within days.
FRONT_SCALE = [10000, 25000, 50000]

# ---------------------------------------------------------------- load panel
contracts = {}
for fn in sorted(os.listdir(RAW)):
    if not (fn.startswith("6A_") and fn.endswith("_TRADES_1day_6Y.json")):
        continue
    d = json.load(open(os.path.join(RAW, fn)))
    if not d["ok"]:
        raise SystemExit(f"raw file not ok: {fn}")
    bars = {b["t"]: b for b in d["bars"]}
    contracts[d["localSymbol"]] = {
        "conId": d["conId"],
        "expiry_month_raw": d["expiry_month"],   # lastTradeDate yyyymmdd
        "bars": bars,
        "useRTH": d["useRTH"],
    }

def ym_of(ls):
    """(year, month) from localSymbol like 6AZ6 -> (2026, 12)."""
    return 2020 + int(ls[3]), MONTH_CODE[ls[2]]

def is_q(ls):
    return ls[2] in QUARTERLY

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

def autocorr1(xs):
    if len(xs) < 10:
        return None
    mean = statistics.fmean(xs)
    num = sum((xs[i] - mean) * (xs[i + 1] - mean) for i in range(len(xs) - 1))
    den = sum((x - mean) ** 2 for x in xs)
    return round(num / den, 4) if den else None

# ------------------------------------------------------------------- panel
panel = []
for ls, c in sorted(contracts.items(), key=lambda kv: ym_of(kv[0])):
    y, m = ym_of(ls)
    dates = sorted(c["bars"])
    flat = sum(1 for t in dates if c["bars"][t]["v"] == 0
               and c["bars"][t]["o"] == c["bars"][t]["h"] == c["bars"][t]["l"] == c["bars"][t]["c"])
    rv = [t for t in dates if c["bars"][t]["v"] > 0]
    vols = [c["bars"][t]["v"] for t in rv]
    closes = [c["bars"][t]["c"] for t in dates if c["bars"][t]["v"] > 0]
    panel.append({
        "localSymbol": ls, "conId": c["conId"], "is_quarterly": is_q(ls),
        "delivery_month": f"{y}-{m:02d}",
        "lastTradeDate_raw": c["expiry_month_raw"],
        "n_bars": len(dates), "first_bar": dates[0], "last_bar": dates[-1],
        "flat_zero_vol_bars": flat,
        "flat_share_pct": round(100.0 * flat / len(dates), 1) if dates else None,
        "real_volume_first": rv[0] if rv else None,
        "real_volume_last": rv[-1] if rv else None,
        "real_volume_days": len(rv),
        "median_daily_volume_real_window": int(statistics.median(vols)) if vols else 0,
        "max_daily_volume": max(vols) if vols else 0,
        "close_min_real_window": min(closes) if closes else None,
        "close_max_real_window": max(closes) if closes else None,
    })

# ----------------------------------------- quarterly vs serial liquidity split
last40_by_type = defaultdict(list)   # recent median volume by Q/S across contracts
for p in panel:
    c = contracts[p["localSymbol"]]["bars"]
    recent = [c[t]["v"] for t in sorted(c)[-40:]]
    last40_by_type["quarterly" if p["is_quarterly"] else "serial"].append(
        {"ls": p["localSymbol"], "median_vol_last40_sessions": int(statistics.median(recent)) if recent else 0})
qser = {
    "note": ("serial (non-HMUZ) months are listed but trade 3-4 orders of magnitude below "
             "quarterlies; the market front chain for 6A is the quarterly chain"),
    "quarterly_recent_median_volumes": last40_by_type["quarterly"],
    "serial_recent_median_volumes": last40_by_type["serial"],
}

# ------------------------------------------------ quote convention sanity check
all_closes = [(ls, t, b["c"]) for ls, c in contracts.items() for t, b in c["bars"].items()]
mn = min(all_closes, key=lambda x: x[2])
mx = max(all_closes, key=lambda x: x[2])
quote_check = {
    "convention": "USD per 1 AUD (AUD/USD style), NOT inverted; S1 currency=USD, multiplier 100000 AUD",
    "min_close": {"value": mn[2], "sym": mn[0], "date": mn[1]},
    "max_close": {"value": mx[2], "sym": mx[0], "date": mx[1]},
    "reciprocal_range_AUDUSD_spot_equivalent": [round(1.0 / mx[2], 4), round(1.0 / mn[2], 4)],
    "n_closes_total": len(all_closes),
}

# ------------------------------------------------------- declared roll tables
union_dates = set()
for c in contracts.values():
    union_dates |= set(c["bars"])
DATA_END = max(union_dates)

def last_session_before(ym_string):
    y, m = map(int, ym_string.split("-"))
    d0 = date(y, m, 1)
    cand = [date.fromisoformat(t) for t in union_dates if date.fromisoformat(t) < d0]
    return max(cand).isoformat() if cand else None

def roll_table(syms):
    rolls = []
    for old, new in zip(syms, syms[1:]):
        y, m = ym_of(old)
        ym = f"{y}-{m:02d}"
        effective = date(y, m, 1) <= date.fromisoformat(DATA_END)
        rd = last_session_before(ym) if effective else None
        ob, nb = contracts[old]["bars"], contracts[new]["bars"]
        rec = {
            "old": old, "new": new, "old_delivery_month": ym,
            "old_expiry_lastTradeDate": contracts[old]["expiry_month_raw"],
            "effective_in_data": effective, "declared_roll_date": rd,
            "old_has_bar": rd in ob if rd else None,
            "new_has_bar": rd in nb if rd else None,
        }
        if rd and rd in ob and rd in nb:
            gap = nb[rd]["c"] - ob[rd]["c"]
            days_gap = (date.fromisoformat(contracts[new]["expiry_month_raw"])
                        - date.fromisoformat(contracts[old]["expiry_month_raw"])).days
            rec.update({
                "old_close": ob[rd]["c"], "new_close": nb[rd]["c"],
                "roll_gap_pts": round(gap, 6),
                "roll_gap_ticks": round(gap / TICK, 1),
                "roll_gap_usd_per_contract": round(gap * MULT, 2),
                "roll_gap_pct_of_level": round(100.0 * gap / ob[rd]["c"], 4),
                "roll_gap_annualized_pct": round(100.0 * gap / ob[rd]["c"] * 365.0 / days_gap, 3)
                if days_gap else None,
                "old_vol_at_roll": ob[rd]["v"], "new_vol_at_roll": nb[rd]["v"],
                "calendar_days_between_expiries": days_gap,
            })
        rolls.append(rec)
    return rolls

all_syms = sorted(contracts, key=ym_of)
q_syms = [s for s in all_syms if is_q(s)]
rolls_literal = roll_table(all_syms)     # includes serial legs where present
rolls_quarterly = roll_table(q_syms)     # the liquidity chain

# ------------------------- serial-gap executability check (GC-style, explicit)
# The LITERAL declared rule needs the next LISTED month (incl. serials) at each
# roll. Enumerate every calendar month from the first real-volume chain month
# to DATA_END+1 and record which month the literal rule would need vs whether
# the raw set has that contract.
first_chain_ls = "6AZ5"   # deepest resolved quarterly (S1 deepest_resolved 202512);
                          # the pre-2025-12 quarterlies never resolved (expired wall)
chain_months = []
y0, m0 = ym_of(first_chain_ls)
y1, m1 = map(int, DATA_END.split("-")[:2])
y, m = y0, m0
while (y, m) <= (y1, m1):
    chain_months.append((y, m))
    m += 1
    if m == 13:
        y, m = y + 1, 1

def sym_for(y, m):
    code = {v: k for k, v in MONTH_CODE.items()}[m]
    return f"6A{code}{y % 10}"

serial_gaps = {
    "rule_under_test": ("LITERAL declared rule: roll to next LISTED contract (incl. serial "
                        "months) at the last session before day-1 of the expiry month"),
    "chain_start_quarterly": first_chain_ls,
    "months_checked": [],
    "missing_serial_contracts_needed": [],
    "note": ("pre-2025-12 quarterlies (6AU5 and earlier) are absent entirely (expired-secdef "
             "wall, S1 deepest_resolved=202512), so the literal chain is only evaluable from "
             "the 6AZ5 holding window onward; S1 cannot adjudicate whether the missing serial "
             "months were listed on their roll dates (CME product calendar transport-blocked) "
             "— the DEFECT reported here is snapshot non-executability, not non-listing"),
}
for y, m in chain_months:
    s = sym_for(y, m)
    serial_gaps["months_checked"].append({
        "month": f"{y}-{m:02d}", "needed_by_literal_rule": s, "in_raw_set": s in contracts,
        "is_quarterly": is_q(s),
        "has_any_real_volume": any(b["v"] > 0 for b in contracts[s]["bars"].values())
        if s in contracts else False,
    })
serial_gaps["missing_serial_contracts_needed"] = [
    x["needed_by_literal_rule"] for x in serial_gaps["months_checked"]
    if not x["in_raw_set"] and not x["is_quarterly"]]

# liquidity migration on the quarterly chain: when does NEXT quarterly reach
# front-scale volume, relative to old quarterly's expiry and declared roll?
migration = []
for r in rolls_quarterly:
    old, new, rd = r["old"], r["new"], r["declared_roll_date"]
    if not rd:
        continue
    nb = contracts[new]["bars"]
    rec = {
        "old": old, "new": new, "declared_roll_date": rd,
        "old_lastTradeDate": contracts[old]["expiry_month_raw"],
        "old_vol_at_declared_roll": contracts[old]["bars"].get(rd, {}).get("v"),
        "new_vol_at_declared_roll": nb.get(rd, {}).get("v"),
        "old_file_last_date": sorted(contracts[old]["bars"])[-1],
        "note": ("old contract raw bars end at/just before the declared roll date (fetch "
                 "window endDateTime = day-1 of expiry month); old-side decay after that and "
                 "the exact old-vs-new volume crossover are NOT observable in this snapshot"),
        "new_first_front_scale_date": {},
        "new_first_front_scale_vs_old_expiry_biz_days": {},
    }
    old_exp = date.fromisoformat(contracts[old]["expiry_month_raw"])
    for th in FRONT_SCALE:
        firsts = [t for t in sorted(nb) if nb[t]["v"] >= th]
        rec["new_first_front_scale_date"][f"v>={th}"] = firsts[0] if firsts else None
        if firsts:
            f0 = date.fromisoformat(firsts[0])
            rec["new_first_front_scale_vs_old_expiry_biz_days"][f"v>={th}"] = \
                round((f0 - old_exp).days / 7.0, 2)  # approximate weeks vs expiry (calendar)
    migration.append(rec)

# --------------------------------------------------- front chains (unadjusted)
def build_chain(syms, use_declared_dates=True):
    rolls_local = roll_table(syms)
    front_by_date = {}
    for r in rolls_local:
        old, new, rd = r["old"], r["new"], r["declared_roll_date"]
        for t, b in contracts[old]["bars"].items():
            if t <= (rd or "9999-12-31"):
                front_by_date.setdefault(t, (old, b))
        for t, b in contracts[new]["bars"].items():
            if t > (rd or "9999-12-31"):
                front_by_date[t] = (new, b)
    for t, b in contracts[syms[0]]["bars"].items():
        front_by_date.setdefault(t, (syms[0], b))
    out = []
    prev_c = None
    for t in sorted(front_by_date):
        sym, b = front_by_date[t]
        ret = None if prev_c is None else b["c"] / prev_c - 1.0
        out.append({
            "date": t, "front": sym, "is_quarterly": is_q(sym),
            "close": b["c"], "open": b["o"], "volume": b["v"],
            "simple_ret": None if ret is None else round(ret, 6),
            "rv_flag": 1 if b["v"] > 0 else 0,
        })
        prev_c = b["c"]
    return out, rolls_local

chain_q, _ = build_chain(q_syms)                 # quarterly-only adaptation
chain_lit, _ = build_chain(all_syms)             # literal next-listed (serials in)

roll_dates_eff = {r["declared_roll_date"] for r in rolls_quarterly if r["declared_roll_date"]}

def chain_stats(series, name, roll_dates):
    all_rets = [s["simple_ret"] for s in series[1:] if s["simple_ret"] is not None]
    ret_excl = []
    for i in range(1, len(series)):
        if series[i - 1]["date"] in roll_dates:
            continue
        if series[i]["simple_ret"] is not None:
            ret_excl.append(series[i]["simple_ret"])
    fs = [s for s in series if s["volume"] >= FRONT_SCALE[0]]
    res = {
        "definition": name,
        "n_days": len(series),
        "first_date": series[0]["date"], "last_date": series[-1]["date"],
        "n_roll_boundaries": len(roll_dates),
        "unadjusted_level_first": series[0]["close"],
        "unadjusted_level_last": series[-1]["close"],
        "returns_all": dstat(all_rets),
        "returns_excl_roll_boundaries": dstat(ret_excl),
    }
    if fs:
        fs_rets = []
        for i in range(1, len(series)):
            if series[i]["volume"] >= FRONT_SCALE[0] \
                    and series[i - 1]["date"] not in roll_dates \
                    and series[i]["simple_ret"] is not None:
                fs_rets.append(series[i]["simple_ret"])
        res["front_scale_era"] = {
            "definition": f"chain front daily volume >= {FRONT_SCALE[0]:,} contracts (RTH bar)",
            "first_date": fs[0]["date"], "last_date": fs[-1]["date"], "n_days": len(fs),
            "n_days_ge_25k": sum(1 for s in series if s["volume"] >= FRONT_SCALE[1]),
            "n_days_ge_50k": sum(1 for s in series if s["volume"] >= FRONT_SCALE[2]),
            "median_front_volume": int(statistics.median([s["volume"] for s in fs])),
            "returns_front_scale_era_excl_roll_boundaries": dstat(fs_rets),
            "annualized_vol_desc": round(statistics.stdev(fs_rets) * math.sqrt(252), 4)
            if len(fs_rets) > 1 else None,
            "abs_ret_lag1_autocorr": autocorr1([abs(r) for r in fs_rets]),
        }
    return res

q_chain_stats = chain_stats(chain_q, "quarterly-only front (declared roll timing, HMUZ targets)", roll_dates_eff)

# literal-rule damage report: front volume where literal rule holds a serial
def flush(run):
    return {
        "front": run[2], "first": run[0], "last": run[1], "n_days": len(run[3]),
        "median_front_volume": int(statistics.median(run[3])),
        "max_front_volume": max(run[3]),
    }

serial_windows = []
run = None
for s in chain_lit:
    same_front = run is not None and run[2] == s["front"]
    if run is not None and not same_front:      # any front change flushes
        serial_windows.append(flush(run))
        run = None
    if not s["is_quarterly"]:
        run = [s["date"], s["date"], s["front"], [s["volume"]]] if run is None \
            else [run[0], s["date"], s["front"], run[3] + [s["volume"]]]
    # quarterly fronts leave run = None
if run:
    serial_windows.append(flush(run))
# for each serial-front window, the QUARTERLY chain's front volume same day (what
# the quarterly adaptation would have held)
for w in serial_windows:
    qvols = [s["volume"] for s in chain_q
             if w["first"] <= s["date"] <= w["last"] and s["is_quarterly"]]
    w["quarterly_chain_front_median_volume_same_window"] = int(statistics.median(qvols)) if qvols else None

# vol persistence + rolling 63d vol (quarterly chain, all eras, descriptive)
allr_q = [s["simple_ret"] for s in chain_q[1:]]
q_chain_stats["abs_ret_lag1_autocorr_full_chain"] = autocorr1([abs(r) for r in allr_q if r is not None])
roll63 = []
for i in range(len(chain_q)):
    w = [s["simple_ret"] for s in chain_q[max(0, i - 62):i + 1] if s["simple_ret"] is not None]
    if len(w) >= 40:
        roll63.append(statistics.stdev(w))
q_chain_stats["rolling63_vol"] = {
    "n_windows": len(roll63),
    "min": round(min(roll63), 5), "median": round(statistics.median(roll63), 5),
    "max": round(max(roll63), 5),
} if roll63 else None

# annualized vol by year: quarterly chain vs single-contract long refs (settlement-derived)
def vol_by_year(series):
    byyr = defaultdict(list)
    for s in series:
        if s["simple_ret"] is not None:
            byyr[s["date"][:4]].append(s["simple_ret"])
    return {y: {"n": len(v), "ann_vol_pct": round(statistics.stdev(v) * math.sqrt(252) * 100, 2)}
            for y, v in sorted(byyr.items()) if len(v) > 1}

single_refs = {}
for ref in ["6AU6", "6AZ6"]:
    if ref in contracts:
        dates = sorted(contracts[ref]["bars"])
        rows, prev = [], None
        for t in dates:
            c = contracts[ref]["bars"][t]["c"]
            rows.append({"date": t, "simple_ret": None if prev is None else round(c / prev - 1, 6)})
            prev = c
        single_refs[ref] = {
            "span": f"{dates[0]}..{dates[-1]}", "n": len(dates),
            "caveat": "full-depth daily file is settlement-derived (v=0, o=h=l=c) except its "
                      "final months; reference/description only, never fill prices",
            "vol_by_year_pct": vol_by_year(rows),
        }
q_chain_stats["vol_by_year_pct"] = vol_by_year(chain_q)

# worst/best real-era days, trend persistence, large-move frequency (strict past)
fs_start = q_chain_stats.get("front_scale_era", {}).get("first_date")
fs_rows = [s for s in chain_q if fs_start and s["date"] >= fs_start]
worst_best = sorted([s for s in fs_rows if s["simple_ret"] is not None],
                    key=lambda s: s["simple_ret"])
trend_persist = {
    "definition": ("share of days whose return sign matches the mean sign of the PRIOR 50 "
                   "sessions (strict past window), front-scale era"),
}
sg_match, sg_n = 0, 0
for i in range(len(chain_q)):
    s = chain_q[i]
    if s["simple_ret"] is None or i < 50 or (fs_start and s["date"] < fs_start):
        continue
    prior = [x["simple_ret"] for x in chain_q[i - 50:i] if x["simple_ret"] is not None]
    if not prior:
        continue
    pm = statistics.fmean(prior)
    if pm == 0:
        continue
    sg_n += 1
    if (s["simple_ret"] > 0) == (pm > 0):
        sg_match += 1
trend_persist.update({"n": sg_n, "share_sign_match_pct": round(100.0 * sg_match / sg_n, 1) if sg_n else None})

big_moves = {
    "definition": ("days with |return| above the 95th percentile of |return| over the PRIOR "
                   "126 sessions (strict past window), front-scale era"),
    "dates": [],
}
for i in range(len(chain_q)):
    s = chain_q[i]
    if s["simple_ret"] is None or i < 126 or (fs_start and s["date"] < fs_start):
        continue
    prior = [abs(x["simple_ret"]) for x in chain_q[i - 126:i] if x["simple_ret"] is not None]
    if len(prior) < 100:
        continue
    thr = sorted(prior)[int(0.95 * len(prior))]
    if abs(s["simple_ret"]) > thr:
        big_moves["dates"].append({"date": s["date"], "ret_pct": round(100 * s["simple_ret"], 3),
                                   "thr_pct": round(100 * thr, 3), "front": s["front"]})
big_moves["n_events"] = len(big_moves["dates"])

# seasonality: full quarterly chain (settlement-era caveat) + front-scale era weekday only
bym, byw, byw_fs = defaultdict(list), defaultdict(list), defaultdict(list)
for i in range(1, len(chain_q)):
    s = chain_q[i]
    if s["simple_ret"] is None:
        continue
    y, m, dd = map(int, s["date"].split("-"))
    bym[m].append(s["simple_ret"])
    wd = date(y, m, dd).weekday()
    byw[wd].append(s["simple_ret"])
    if fs_start and s["date"] >= fs_start and s["date"] not in roll_dates_eff:
        byw_fs[wd].append(s["simple_ret"])
q_chain_stats["seasonality"] = {
    "by_calendar_month_full_chain": {
        m: {"n": len(v), "mean": round(statistics.fmean(v), 5),
            "vol": round(statistics.stdev(v), 5) if len(v) > 1 else None}
        for m, v in sorted(bym.items())},
    "by_weekday_full_chain": {
        wd: {"n": len(v), "mean": round(statistics.fmean(v), 5),
             "vol": round(statistics.stdev(v), 5) if len(v) > 1 else None}
        for wd, v in sorted(byw.items())},
    "by_weekday_front_scale_era": {
        wd: {"n": len(v), "mean": round(statistics.fmean(v), 5),
             "vol": round(statistics.stdev(v), 5) if len(v) > 1 else None}
        for wd, v in sorted(byw_fs.items())},
    "caveat": "full chain includes settlement-derived marks (v=0, o=h=l=c) pre ~2025; "
              "front-scale era is only ~13 months so by-month cells have n<=2 (not reported)",
}

# overnight/hidden-session gap: RTH open vs PRIOR RTH close (quarterly chain).
# For 6A this gap spans the Sydney/Tokyo open + full London morning + the 08:30 ET
# US-data block — i.e., everything outside 08:30-16:00 CT, which includes the
# RBA decision time, AU CPI/labour-force releases and China data. Normalize by
# trailing-20d mean |ret| ending the prior session (strict past).
rets_q = [s["simple_ret"] for s in chain_q]
gaps = []
for i in range(1, len(chain_q)):
    s, p = chain_q[i], chain_q[i - 1]
    trailing = [abs(x) for x in rets_q[max(0, i - 20):i] if x is not None]
    gap = s["open"] - p["close"]
    gaps.append({
        "date": s["date"], "gap_pts": round(gap, 6),
        "gap_rel": round(gap / p["close"], 6),
        "gap_pips": round(gap * 10000, 1),  # AUD/USD pip = 0.0001
        "trail20_mean_absret": round(statistics.fmean(trailing), 5) if trailing else None,
        "gap_in_trail20_units": round(abs(gap) / p["close"] / statistics.fmean(trailing), 2)
        if trailing and statistics.fmean(trailing) > 0 else None,
        "rv": s["rv_flag"],
        "fs": 1 if s["volume"] >= FRONT_SCALE[0] else 0,
    })
g_fs = [g["gap_rel"] for g in gaps if g["fs"] == 1]
g_all = [g["gap_rel"] for g in gaps]
big = [g for g in gaps if g["gap_in_trail20_units"] is not None and g["gap_in_trail20_units"] >= 2.0]
overnight = {
    "definition": ("RTH open (08:30 CT) minus prior RTH close, relative; the hidden part of the "
                   "day for this snapshot: Sydney/Tokyo + full London morning + 08:30 ET US "
                   "releases + (for CT-morning dates) AU/China releases; normalized by "
                   "trailing-20d mean |daily ret| incl. prior session (strict past)"),
    "n_days": len(gaps),
    "gap_rel_all_days": dstat(g_all),
    "gap_rel_front_scale_days": dstat(g_fs),
    "gap_pips_front_scale_median": round(statistics.median([g["gap_pips"] for g in gaps if g["fs"] == 1]), 1)
    if g_fs else None,
    "n_gap_ge_2x_trailing": len(big),
    "share_gap_ge_2x_trailing_all": round(len(big) / len(gaps), 4) if gaps else None,
    "biggest_5_gaps": sorted(gaps, key=lambda g: abs(g["gap_pts"]), reverse=True)[:5],
}

# ------------------------------------------------------------- BID/ASK 1-year
bid_close, ask_close = {}, {}
for ls in contracts:
    bid_f = os.path.join(RAW, f"6A_{ls}_{contracts[ls]['conId']}_BID_1day_1Y.json")
    ask_f = os.path.join(RAW, f"6A_{ls}_{contracts[ls]['conId']}_ASK_1day_1Y.json")
    if os.path.exists(bid_f) and os.path.exists(ask_f):
        for b in json.load(open(bid_f))["bars"]:
            bid_close[(ls, b["t"])] = b["c"]
        for b in json.load(open(ask_f))["bars"]:
            ask_close[(ls, b["t"])] = b["c"]
ba = []
for s in chain_q:
    ls, t = s["front"], s["date"]
    if (ls, t) in bid_close and (ls, t) in ask_close:
        sp = ask_close[(ls, t)] - bid_close[(ls, t)]
        ba.append({"date": t, "sym": ls, "spread_pts": round(sp, 6),
                   "spread_ticks": round(sp / TICK, 1),
                   "spread_usd": round(sp * MULT, 2),
                   "crossed": sp < 0,
                   "front_scale": 1 if s["volume"] >= FRONT_SCALE[0] else 0})
sp_usd = [x["spread_usd"] for x in ba if not x["crossed"]]
sp_fs = [x["spread_usd"] for x in ba if not x["crossed"] and x["front_scale"] == 1]
bidask = {
    "n_days": len(ba),
    "first": ba[0]["date"] if ba else None, "last": ba[-1]["date"] if ba else None,
    "n_crossed": sum(1 for x in ba if x["crossed"]),
    "median_spread_usd_all": round(statistics.median(sp_usd), 2) if sp_usd else None,
    "median_spread_ticks_all": round(statistics.median(sp_usd) / (TICK * MULT), 1) if sp_usd else None,
    "p90_spread_usd_all": round(sorted(sp_usd)[int(0.9 * len(sp_usd))], 2) if sp_usd else None,
    "front_scale_days_only": {
        "n_days": len(sp_fs),
        "median_spread_usd": round(statistics.median(sp_fs), 2) if sp_fs else None,
        "median_spread_ticks": round(statistics.median(sp_fs) / (TICK * MULT), 1) if sp_fs else None,
        "p90_spread_usd": round(sorted(sp_fs)[int(0.9 * len(sp_fs))], 2) if sp_fs else None,
    },
    "note": ("BID/ASK daily closes are not synchronous snapshots; close-to-close proxy (same "
             "caveat as S6_FRONT_SPREADS, which measured the S1 serial front 6AV6: 4 ticks=$20); "
             "this chain table follows the QUARTERLY chain front"),
}
# also the S1 serial front (6AV6/6AX6) spread for direct reconciliation with S6
serial_front_ba = []
for ls in ["6AV6", "6AX6"]:
    dates = sorted(t for (l, t) in bid_close if l == ls and (ls, t) in ask_close)
    rows = [{"date": t, "sym": ls,
             "spread_ticks": round((ask_close[(ls, t)] - bid_close[(ls, t)]) / TICK, 1),
             "spread_usd": round((ask_close[(ls, t)] - bid_close[(ls, t)]) * MULT, 2)}
            for t in dates]
    if rows:
        usd = [r["spread_usd"] for r in rows if r["spread_usd"] >= 0]
        serial_front_ba.append({
            "sym": ls, "n_days": len(rows), "first": rows[0]["date"], "last": rows[-1]["date"],
            "median_spread_usd": round(statistics.median(usd), 2) if usd else None,
            "median_spread_ticks": round(statistics.median(usd) / (TICK * MULT), 1) if usd else None,
        })

# ------------------------------------------------- hourly RTH profile (30 days)
hourly_files = {}
for fn in sorted(os.listdir(RAW)):
    if fn.startswith("6A_") and fn.endswith("_TRADES_1hour_30D.json"):
        d = json.load(open(os.path.join(RAW, fn)))
        if d["bars"]:
            hourly_files[d["localSymbol"]] = {
                "window": f"{d['bars'][0]['t'][:10]}..{d['bars'][-1]['t'][:10]}",
                "n_bars": len(d["bars"]),
                "total_volume": sum(b["v"] for b in d["bars"]),
                "bars": d["bars"],
            }
front_now = chain_q[-1]["front"]
hf = hourly_files.get(front_now)
hourly_profile = None
if hf:
    hourly, days = defaultdict(int), set()
    for b in hf["bars"]:
        hourly[int(b["t"][11:13])] += b["v"]
        days.add(b["t"][:10])
    tot = sum(hourly.values())
    hourly_profile = {
        "contract": front_now, "window": hf["window"], "n_days": len(days), "n_bars": hf["n_bars"],
        "note": ("useRTH=true: bars cover 08:30-16:00 US/Central only; Sydney/Tokyo/London "
                 "NOT in file; 6A's home-session price discovery is unmeasured here"),
        "volume_share_by_hour_CT": {h: round(v / tot, 4) for h, v in sorted(hourly.items())},
        "first_half_hour_0830": round(hourly.get(8, 0) / tot, 4),
        "last_full_hour_14": round(hourly.get(14, 0) / tot, 4),
        "per_file_windows": {k: {kk: vv for kk, vv in v.items() if kk != "bars"}
                             for k, v in sorted(hourly_files.items())},
    }

# ------------------------------------- expiry-day rule check (3rd Wed -2 bus dys)
def third_wednesday(y, m):
    d = date(y, m, 1)
    wds = [d + timedelta(days=i) for i in range(31) if (d + timedelta(days=i)).month == m]
    weds = [x for x in wds if x.weekday() == 2]
    return weds[2]

def two_business_days_before(d0, holidays=None):
    # approximate: business days = Mon-Fri (CME holidays not modeled; deviations flagged)
    d = d0
    n = 0
    while n < 2:
        d -= timedelta(days=1)
        if d.weekday() < 5:
            n += 1
    return d

expiry_rule = []
for p in panel:
    ltd = date.fromisoformat(p["lastTradeDate_raw"])
    y, m = map(int, p["delivery_month"].split("-"))
    tw = third_wednesday(y, m)
    exp2 = two_business_days_before(tw)
    expiry_rule.append({
        "ls": p["localSymbol"], "delivery_month": p["delivery_month"],
        "lastTradeDate": p["lastTradeDate_raw"],
        "third_wednesday": tw.isoformat(),
        "matches_2busday_before_3rd_wed": ltd == exp2,
        "diff_days_if_not": (ltd - exp2).days if ltd != exp2 else 0,
    })

out = {
    "schema": "FUTURES-BEHAVIOR-10SYMS-PREP/6A_descriptives@1",
    "generated_utc": "2026-10-02",
    "script": "analysis/6A_descriptives.py",
    "raw_source": ("~/.my-quantitative-data/futures-10syms-v1/raw/ 6A_*_TRADES_1day_6Y.json "
                   "(+BID/ASK_1day_1Y, +TRADES_1hour_30D), useRTH=true -> 08:30-16:00 CT bars only"),
    "tick": TICK, "multiplier": MULT,
    "contract_panel": panel,
    "quarterly_vs_serial": qser,
    "quote_convention_check": quote_check,
    "declared_rule_rolls_literal_incl_serials": rolls_literal,
    "declared_rule_rolls_quarterly_chain": rolls_quarterly,
    "serial_gap_executability": serial_gaps,
    "liquidity_migration_quarterly": migration,
    "literal_rule_serial_front_windows": serial_windows,
    "front_chain_quarterly_stats": q_chain_stats,
    "single_contract_long_refs": single_refs,
    "worst_days_front_scale_era": [worst_best[0], worst_best[1]] if worst_best else [],
    "best_days_front_scale_era": worst_best[-2:] if worst_best else [],
    "trend_persistence": trend_persist,
    "large_move_frequency_prior126": big_moves,
    "overnight_hidden_session_gap": overnight,
    "bid_ask_1y": bidask,
    "bid_ask_serial_fronts": serial_front_ba,
    "hourly_rth_profile_30d": hourly_profile,
    "expiry_rule_check": expiry_rule,
}
with open(OUT, "w") as f:
    json.dump(out, f, indent=1)
print("wrote", OUT)
for k in ["quarterly_vs_serial", "quote_convention_check", "declared_rule_rolls_quarterly_chain",
          "serial_gap_executability", "liquidity_migration_quarterly",
          "literal_rule_serial_front_windows", "front_chain_quarterly_stats",
          "single_contract_long_refs", "trend_persistence", "large_move_frequency_prior126",
          "overnight_hidden_session_gap", "bid_ask_1y", "bid_ask_serial_fronts",
          "hourly_rth_profile_30d"]:
    print("=== " + k + " ===")
    print(json.dumps(out[k], indent=1))
