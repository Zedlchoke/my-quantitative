#!/usr/bin/env python
"""GC_descriptives.py — lane SYMBOL-DOSSIER-GC, task FUTURES-BEHAVIOR-10SYMS-PREP-20261002.

Descriptive statistics ONLY for COMEX Gold futures (GC), computed from the
legal read-only raw snapshot of FUTURES-DATA-10SYMS-V1 at
~/.my-quantitative-data/futures-10syms-v1/raw/ (files GC_*).

Hard constraints honored:
  - No PnL, no equity curves, no Sharpe/performance metrics, no parameter
    selection, no return-based event studies. Descriptive distribution /
    window statistics only.
  - Any activation/threshold definition uses STRICT PAST/ROLLING windows
    (trailing window of PRIOR observations only; never ex-post labels).
  - Conventions fixed a priori and disclosed (not tuned):
      roll rule  = data lane's declared rule (hold until last session BEFORE
                   day-1 of the held contract's delivery month, roll to the
                   next listed contract at that session close). On this raw
                   set the serial (non-GJMQVZ) months of 2025-09..2026-09
                   (GCX5, GCF6, GCH6, GCK6, GCN6, GCU6) were NOT fetched, so
                   the declared rule is NOT executable for those rolls; the
                   executable approximation used here rolls to the NEXT
                   AVAILABLE contract in the dataset (a cycle skip). Every
                   such deviation is listed in output.roll_analysis.serial_gaps.
      returns    = within-contract daily log returns; on a roll date the
                   return belongs to the OLD contract (old_t vs old_{t-1});
                   the new contract's segment starts the NEXT session, so no
                   synthetic stitching jump ever enters the return series.
                   Roll-day adjacent-contract close gaps are reported
                   separately as raw gaps (description, not a cost model).
      deep bars  = daily bars with v==0 and o==h==l==c are settlement-derived
                   (FINAL_REPORT FUTURES-DATA-10SYMS-V1); they are used ONLY
                   for long-horizon reference/curve descriptives and are
                   never treated as tradable prices.
      multiplier: multiplier=100, minTick=0.1 -> tick value USD 10.00
                   (S1_IDENTITY.json GC, 22/22 resolved contracts uniform).

Output: analysis/GC_descriptives.json (same directory as this script).
Run: /Users/hoangminhlong/my-quantitative/.venv/bin/python GC_descriptives.py
"""

import json
import math
import os
from datetime import datetime, timezone
from statistics import median

RAW = os.path.expanduser("~/.my-quantitative-data/futures-10syms-v1/raw")
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "GC_descriptives.json")

MULT = 100.0
MIN_TICK = 0.1
TICK_USD = MULT * MIN_TICK  # 10.00 USD per tick per contract

MONTH_CODE = {"F": 1, "G": 2, "H": 3, "J": 4, "K": 5, "M": 6,
              "N": 7, "Q": 8, "U": 9, "V": 10, "X": 11, "Z": 12}
CYCLE = {2, 4, 6, 8, 10, 12}  # GC active cycle G,J,M,Q,V,Z


# ---------------------------------------------------------------- loading
def load_contracts():
    """Return {localSymbol: {conId, delivery (yyyymm), last_trade (yyyymmdd),
    bars: {date: bar}, ordered_dates: [dates]}} from GC daily TRADES 6Y files."""
    import glob
    out = {}
    for path in sorted(glob.glob(os.path.join(RAW, "GC_*_TRADES_1day_6Y.json"))):
        with open(path) as f:
            d = json.load(f)
        ls = d["localSymbol"]
        mc, yc = ls[2], int(ls[3])
        delivery = f"{2020 + yc:04d}{MONTH_CODE[mc]:02d}"
        bars = {b["t"]: b for b in d["bars"]}
        out[ls] = {
            "conId": d["conId"],
            "delivery": delivery,
            "last_trade": str(d["expiry_month"]),
            "bars": bars,
            "ordered_dates": sorted(bars),
            "timeZoneId": d.get("timeZoneId"),
            "useRTH": d.get("useRTH"),
            "n_rows": d["n_rows"],
        }
    return out


def load_side(what):
    """BID/ASK 1Y daily files -> {localSymbol: {date: close}}."""
    import glob
    out = {}
    for path in sorted(glob.glob(os.path.join(RAW, f"GC_*_{what}_1day_1Y.json"))):
        with open(path) as f:
            d = json.load(f)
        out[d["localSymbol"]] = {b["t"]: b["c"] for b in d["bars"]}
    return out


def load_hourly():
    import glob
    per_contract, seen = {}, set()
    for path in sorted(glob.glob(os.path.join(RAW, "GC_*_TRADES_1hour_30D.json"))):
        with open(path) as f:
            d = json.load(f)
        ls = d["localSymbol"]
        keep = []
        for b in d["bars"]:
            key = (b["t"], d["conId"])
            if key in seen:
                continue
            seen.add(key)
            keep.append(b)
        per_contract[ls] = {
            "n": len(keep),
            "first": keep[0]["t"] if keep else None,
            "last": keep[-1]["t"] if keep else None,
            "bars": keep,
        }
    return per_contract


# ---------------------------------------------------------------- helpers
def pct(vals, q):
    if not vals:
        return None
    s = sorted(vals)
    if len(s) == 1:
        return s[0]
    pos = q * (len(s) - 1)
    lo, hi = int(math.floor(pos)), int(math.ceil(pos))
    if lo == hi:
        return s[lo]
    return s[lo] + (s[hi] - s[lo]) * (pos - lo)


def mean(vals):
    return sum(vals) / len(vals) if vals else None


def stdev(vals):
    if len(vals) < 2:
        return None
    m = mean(vals)
    return math.sqrt(sum((x - m) ** 2 for x in vals) / (len(vals) - 1))


def autocorr(vals, lag):
    if len(vals) <= lag + 2:
        return None
    m = mean(vals)
    num = sum((vals[i] - m) * (vals[i + lag] - m) for i in range(len(vals) - lag))
    den = sum((x - m) ** 2 for x in vals)
    return num / den if den else None


def r1(x):
    if x is None:
        return None
    return round(x, 6)


def r2(x):
    if x is None:
        return None
    return round(x, 2)


def ym(datestr):
    return datestr[:7].replace("-", "")


def next_ym(yyyymm):
    y, m = int(yyyymm[:4]), int(yyyymm[4:])
    return f"{y + (m == 12):04d}{(m % 12) + 1:02d}"


# ---------------------------------------------------------------- panel
def panel(contracts):
    rows = []
    for ls in sorted(contracts, key=lambda s: contracts[s]["delivery"]):
        c = contracts[ls]
        dates = c["ordered_dates"]
        real = [t for t in dates if c["bars"][t]["v"] > 0]
        flat = [t for t in dates
                if c["bars"][t]["v"] == 0 and c["bars"][t]["o"] == c["bars"][t]["h"]
                == c["bars"][t]["l"] == c["bars"][t]["c"]]
        tot_v = sum(c["bars"][t]["v"] for t in dates)
        v_last60 = sum(c["bars"][t]["v"] for t in dates[-60:])
        rows.append({
            "localSymbol": ls,
            "conId": c["conId"],
            "delivery_yyyymm": c["delivery"],
            "last_trade_date": c["last_trade"],
            "is_cycle_month": int(c["delivery"][4:]) in CYCLE,
            "n_bars": len(dates),
            "first": dates[0],
            "last": dates[-1],
            "flat_zero_vol_rows": len(flat),
            "flat_share_pct": r2(100.0 * len(flat) / len(dates)) if dates else None,
            "first_real_vol": real[0] if real else None,
            "last_real_vol": real[-1] if real else None,
            "n_real_vol_rows": len(real),
            "total_volume": tot_v,
            "vol_share_last60_rows_pct": r2(100.0 * v_last60 / tot_v) if tot_v else None,
        })
    return rows


# ---------------------------------------------------------------- rolls
def roll_analysis(contracts):
    """Declared-rule rolls between dataset contracts ordered by delivery."""
    order = sorted(contracts, key=lambda s: contracts[s]["delivery"])
    rolls, serial_gaps = [], []
    for a, b in zip(order, order[1:]):
        ca, cb = contracts[a], contracts[b]
        da, db_ = ca["delivery"], cb["delivery"]
        # declared roll session for A: last bar strictly before day-1 of A's delivery month
        cand = [t for t in ca["ordered_dates"] if t[:7].replace("-", "") < da]
        roll_t = cand[-1] if cand else None
        # serial gap: calendar-next delivery month after A absent from dataset
        nxt = next_ym(da)
        if nxt != db_:
            serial_gaps.append({
                "after": a, "delivery": da,
                "declared_next_delivery_yyyymm": nxt,
                "missing_delivery_yyyymm": nxt,
                "fallback_in_dataset": b,
                "note": "declared next-listed roll NOT executable on raw set; approximation rolls to next available (cycle skip)",
            })
        entry = {
            "old": a, "old_delivery": da,
            "new": b, "new_delivery": db_,
            "declared_roll_session": roll_t,
            "old_close_at_roll": ca["bars"][roll_t]["c"] if roll_t else None,
        }
        # Pseudo-roll detection: if the computed session is the contract's LAST
        # available bar while its delivery month has not yet begun, the true
        # declared roll session lies in the future; the row is a curve snapshot.
        if roll_t is not None and roll_t == ca["ordered_dates"][-1] and da > roll_t[:7].replace("-", ""):
            entry["roll_session_status"] = "PSEUDO_curve_snapshot_not_yet_occurred"
        if roll_t:
            nb = cb["bars"].get(roll_t)
            used_t = roll_t
            if nb is None:
                idx = cb["ordered_dates"]
                near = [t for t in idx if abs((datetime.strptime(t, "%Y-%m-%d")
                       - datetime.strptime(roll_t, "%Y-%m-%d")).days) <= 5]
                if near:
                    used_t = min(near, key=lambda t: abs((datetime.strptime(t, "%Y-%m-%d")
                              - datetime.strptime(roll_t, "%Y-%m-%d")).days))
                    nb = cb["bars"][used_t]
            if nb is not None:
                gap = nb["c"] - entry["old_close_at_roll"]
                entry.update({
                    "new_close_used_session": used_t,
                    "new_close": nb["c"],
                    "gap_usd_per_oz": r2(gap),
                    "gap_ticks": r1(gap / MIN_TICK),
                    "gap_usd_per_contract": r2(gap * MULT),
                })
            else:
                entry["gap_usd_per_oz"] = None
        rolls.append(entry)
    return rolls, serial_gaps


def migration(contracts, rolls, window_before=10, window_after=3):
    """Volume migration front->next around each declared roll session."""
    out = []
    order = {c: i for i, c in enumerate(sorted(contracts,
            key=lambda s: contracts[s]["delivery"]))}
    for r in rolls:
        a, b, rt = r["old"], r["new"], r["declared_roll_session"]
        if rt is None:
            continue
        ca, cb = contracts[a], contracts[b]
        ad = ca["ordered_dates"]
        i = ad.index(rt)
        prof = []
        for k in range(-window_before, window_after + 1):
            j = i + k
            if j < 0 or j >= len(ad):
                continue
            t = ad[j]
            va = ca["bars"][t]["v"]
            vb = cb["bars"].get(t, {}).get("v", None)
            if vb is None:
                bt = min(cb["ordered_dates"], key=lambda s: abs((
                     datetime.strptime(s, "%Y-%m-%d") - datetime.strptime(t, "%Y-%m-%d")).days)) \
                     if cb["ordered_dates"] else None
                vb = cb["bars"].get(bt, {}).get("v") if bt else None
            prof.append({
                "session_offset": k, "date": t,
                "v_old": va, "v_new": vb,
                "share_new": r2(vb / (va + vb)) if (va is not None and vb is not None
                              and va + vb > 0) else None,
            })
        first_flip = None
        for p in prof:
            if p["v_old"] is not None and p["v_new"] is not None \
               and p["v_new"] > p["v_old"] and p["v_old"] + p["v_new"] > 0:
                first_flip = {"date": p["date"], "offset": p["session_offset"]}
                break
        any_real = any((p["v_new"] or 0) + (p["v_old"] or 0) > 0 for p in prof)
        out.append({
            "old": a, "new": b, "roll_session": rt,
            "any_real_volume_in_window": any_real,
            "first_session_new_vol_exceeds_old": first_flip,
            "profile": prof,
        })
    return out


# ---------------------------------------------------------------- chains
def build_front_chain(contracts):
    """Executable approximation of the declared rule on this dataset:
    at each date, hold the dataset contract with the smallest delivery month
    strictly after the date's month. Returns [(date, localSymbol, close, v)]."""
    order = sorted(contracts, key=lambda s: contracts[s]["delivery"])
    all_dates = sorted({t for ls in order for t in contracts[ls]["ordered_dates"]})
    chain = []
    for t in all_dates:
        tym = t[:7].replace("-", "")
        for ls in order:
            if contracts[ls]["delivery"] > tym:
                b = contracts[ls]["bars"].get(t)
                if b is not None:
                    chain.append((t, ls, b["c"], b["v"]))
                break
    return chain


def chain_returns(chain):
    """Within-contract log returns; roll-date return belongs to OLD contract."""
    rets, meta = [], []
    for i in range(1, len(chain)):
        t0, ls0, c0, _ = chain[i - 1]
        t1, ls1, c1, _ = chain[i]
        if ls1 != ls0:
            meta.append({"roll_date": t1, "from": ls0, "to": ls1})
            continue
        if c0 and c1:
            rets.append({"date": t1, "sym": ls1, "r": math.log(c1 / c0)})
    return rets, meta


def describe_returns(rets, label):
    rs = [x["r"] for x in rets]
    if not rs:
        return {"label": label, "n": 0}
    out = {
        "label": label,
        "n": len(rs),
        "first": rets[0]["date"],
        "last": rets[-1]["date"],
        "mean_daily": r1(mean(rs)),
        "std_daily": r1(stdev(rs)),
        "ann_vol_pct": r2(100 * stdev(rs) * math.sqrt(252)) if stdev(rs) else None,
        "min": r1(min(rs)),
        "max": r1(max(rs)),
        "q05": r1(pct(rs, 0.05)),
        "q50": r1(pct(rs, 0.50)),
        "q95": r1(pct(rs, 0.95)),
        "share_pos_days": r2(100.0 * sum(1 for x in rs if x > 0) / len(rs)),
        "autocorr_r_lag1": r1(autocorr(rs, 1)),
        "autocorr_absr_lag1": r1(autocorr([abs(x) for x in rs], 1)),
        "autocorr_absr_lag5": r1(autocorr([abs(x) for x in rs], 5)),
    }
    by_year = {}
    for x in rets:
        by_year.setdefault(x["date"][:4], []).append(x["r"])
    imin = min(range(len(rs)), key=lambda i: rs[i])
    imax = max(range(len(rs)), key=lambda i: rs[i])
    out["min_date"] = rets[imin]["date"]
    out["max_date"] = rets[imax]["date"]
    out["by_year"] = {y: {"n": len(v), "mean": r1(mean(v)), "std": r1(stdev(v)),
                          "ann_vol_pct": r2(100 * stdev(v) * math.sqrt(252)) if stdev(v) else None,
                          "min": r1(min(v)), "max": r1(max(v))}
                      for y, v in sorted(by_year.items())}
    return out


def rolling_vol(rets, w):
    out = []
    for i in range(w, len(rets) + 1):
        win = [x["r"] for x in rets[i - w:i]]
        s = stdev(win)
        if s is not None:
            out.append({"date": rets[i - 1]["date"], "vol": s})
    return out


def past_threshold_large_moves(rets, w=126, q=0.95):
    """Days whose |r| exceeds the q-quantile of |r| over the STRICTLY PRIOR w
    sessions. Description only — thresholds never use same-day or future data."""
    evaluated, above = 0, 0
    hits = []
    for i in range(w, len(rets)):
        prior = sorted(abs(x["r"]) for x in rets[i - w:i])
        thr = pct(prior, q)
        if thr is None or thr <= 0:
            continue
        evaluated += 1
        if abs(rets[i]["r"]) > thr:
            above += 1
            hits.append({"date": rets[i]["date"], "r": r1(rets[i]["r"]), "thr": r1(thr)})
    return {
        "window_prior_sessions": w, "quantile": q,
        "n_evaluated": evaluated, "n_above": above,
        "share_above_pct": r2(100.0 * above / evaluated) if evaluated else None,
        "hit_dates": [h["date"] for h in hits][:50],
    }


def seasonal(rets):
    mon, wed = {}, {}
    for x in rets:
        d = datetime.strptime(x["date"], "%Y-%m-%d")
        mon.setdefault(d.month, []).append(abs(x["r"]))
        wed.setdefault(d.weekday(), []).append(abs(x["r"]))
    MN = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    WD = ["Mon", "Tue", "Wed", "Thu", "Fri"]
    return {
        "mean_abs_ret_by_calendar_month": {MN[k - 1]: {"n": len(v), "mean_abs": r1(mean(v))}
                                           for k, v in sorted(mon.items())},
        "mean_abs_ret_by_weekday": {WD[k]: {"n": len(v), "mean_abs": r1(mean(v))}
                                    for k, v in sorted(wed.items())},
        "note": "description only; samples tiny per bucket; no signal claimed",
    }


def trend_share(rets_with_dates, w):
    """Share of sessions whose close-to-close basis vs trailing-w-session mean
    return is positive (strict past window). Description only."""
    pos = tot = 0
    series = []
    for i in range(w, len(rets_with_dates)):
        prior = [x["r"] for x in rets_with_dates[i - w:i]]
        m = mean(prior)
        tot += 1
        if rets_with_dates[i]["r"] > 0 and m > 0:
            pos += 1
        elif rets_with_dates[i]["r"] < 0 and m < 0:
            pos += 1
        series.append(rets_with_dates[i]["date"])
    return {"window": w, "n_evaluated": tot,
            "pct_days_ret_sign_matches_prior_w_mean_sign": r2(100.0 * pos / tot) if tot else None,
            "first_evaluated": series[0] if series else None}


# ---------------------------------------------------------------- term structure
def term_structure(contracts, pairs):
    out = []
    for a, b in pairs:
        ca, cb = contracts.get(a), contracts.get(b)
        if not ca or not cb:
            continue
        common = sorted(set(ca["bars"]) & set(cb["bars"]))
        if len(common) < 30:
            continue
        spreads = [ca["bars"][t]["c"] - cb["bars"][t]["c"] for t in common]
        out.append({
            "near": a, "far": b,
            "near_delivery": ca["delivery"], "far_delivery": cb["delivery"],
            "n_overlap_sessions": len(common),
            "first": common[0], "last": common[-1],
            "median_spread_usd_per_oz": r2(median(spreads)),
            "mean_spread_usd_per_oz": r2(mean(spreads)),
            "q05": r2(pct(spreads, 0.05)), "q95": r2(pct(spreads, 0.95)),
            "share_near_below_far_pct": r2(100.0 * sum(1 for s in spreads if s < 0) / len(spreads)),
            "note": "settlement-derived deep bars included; curve-shape description only",
        })
    return out


# ---------------------------------------------------------------- intraday
def hourly_stats(per_contract):
    rows, all_bars = [], []
    for ls, c in sorted(per_contract.items(),
                        key=lambda kv: (kv[1]["first"] or "")):
        rows.append({"localSymbol": ls, "n_bars": c["n"],
                     "first": c["first"], "last": c["last"]})
        all_bars.extend((ls, b) for b in c["bars"])
    byhour = {}
    for ls, b in all_bars:
        hhmm = b["t"][11:16]
        h = hhmm[:2]
        byhour.setdefault(hhmm if hhmm == "09:30" else h, []).append(b)
    prof = {}
    for k, bs in sorted(byhour.items()):
        vols = [b["v"] for b in bs if b["v"] and b["v"] > 0]
        rngs = [(b["h"] - b["l"]) / b["c"] * 100.0 for b in bs if b["c"]]
        prof[k] = {
            "n_bars": len(bs),
            "median_volume": median(vols) if vols else 0,
            "sum_volume": sum(b["v"] for b in bs),
            "volume_share_pct": None,  # filled below
            "median_range_pct": r2(median(rngs)) if rngs else None,
        }
    tot = sum(p["sum_volume"] for p in prof.values())
    for p in prof.values():
        p["volume_share_pct"] = r2(100.0 * p["sum_volume"] / tot) if tot else None
    return {
        "coverage_per_contract": rows,
        "by_session_clock_et": prof,
        "total_bars": len(all_bars),
        "distinct_sessions": len({b["t"][:10] for _, b in all_bars}),
        "caveat": "useRTH=True: bars cover the US RTH window only (first label "
                  "09:30 ET to last label 16:00 ET); COMEX electronic session "
                  "18:00-09:30 ET (Asia/London) is NOT in these files",
    }


# ---------------------------------------------------------------- bid/ask
def bidask(bid, ask):
    out = []
    for ls in sorted(bid, key=lambda s: s):
        if ls not in ask:
            continue
        common = sorted(set(bid[ls]) & set(ask[ls]))
        if not common:
            continue
        sp = [ask[ls][t] - bid[ls][t] for t in common]
        crossed = sum(1 for s in sp if s < 0)
        row = {
            "localSymbol": ls, "n_days": len(common),
            "first": common[0], "last": common[-1],
            "median_spread_usd": r2(median(sp)),
            "median_spread_ticks": r1(median(sp) / MIN_TICK),
            "p90_spread_usd": r2(pct(sp, 0.9)),
            "min_spread_usd": r2(min(sp)),
            "crossed_days": crossed,
        }
        last20 = sp[-20:]
        row["median_spread_ticks_last20d"] = r1(median(last20) / MIN_TICK) if last20 else None
        out.append(row)
    return out


# ---------------------------------------------------------------- main
def main():
    contracts = load_contracts()
    bid, ask = load_side("BID"), load_side("ASK")
    hourly = load_hourly()

    pan = panel(contracts)
    rolls, serial_gaps = roll_analysis(contracts)
    mig = migration(contracts, rolls)

    chain = build_front_chain(contracts)
    rets, roll_dates_used = chain_returns(chain)

    # real-volume continuous sub-era: first date such that every later session v>0
    real_start = None
    for i, (t, ls, c, v) in enumerate(chain):
        if all(x[3] > 0 for x in chain[i:]):
            real_start = t
            break
    real_rets = [x for x in rets if x["date"] >= real_start] if real_start else []

    full_desc = describe_returns(rets, "front_chain_full_depth_2019-2026_settlement_derived_reference")
    real_desc = describe_returns(real_rets, "front_chain_real_volume_subera")

    vol21 = rolling_vol(real_rets, 21)
    vol63 = rolling_vol(real_rets, 63)

    # long-horizon single-contract references (no stitching)
    refs = {}
    for ls in ("GCZ5", "GCZ6"):
        cl = [(t, contracts[ls]["bars"][t]["c"]) for t in contracts[ls]["ordered_dates"]]
        rr = [{"date": t1, "sym": ls, "r": math.log(c1 / c0)}
              for (t0, c0), (t1, c1) in zip(cl, cl[1:])]
        refs[ls] = describe_returns(rr, f"{ls}_single_contract_full_life")

    ts = term_structure(contracts, [
        ("GCV5", "GCZ5"), ("GCZ5", "GCG6"), ("GCG6", "GCJ6"), ("GCJ6", "GCM6"),
        ("GCM6", "GCQ6"), ("GCQ6", "GCV6"), ("GCV6", "GCX6"), ("GCX6", "GCZ6"),
        ("GCZ5", "GCZ6"), ("GCM6", "GCZ6"), ("GCZ6", "GCZ7"), ("GCM7", "GCZ7"),
        ("GCV6", "GCZ6"),
    ])

    closes_all = [b["c"] for c in contracts.values() for b in c["bars"].values()]
    result = {
        "meta": {
            "script": os.path.abspath(__file__),
            "run_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "raw_root": RAW,
            "input_files": {"daily_trades_6Y": len(contracts),
                            "bid_1Y": len(bid), "ask_1Y": len(ask),
                            "hourly_30D": len(hourly)},
            "constraints": "descriptive only; no PnL/event-study/sweeps; "
                           "strict past windows for thresholds",
            "conventions": {"roll_rule": "data lane declared rule (see docstring); "
                                         "serial-month gaps approximated by next available contract",
                            "returns": "within-contract daily log returns; roll-date return on old contract",
                            "tick": {"multiplier": MULT, "minTick": MIN_TICK,
                                     "tick_usd": TICK_USD}},
        },
        "quote_convention_check": {
            "min_close_usd_per_oz": r2(min(closes_all)),
            "max_close_usd_per_oz": r2(max(closes_all)),
            "expected": "USD per troy ounce; 2019-2026 gold range ~1000-4600",
            "verdict": "PASS-scale-consistent" if 500 < min(closes_all) and max(closes_all) < 10000 else "CHECK",
        },
        "panel": pan,
        "real_volume_chain_start": real_start,
        "roll_analysis": {"declared_rule": "hold until last session before day-1 of delivery month; roll to next listed at that close",
                          "rolls": rolls, "serial_gaps": serial_gaps,
                          "note": "gaps are raw adjacent-closes, descriptive only, NOT_COMPUTED as tradable cost",
                          "volume_scale_caveat": "vendor-recorded daily volume is full-scale (~30k-260k/day) for "
                                                 "G/J/M/Q/Z-month contracts during their front windows but 1-2 orders "
                                                 "thinner for the V-month contracts (GCV5 front Aug-Sep 2025 median ~3.0k, "
                                                 "GCV6 front Aug-Sep 2026 median ~3.2k) and deferred months; hourly sums "
                                                 "match dailies where checked (GCV6 2026-08-20: 6068=6068), so the "
                                                 "thinness is per-contract vendor recording, not aggregation. Use volume "
                                                 "only for RELATIVE migration timing, never absolute liquidity claims."},
        "volume_migration": mig,
        "front_chain": {
            "construction": "dataset executable approximation (see docstring); "
                            f"{len(roll_dates_used)} rolls used",
            "roll_dates": roll_dates_used,
            "n_sessions": len(chain),
            "first": chain[0][0], "last": chain[-1][0],
            "real_volume_subera_start": real_start,
            "returns_full_depth": full_desc,
            "returns_real_volume_subera": real_desc,
            "rolling_vol_21d": {"n": len(vol21),
                                "latest_date": vol21[-1]["date"] if vol21 else None,
                                "latest_ann_pct": r2(100 * vol21[-1]["vol"] * math.sqrt(252)) if vol21 else None,
                                "mean_ann_pct": r2(100 * mean([v["vol"] for v in vol21]) * math.sqrt(252)) if vol21 else None,
                                "max_ann_pct": r2(100 * max(v["vol"] for v in vol21) * math.sqrt(252)) if vol21 else None},
            "rolling_vol_63d": {"n": len(vol63),
                                "latest_ann_pct": r2(100 * vol63[-1]["vol"] * math.sqrt(252)) if vol63 else None},
            "large_move_days_past126q95": past_threshold_large_moves(real_rets, 126, 0.95),
            "seasonal": seasonal(real_rets),
            "trend_share_50d_realera": trend_share(real_rets, 50),
            "trend_share_200d_GMZ5_long": None,
        },
        "long_horizon_single_contract_refs": refs,
        "term_structure_pairs": ts,
        "intraday_hourly_rth_only": hourly_stats(hourly),
        "bid_ask_daily_spreads": {
            "note": "BID/ASK daily closes are NOT synchronous quotes; descriptive only, not executable spread",
            "contracts": bidask(bid, ask),
        },
    }

    # long-horizon trend share on GCZ5 (200d) — needs its own return list
    cl = [(t, contracts["GCZ5"]["bars"][t]["c"]) for t in contracts["GCZ5"]["ordered_dates"]]
    rr = [{"date": t1, "sym": "GCZ5", "r": math.log(c1 / c0)}
          for (t0, c0), (t1, c1) in zip(cl, cl[1:])]
    result["front_chain"]["trend_share_200d_GMZ5_long"] = trend_share(rr, 200)

    with open(OUT, "w") as f:
        json.dump(result, f, indent=1)
    print("wrote", OUT)
    print("panel contracts:", len(pan))
    print("chain sessions:", len(chain), "real-era start:", real_start)
    print("rolls:", len(rolls), "serial gaps:", len(serial_gaps))


if __name__ == "__main__":
    main()
