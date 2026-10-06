#!/usr/bin/env python
"""6J_descriptives.py — lane SYMBOL-DOSSIER-6J, task FUTURES-BEHAVIOR-10SYMS-PREP-20261002.

Descriptive statistics ONLY for CME Japanese Yen futures (6J), computed from the
legal read-only raw snapshot of FUTURES-DATA-10SYMS-V1 at
~/.my-quantitative-data/futures-10syms-v1/raw/ (files 6J_*).

Hard constraints honored:
  - No PnL, no equity curves, no Sharpe/performance metrics, no parameter
    selection, no return-based event studies. Descriptive distribution /
    window statistics only. (Intervention-day rows are single-day price
    descriptions, not event-study returns vs a benchmark.)
  - Any activation/threshold definition uses STRICT PAST/ROLLING windows
    (trailing window of PRIOR observations only; never ex-post labels).
  - Conventions fixed a priori and disclosed (not tuned):
      roll rule  = data lane's declared rule (hold until last session BEFORE
                   day-1 of the held contract's delivery month, roll to the
                   next listed contract at that session close).
                   TWO executability defects measured on this raw set:
                   (a) serial months with delivery 2025-10..2026-08
                       (6JV5,6JX5,6JF6,6JG6,6JJ6,6JK6,6JN6,6JQ6) were NOT
                       fetched -> declared rule NOT executable for rolls in
                       2025-09..2026-08 on this dataset;
                   (b) from 2026-08-31 the declared next-listed contracts ARE
                       in the raw set but are near-dead serials (6JV6 Oct-26,
                       6JX6 Nov-26: tens of lots/day vs ~40k-120k on the
                       quarterly 6JZ6). The economically liquid chain is
                       quarterly (HMUZ) -> quarterly.
                   Main statistics below therefore use the QUARTERLY LIQUIDITY
                   CHAIN (roll quarterly->next quarterly at the declared
                   session), which during serial calendar months sits 1-2
                   months out — disclosed, and it matches where the volume
                   actually trades.
      returns    = within-contract daily log returns; on a roll date the
                   return belongs to the OLD contract; the new contract's
                   segment starts the NEXT session, so no synthetic stitching
                   jump ever enters the return series. Roll-day adjacent-
                   contract close gaps are reported separately as raw gaps.
      deep bars  = daily bars with v==0 and o==h==l==c are settlement-derived
                   (FINAL_REPORT FUTURES-DATA-10SYMS-V1); used ONLY for
                   long-horizon reference/curve descriptives, never as
                   tradable/fill prices.
      quote      = USD per JPY (JPY/USD convention; 6J price = 1 / USDJPY),
                   multiplier 12,500,000 JPY, minTick 5e-7 USD/JPY
                   -> tick value USD 6.25 (S1_IDENTITY.json 6J, uniform on all
                   resolved contracts; S9 check 6 PASS).

Output: analysis/6J_descriptives.json (same directory as this script).
Run: /Users/hoangminhlong/my-quantitative/.venv/bin/python 6J_descriptives.py
"""

import glob
import json
import math
import os
from datetime import datetime, timezone
from statistics import median

RAW = os.path.expanduser("~/.my-quantitative-data/futures-10syms-v1/raw")
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "6J_descriptives.json")

MULT = 12_500_000.0        # JPY per contract
MIN_TICK = 5e-07           # USD per JPY
TICK_USD = MULT * MIN_TICK  # 6.25 USD per tick per contract

MONTH_CODE = {"F": 1, "G": 2, "H": 3, "J": 4, "K": 5, "M": 6,
              "N": 7, "Q": 8, "U": 9, "V": 10, "X": 11, "Z": 12}
QUARTERLY = {3, 6, 9, 12}  # HMUZ cycle for 6J


# ---------------------------------------------------------------- loading
def load_contracts():
    """6J daily TRADES 6Y files -> {localSymbol: {...}} (delivery yyyymm)."""
    out = {}
    for path in sorted(glob.glob(os.path.join(RAW, "6J_*_TRADES_1day_6Y.json"))):
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
    out = {}
    for path in sorted(glob.glob(os.path.join(RAW, f"6J_*_{what}_1day_1Y.json"))):
        with open(path) as f:
            d = json.load(f)
        out[d["localSymbol"]] = {b["t"]: b["c"] for b in d["bars"]}
    return out


def load_hourly():
    per_contract, seen = {}, set()
    for path in sorted(glob.glob(os.path.join(RAW, "6J_*_TRADES_1hour_30D.json"))):
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
    return None if x is None else round(x, 6)


def r2(x):
    return None if x is None else round(x, 2)


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
            "is_quarterly_hmuz": int(c["delivery"][4:]) in QUARTERLY,
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
            "last5_volumes": [c["bars"][t]["v"] for t in dates[-5:]],
        })
    return rows


# ---------------------------------------------------------------- serial coverage
def serial_coverage(contracts, fetch_month="202610"):
    """Which listed serial months are missing from the raw snapshot?
    Exchange listing (S1 active_chain 2026-10-02): ~24 consecutive monthly
    contracts + HMUZ quarterlies out ~5y -> every calendar month within the
    raw span has a listed serial/quarterly counterpart. Report absence."""
    have = {c["delivery"]: ls for ls, c in contracts.items()}
    missing = []
    for y in (2025, 2026):
        for m in range(1, 13):
            d = f"{y}{m:02d}"
            if d >= fetch_month or d < "202510":
                continue
            if d not in have:
                mc = {1: "F", 2: "G", 3: "H", 4: "J", 5: "K", 6: "M",
                      7: "N", 8: "Q", 9: "U", 10: "V", 11: "X", 12: "Z"}[m]
                missing.append({
                    "delivery_yyyymm": d,
                    "expected_localSymbol": f"6J{mc}{str(y)[3]}",
                    "note": "listed by CME (monthly listings) but NOT fetched into raw snapshot; unresolvable post-hoc (expired-secdef wall ~1y)",
                })
    present_serials = [r for r in panel_cache
                       if not r["is_quarterly_hmuz"] and r["delivery_yyyymm"] >= "202609"]
    return {"missing_serial_delivery_months": missing,
            "present_serial_contracts_recent": [
                {k: r[k] for k in ("localSymbol", "delivery_yyyymm", "total_volume",
                                   "n_real_vol_rows", "last5_volumes")}
                for r in present_serials]}


# ---------------------------------------------------------------- rolls
def roll_analysis(contracts):
    """Declared-rule rolls between dataset contracts ordered by delivery."""
    order = sorted(contracts, key=lambda s: contracts[s]["delivery"])
    rolls, serial_gaps = [], []
    for a, b in zip(order, order[1:]):
        ca, cb = contracts[a], contracts[b]
        da, db_ = ca["delivery"], cb["delivery"]
        cand = [t for t in ca["ordered_dates"] if ym(t) < da]
        roll_t = cand[-1] if cand else None
        nxt = next_ym(da)
        gap_flag = None
        if nxt != db_:
            gap_flag = "declared next-listed roll NOT executable on raw set (serial missing); approximation rolls to next available"
            serial_gaps.append({
                "after": a, "delivery": da,
                "declared_next_delivery_yyyymm": nxt,
                "missing_delivery_yyyymm": nxt,
                "fallback_in_dataset": b,
            })
        entry = {
            "old": a, "old_delivery": da, "old_is_quarterly": int(da[4:]) in QUARTERLY,
            "new": b, "new_delivery": db_, "new_is_quarterly": int(db_[4:]) in QUARTERLY,
            "declared_roll_session": roll_t,
            "old_close_at_roll": ca["bars"][roll_t]["c"] if roll_t else None,
            "serial_gap_flag": gap_flag,
        }
        # Pseudo-roll detection: the computed session is the contract's LAST
        # available bar AND that bar sits at/after the global snapshot end ->
        # the true declared roll session lies in the future (curve snapshot).
        # (Expired contracts' files also end on their roll session because the
        # vendor window was clipped at the delivery month by endDateTime; those
        # rolls DID occur in the past and are not pseudo.)
        global_end = max(t for c_ in contracts.values() for t in c_["ordered_dates"])
        if roll_t is not None and roll_t == ca["ordered_dates"][-1] \
           and da > ym(roll_t) and roll_t >= global_end:
            entry["roll_session_status"] = "PSEUDO_curve_snapshot_not_yet_occurred"
        if roll_t:
            nb = cb["bars"].get(roll_t)
            used_t = roll_t
            if nb is None:
                near = [t for t in cb["ordered_dates"]
                        if abs((datetime.strptime(t, "%Y-%m-%d")
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
                    "gap_usd_per_jpy": r1(gap),
                    "gap_ticks": r1(gap / MIN_TICK),
                    "gap_bps_of_price": r1(1e4 * gap / entry["old_close_at_roll"]),
                    "gap_usd_per_contract": r2(gap * MULT),
                })
        rolls.append(entry)
    return rolls, serial_gaps


def migration(contracts, rolls, window_before=10, window_after=3):
    out = []
    for r in rolls:
        a, b, rt = r["old"], r["new"], r["declared_roll_session"]
        if rt is None:
            continue
        ca, cb = contracts[a], contracts[b]
        ad = ca["ordered_dates"]
        if rt not in ad:
            continue
        i = ad.index(rt)
        prof = []
        for k in range(-window_before, window_after + 1):
            j = i + k
            if j < 0 or j >= len(ad):
                continue
            t = ad[j]
            va = ca["bars"][t]["v"]
            vb = cb["bars"].get(t, {}).get("v", None)
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
        out.append({
            "old": a, "new": b, "roll_session": rt,
            "first_session_new_vol_exceeds_old": first_flip,
            "profile": prof,
        })
    return out


def u6_to_z6_skip(contracts):
    """Where did liquidity actually go after 6JU6's declared roll (2026-08-31)?
    Compare U6, V6 (declared next), X6, Z6 daily volumes Aug-Oct 2026."""
    rows = []
    dates = sorted({t for ls in ("6JU6", "6JV6", "6JX6", "6JZ6")
                    for t in contracts[ls]["ordered_dates"]
                    if "2026-06-01" <= t <= "2026-10-01"})
    for t in dates:
        row = {"date": t}
        for ls in ("6JU6", "6JV6", "6JX6", "6JZ6"):
            row[ls] = contracts[ls]["bars"].get(t, {}).get("v")
        rows.append(row)
    first_z6_gt_u6 = next((r["date"] for r in rows
                           if (r["6JZ6"] or 0) > (r["6JU6"] or 0) > 0), None)
    sep = [r for r in rows if r["date"] >= "2026-09-01"]
    share_z6_sep = None
    tot_sep = sum((r["6JZ6"] or 0) + (r["6JV6"] or 0) + (r["6JX6"] or 0) for r in sep)
    if tot_sep:
        share_z6_sep = r2(100.0 * sum(r["6JZ6"] or 0 for r in sep) / tot_sep)
    return {"daily_volumes_aug_oct_2026": rows,
            "first_session_z6_vol_gt_u6": first_z6_gt_u6,
            "september_2026_volume_share_pct": {
                "6JZ6": share_z6_sep,
                "note": "share of U6+V6+X6+Z6 recorded volume in Sep-2026 held by quarterly Z6 (rest mostly U6 residual early Sep)"}}


# ---------------------------------------------------------------- chains
def build_quarterly_chain(contracts):
    """At each date hold the smallest-delivery HMUZ contract with delivery
    month strictly after the date's month that HAS a bar that date.
    Executable liquid-chain approximation (see docstring)."""
    quarts = [ls for ls in contracts
              if int(contracts[ls]["delivery"][4:]) in QUARTERLY]
    order = sorted(quarts, key=lambda s: contracts[s]["delivery"])
    all_dates = sorted({t for ls in order for t in contracts[ls]["ordered_dates"]})
    chain = []
    for t in all_dates:
        tym = ym(t)
        for ls in order:
            if contracts[ls]["delivery"] > tym:
                b = contracts[ls]["bars"].get(t)
                if b is not None:
                    chain.append((t, ls, b["c"], b["v"]))
                break
    return chain


def chain_returns(chain):
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
    by_year = {}
    for x in rets:
        by_year.setdefault(x["date"][:4], []).append(x["r"])
    imin = min(range(len(rs)), key=lambda i: rs[i])
    imax = max(range(len(rs)), key=lambda i: rs[i])
    return {
        "label": label,
        "n": len(rs),
        "first": rets[0]["date"],
        "last": rets[-1]["date"],
        "mean_daily": r1(mean(rs)),
        "std_daily": r1(stdev(rs)),
        "ann_vol_pct": r2(100 * stdev(rs) * math.sqrt(252)) if stdev(rs) else None,
        "min": r1(min(rs)), "min_date": rets[imin]["date"],
        "max": r1(max(rs)), "max_date": rets[imax]["date"],
        "q05": r1(pct(rs, 0.05)), "q50": r1(pct(rs, 0.50)), "q95": r1(pct(rs, 0.95)),
        "share_pos_days": r2(100.0 * sum(1 for x in rs if x > 0) / len(rs)),
        "autocorr_r_lag1": r1(autocorr(rs, 1)),
        "autocorr_absr_lag1": r1(autocorr([abs(x) for x in rs], 1)),
        "autocorr_absr_lag5": r1(autocorr([abs(x) for x in rs], 5)),
        "by_year": {y: {"n": len(v), "mean": r1(mean(v)), "std": r1(stdev(v)),
                        "ann_vol_pct": r2(100 * stdev(v) * math.sqrt(252)) if stdev(v) else None,
                        "min": r1(min(v)), "max": r1(max(v))}
                    for y, v in sorted(by_year.items())},
    }


def rolling_vol(rets, w):
    out = []
    for i in range(w, len(rets) + 1):
        s = stdev([x["r"] for x in rets[i - w:i]])
        if s is not None:
            out.append({"date": rets[i - 1]["date"], "vol": s})
    return out


def past_threshold_large_moves(rets, w=126, q=0.95):
    evaluated, above, hits = 0, 0, []
    for i in range(w, len(rets)):
        prior = sorted(abs(x["r"]) for x in rets[i - w:i])
        thr = pct(prior, q)
        if thr is None or thr <= 0:
            continue
        evaluated += 1
        if abs(rets[i]["r"]) > thr:
            above += 1
            hits.append({"date": rets[i]["date"], "r": r1(rets[i]["r"])})
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
        "note": "description only; tiny buckets; no signal claimed",
    }


def trend_share(rets, w):
    pos = tot = 0
    for i in range(w, len(rets)):
        prior = [x["r"] for x in rets[i - w:i]]
        m = mean(prior)
        tot += 1
        if (rets[i]["r"] > 0 and m > 0) or (rets[i]["r"] < 0 and m < 0):
            pos += 1
    return {"window": w, "n_evaluated": tot,
            "pct_days_ret_sign_matches_prior_w_mean_sign": r2(100.0 * pos / tot) if tot else None}


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
            "median_spread_usd_per_jpy": r1(median(spreads)),
            "median_spread_ticks": r1(median(spreads) / MIN_TICK),
            "q05": r1(pct(spreads, 0.05)), "q95": r1(pct(spreads, 0.95)),
            "share_near_below_far_pct": r2(100.0 * sum(1 for s in spreads if s < 0) / len(spreads)),
            "note": "near minus far in USD/JPY quote; settlement-derived deep bars included; curve description only",
        })
    return out


# ---------------------------------------------------------------- intervention days
INTERVENTION_DAYS = [
    ("2026-04-30", "MOF yen-buying JPY 6,278.7bn (primary mof.go.jp)"),
    ("2026-05-01", "day after Apr-30 operation"),
    ("2026-05-04", "MOF yen-buying JPY 780.2bn (primary)"),
    ("2026-05-06", "MOF yen-buying JPY 4,675.9bn (primary)"),
    ("2026-05-07", "day after May-06 operation"),
    ("2026-07-30", "start of record intervention window (press-cited MOF data; Q3 page not yet out)"),
    ("2026-07-31", "BoJ MPM decision day (Jul 30-31)"),
]


def intervention_day_rows(contracts, chain_map):
    rows = []
    for date, why in INTERVENTION_DAYS:
        ls = chain_map.get(date)
        row = {"date": date, "event": why, "held_contract": ls}
        if ls:
            c = contracts[ls]
            b = c["bars"].get(date)
            idx = c["ordered_dates"].index(date) if date in c["bars"] else None
            if b is not None and idx is not None and idx > 0:
                prev = c["bars"][c["ordered_dates"][idx - 1]]["c"]
                row.update({
                    "close": b["c"], "prev_close": prev,
                    "log_ret": r1(math.log(b["c"] / prev)),
                    "ret_pct": r2(100 * (b["c"] / prev - 1)),
                    "volume": b["v"],
                })
        rows.append(row)
    return rows


# ---------------------------------------------------------------- intraday
def hourly_stats(per_contract):
    rows, all_bars = [], []
    for ls, c in sorted(per_contract.items(), key=lambda kv: (kv[1]["first"] or "")):
        rows.append({"localSymbol": ls, "n_bars": c["n"],
                     "first": c["first"], "last": c["last"]})
        all_bars.extend((ls, b) for b in c["bars"])
    byhour = {}
    for ls, b in all_bars:
        hhmm = b["t"][11:16]
        key = hhmm if hhmm in ("08:30",) else hhmm[:2]
        byhour.setdefault(key, []).append(b)
    prof = {}
    for k, bs in sorted(byhour.items()):
        vols = [b["v"] for b in bs if b["v"] and b["v"] > 0]
        rngs = [(b["h"] - b["l"]) / b["c"] * 100.0 for b in bs if b["c"]]
        prof[k] = {
            "n_bars": len(bs),
            "sum_volume": sum(b["v"] for b in bs),
            "median_volume": median(vols) if vols else 0,
            "volume_share_pct": None,
            "median_range_pct": r2(median(rngs)) if rngs else None,
        }
    tot = sum(p["sum_volume"] for p in prof.values())
    for p in prof.values():
        p["volume_share_pct"] = r2(100.0 * p["sum_volume"] / tot) if tot else None
    return {
        "coverage_per_contract": rows,
        "by_session_clock_ct": prof,
        "clock_note": "labels are America/Chicago (CT); ET = CT+1 (08:30 CT stub = 09:30 ET RTH open)",
        "total_bars": len(all_bars),
        "distinct_sessions": len({b["t"][:10] for _, b in all_bars}),
        "caveat": "useRTH=True: US RTH window only; CME Globex 17:00 CT prior day -> 08:30 CT "
                  "(Asia 08:00-17:00 JST / London) is NOT in these files",
    }


# ---------------------------------------------------------------- bid/ask
def bidask(bid, ask):
    out = []
    for ls in sorted(bid):
        if ls not in ask:
            continue
        common = sorted(set(bid[ls]) & set(ask[ls]))
        if not common:
            continue
        sp = [ask[ls][t] - bid[ls][t] for t in common]
        row = {
            "localSymbol": ls, "n_days": len(common),
            "first": common[0], "last": common[-1],
            "median_spread_usd": r1(median(sp)),
            "median_spread_ticks": r1(median(sp) / MIN_TICK),
            "p90_spread_usd": r1(pct(sp, 0.9)),
            "min_spread_usd": r1(min(sp)),
            "crossed_days": sum(1 for s in sp if s < 0),
        }
        last20 = sp[-20:]
        row["median_spread_ticks_last20d"] = r1(median(last20) / MIN_TICK) if last20 else None
        out.append(row)
    return out


# ---------------------------------------------------------------- main
def main():
    global panel_cache
    contracts = load_contracts()
    bid, ask = load_side("BID"), load_side("ASK")
    hourly = load_hourly()

    pan = panel(contracts)
    panel_cache = pan
    rolls, serial_gaps = roll_analysis(contracts)
    mig = migration(contracts, rolls)
    u6skip = u6_to_z6_skip(contracts)
    sercov = serial_coverage(contracts)
    # crossover may precede the U6 window start; search whole U6 life
    if u6skip["first_session_z6_vol_gt_u6"] is None:
        allrows = []
        for t in contracts["6JU6"]["ordered_dates"]:
            vu = contracts["6JU6"]["bars"][t]["v"]
            vz = contracts["6JZ6"]["bars"].get(t, {}).get("v") or 0
            if vu > 0 and vz > vu:
                allrows.append(t)
        u6skip["first_session_z6_vol_gt_u6_full_life"] = allrows[0] if allrows else None
        u6skip["n_sessions_z6_gt_u6_full_life"] = len(allrows)

    chain = build_quarterly_chain(contracts)
    rets, roll_dates_used = chain_returns(chain)
    chain_map = {t: ls for t, ls, _, _ in chain}

    real_start = None
    for i, (t, ls, c, v) in enumerate(chain):
        if all(x[3] > 0 for x in chain[i:]):
            real_start = t
            break
    real_rets = [x for x in rets if real_start and x["date"] >= real_start]

    full_desc = describe_returns(rets, "quarterly_chain_full_depth_2020-2026_settlement_derived_reference")
    real_desc = describe_returns(real_rets, "quarterly_chain_real_volume_subera")

    vol21 = rolling_vol(real_rets, 21)
    vol63 = rolling_vol(real_rets, 63)

    refs = {}
    for ls in ("6JZ5", "6JZ6"):
        cl = [(t, contracts[ls]["bars"][t]["c"]) for t in contracts[ls]["ordered_dates"]]
        rr = [{"date": t1, "sym": ls, "r": math.log(c1 / c0)}
              for (t0, c0), (t1, c1) in zip(cl, cl[1:])]
        refs[ls] = describe_returns(rr, f"{ls}_single_contract_full_life")

    ts = term_structure(contracts, [
        ("6JZ5", "6JH6"), ("6JH6", "6JM6"), ("6JM6", "6JU6"),
        ("6JU6", "6JZ6"), ("6JZ6", "6JH7"),
        ("6JZ5", "6JZ6"), ("6JZ6", "6JZ7"), ("6JM6", "6JZ6"),
        ("6JV6", "6JX6"), ("6JV6", "6JZ6"), ("6JX6", "6JZ6"),
    ])

    closes_all = [b["c"] for c in contracts.values() for b in c["bars"].values()]
    tick_dev = max(abs(round(c / MIN_TICK) * MIN_TICK - c) for c in closes_all)

    result = {
        "meta": {
            "script": os.path.abspath(__file__),
            "run_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "raw_root": RAW,
            "input_files": {"daily_trades_6Y": len(contracts),
                            "bid_1Y": len(bid), "ask_1Y": len(ask),
                            "hourly_30D": len(hourly)},
            "constraints": "descriptive only; no PnL/event-study/sweeps; strict past windows",
            "conventions": {
                "roll_rule": "data-lane declared rule; NOT executable for 2025-09..2026-08 rolls "
                             "(8 serial months missing from raw) and routes into near-dead serials "
                             "from 2026-08-31; main stats use quarterly(HMUZ)->quarterly liquid chain",
                "returns": "within-contract daily log returns; roll-date return on old contract",
                "tick": {"multiplier_jpy": MULT, "minTick_usd_per_jpy": MIN_TICK,
                         "tick_usd": TICK_USD},
            },
        },
        "quote_convention_check": {
            "min_close_usd_per_jpy": r1(min(closes_all)),
            "max_close_usd_per_jpy": r1(max(closes_all)),
            "implied_usdjpy_range": [r2(1 / max(closes_all)), r2(1 / min(closes_all))],
            "max_abs_dev_from_mintick_grid": r1(tick_dev),
            "expected": "USD per JPY (~0.0061-0.0102 for USDJPY 98-164); NOT the ~150 quote (USDJPY direction)",
            "verdict": "PASS-scale-consistent" if 0.001 < min(closes_all) and max(closes_all) < 1.0 else "CHECK",
        },
        "panel": pan,
        "serial_coverage": sercov,
        "roll_analysis": {
            "declared_rule": "hold until last session before day-1 of delivery month; roll to next listed at that close",
            "rolls": rolls,
            "serial_gaps": serial_gaps,
            "u6_to_z6_liquidity_skip": u6skip,
            "note": "gaps are raw adjacent-closes, descriptive only, NOT a tradable cost model",
        },
        "volume_migration": mig,
        "quarterly_chain": {
            "construction": "smallest-delivery HMUZ contract with delivery month > date month; "
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
            "rolling_vol_63d": {"latest_ann_pct": r2(100 * vol63[-1]["vol"] * math.sqrt(252)) if vol63 else None},
            "large_move_days_past126q95": past_threshold_large_moves(real_rets, 126, 0.95),
            "seasonal": seasonal(real_rets) if real_rets else None,
            "trend_share_50d_realera": trend_share(real_rets, 50) if real_rets else None,
            "top10_abs_moves_realera": sorted(
                [{"date": x["date"], "r": r1(x["r"])} for x in real_rets],
                key=lambda z: -abs(z["r"]))[:10],
        },
        "long_horizon_single_contract_refs": refs,
        "term_structure_pairs": ts,
        "intervention_day_description": intervention_day_rows(contracts, chain_map),
        "intraday_hourly_rth_only": hourly_stats(hourly),
        "bid_ask_daily_spreads": {
            "note": "BID/ASK daily closes NOT synchronous; descriptive only, not executable spread",
            "contracts": bidask(bid, ask),
        },
    }

    with open(OUT, "w") as f:
        json.dump(result, f, indent=1)
    print("wrote", OUT)
    print("contracts:", len(contracts))
    print("chain sessions:", len(chain), "real-era start:", real_start)
    print("serial gaps:", len(serial_gaps))
    print("first z6>u6:", u6skip["first_session_z6_vol_gt_u6"])
    print("real-era ann vol:", real_desc.get("ann_vol_pct"))


if __name__ == "__main__":
    main()
