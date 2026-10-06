#!/usr/bin/env python3
"""NG (Henry Hub natural gas futures, NYMEX) descriptive statistics.

Lane: SYMBOL-DOSSIER-NG of FUTURES-BEHAVIOR-10SYMS-PREP-20261002.
PREP ONLY: descriptive statistics; no PnL, no return-based event studies, no
parameter sweeps, no signals selected by performance. No ex-post label is ever
used as an input to a rule; all summaries are full-sample distributions or
strictly trailing/rolling windows.

Data (legal, read-only): ~/.my-quantitative-data/futures-10syms-v1/raw/
snapshot of FUTURES-DATA-10SYMS-V1 fetched 2026-10-02 via IB TWS API readonly
client. Per NG contract: TRADES daily 6Y (early life = settlement-derived
close-only v=0 bars, thin v>0 prints possible in deferred life), TRADES H1 30D
and M1 2D near each contract's end (IB useRTH=True -> 09:30-17:00 US/Eastern
only), BID/ASK daily 1Y. No open interest field anywhere in raw -> OI: NOT_RUN.

STRUCTURAL CAVEAT governed by the expired-secdef wall (~12 months): the
snapshot's deep daily history (2019-2024) belongs to contracts that were then
1-6 years DEFERRED (deliveries 2025-10..2028-02). The contemporaneous fronts of
2019-2024 are NOT in the snapshot. Therefore:
 - "nearest-listed chain" 2019-2024 = forward-strip/curve proxy, descriptive of
   the curve only, NOT a tradable front reconstruction;
 - the true front-month chain exists only from ~2025-08 (delivery 2025-10
   onward), consistent with FUTURES-DATA-10SYMS-V1 FINAL_REPORT (~14 months).

Outputs NG_descriptives.json next to this script.
Run: /Users/hoangminhlong/my-quantitative/.venv/bin/python NG_descriptives.py
"""
import json
import math
import re
import statistics as st
from collections import defaultdict
from datetime import date
from pathlib import Path

RAW = Path.home() / ".my-quantitative-data/futures-10syms-v1/raw"
OUT = Path(__file__).resolve().parent / "NG_descriptives.json"
SNAPSHOT_END = "2026-10-01"  # last daily bar date in snapshot

MONTH_CODE = {c: i + 1 for i, c in enumerate("FGHJKMNQUVXZ")}  # F=Jan..Z=Dec


def delivery_month(local):
    m = re.match(r"^NG([FGHJKMNQUVXZ])(\d{2})$", local)
    y, mth = int(m.group(2)), MONTH_CODE[m.group(1)]
    return (2000 + y, mth)


def dmk(dm):
    return dm[0] * 12 + dm[1]  # month index


def pct(vals, q):
    if not vals:
        return None
    s = sorted(vals)
    i = min(len(s) - 1, max(0, int(round(q * (len(s) - 1)))))
    return s[i]


def load():
    daily, h1, m1, bid, ask = {}, {}, {}, {}, {}
    for p in sorted(RAW.glob("NG_*.json")):
        d = json.loads(p.read_text())
        meta = dict(localSymbol=d["localSymbol"], conId=d["conId"])
        if "front_" in p.name or "nearest_expired" in p.name or "next_" in p.name:
            continue  # 3D probe files are subsets
        if d["whatUse"] == "TRADES" and d["barSize"] == "1 day" and d["durationStr"] == "6 Y":
            daily[d["conId"]] = (meta, d["bars"])
        elif d["whatUse"] == "TRADES" and d["barSize"] == "1 hour" and d["durationStr"] == "30 D":
            h1[d["conId"]] = (meta, d["bars"])
        elif d["whatUse"] == "TRADES" and d["barSize"] == "1 min" and d["durationStr"] == "2 D":
            m1[d["conId"]] = (meta, d["bars"])
        elif d["whatUse"] == "BID" and d["barSize"] == "1 day" and d["durationStr"] == "1 Y":
            bid[d["conId"]] = {b["t"]: b for b in d["bars"]}
        elif d["whatUse"] == "ASK" and d["barSize"] == "1 day" and d["durationStr"] == "1 Y":
            ask[d["conId"]] = {b["t"]: b for b in d["bars"]}
    return daily, h1, m1, bid, ask


def main():
    daily, h1, m1, bid, ask = load()
    R = {"_meta": {
        "symbol": "NG", "venue": "NYMEX", "exchange_tz": "US/Eastern",
        "raw_root": str(RAW), "snapshot_last_daily_bar": SNAPSHOT_END,
        "script": Path(__file__).name,
        "note": "descriptive only; no PnL/event-study/sweeps; OI absent in raw (NOT_RUN)",
        "structural_caveat": "deep daily history = then-deferred contracts (deliveries "
                             "2025-10..2028-02); contemporaneous 2019-2024 fronts absent "
                             "(expired-secdef wall); see docstring",
    }}

    # ---------------- 1. Contract panel (daily) ----------------
    panel = {}
    for cid, (meta, bars) in daily.items():
        dm = delivery_month(meta["localSymbol"])
        real = [b for b in bars if b["v"] > 0]
        flat = sum(1 for b in bars if b["v"] == 0 and b["o"] == b["h"] == b["l"] == b["c"])
        alive = bars[-1]["t"] >= SNAPSHOT_END and dmk(dm) > dmk((2026, 10))
        panel[cid] = {
            "localSymbol": meta["localSymbol"], "delivery_ym": f"{dm[0]}-{dm[1]:02d}",
            "delivery_midx": dmk(dm),
            "alive_at_snapshot": alive,
            "last_bar": bars[-1]["t"], "n_bars": len(bars), "first_bar": bars[0]["t"],
            "n_settlement_only_v0": flat, "n_real_vol_days": len(real),
            "first_real_vol_date": real[0]["t"] if real else None,
            "last_real_vol_date": real[-1]["t"] if real else None,
            "total_volume": int(sum(b["v"] for b in bars)),
        }
    contracts = sorted(panel.values(), key=lambda x: x["delivery_midx"])
    R["contracts"] = contracts
    midxs = [c["delivery_midx"] for c in contracts]
    R["universe"] = {
        "n_contracts": len(contracts),
        "delivery_months": [contracts[0]["delivery_ym"], contracts[-1]["delivery_ym"]],
        "contiguous_monthly": all(midxs[i + 1] - midxs[i] == 1 for i in range(len(midxs) - 1)),
        "n_alive_at_snapshot": sum(c["alive_at_snapshot"] for c in contracts),
        "note": "29 monthly contracts 2025-10..2028-02 incl. gap-filled NGV26 (2026-10)",
    }

    px = {cid: {b["t"]: b for b in bars} for cid, (meta, bars) in daily.items()}
    all_days = sorted({t for cid in px for t in px[cid]})

    def front_candidates(t):
        y = int(t[:4])
        mth = int(t[5:7])
        ymidx = y * 12 + mth
        return sorted((c for c in panel if panel[c]["delivery_midx"] > ymidx),
                      key=lambda c: panel[c]["delivery_midx"])

    def chain_pick(t):
        """nearest-listed selection: smallest delivery month > current calendar
        month that actually has a bar on t (fallback to next listed)."""
        for c in front_candidates(t):
            if t in px[c]:
                return c
        return None

    # ---------------- 2. Chain series + front-true era ----------------
    front_series = []  # (date, cid, close, v, has_range)
    for t in all_days:
        c = chain_pick(t)
        if c is not None:
            b = px[c][t]
            front_series.append((t, c, b["c"], b["v"], b["h"] > b["l"]))

    # (a) daily-prints start: first date from which >=95% of chain days have v>0 AND range
    prints_start = None
    for i, (t, c, cl, v, hr) in enumerate(front_series):
        tail = front_series[i:]
        ok = sum(1 for row in tail if row[3] > 0 and row[4]) / len(tail)
        if ok >= 0.95:
            prints_start = t
            break

    # (b) front-true start: first date from which the chain-selected contract's
    # delivery month is within 2 calendar months of the current month onward
    # (before that, the nearest listed contract was a far-deferred strip leg
    # because the contemporaneous front is behind the expired-secdef wall).
    front_true_start = None
    for i, (t, c, cl, v, hr) in enumerate(front_series):
        ymidx = int(t[:4]) * 12 + int(t[5:7])
        if panel[c]["delivery_midx"] - ymidx <= 2:
            tail_ok = all(
                panel[row[1]]["delivery_midx"] - (int(row[0][:4]) * 12 + int(row[0][5:7])) <= 2
                for row in front_series[i:])
            if tail_ok:
                front_true_start = t
                break
    tv_start = front_true_start  # era splits below use the front-true definition
    R["chain_definition"] = {
        "selection": "nearest listed delivery month > calendar month (dm-sorted), "
                     "fallback to next listed with a bar that day",
        "daily_prints_start_95pct_rule": prints_start,
        "front_true_start_delivery_within_2m": front_true_start,
        "n_chain_days": len(front_series),
        "front_close_at_snapshot": front_series[-1][2],
        "front_at_snapshot": panel[front_series[-1][1]]["localSymbol"],
        "era_note": "daily_prints_start marks when the nearest-LISTED (then deferred) "
                    "chain began printing daily; the contemporaneous FRONT chain exists "
                    "only from front_true_start (~2025-08), deliveries 2025-10 onward",
    }

    def summarize(rets):
        if not rets:
            return None
        v = [r for _, r in rets]
        return {
            "n": len(v),
            "mean_daily_logret": round(st.mean(v), 6),
            "std_daily_logret": round(st.stdev(v), 6),
            "ann_vol_if_iid": round(st.stdev(v) * math.sqrt(252), 4),
            "pct_abs_gt_3pct": round(sum(1 for x in v if abs(x) > .03) / len(v), 4),
            "pct_abs_gt_5pct": round(sum(1 for x in v if abs(x) > .05) / len(v), 4),
            "max_abs": round(max(abs(x) for x in v), 4),
        }

    rets = []
    for i in range(1, len(front_series)):
        t0, c0, p0, _, _ = front_series[i - 1]
        t1, c1, p1, _, _ = front_series[i]
        if c0 == c1 and p0 > 0 and p1 > 0:  # returns within same contract only
            rets.append((t1, math.log(p1 / p0)))
    R["front_returns"] = {
        "window": [rets[0][0], rets[-1][0]],
        "roll_day_returns_skipped": True,
        "nearest_listed_chain_full": summarize(rets),
        "deferred_era_pre_tvstart_curve_proxy": summarize(
            [r for r in rets if r[0] < tv_start]) if tv_start else None,
        "front_true_volume_era": summarize([r for r in rets if r[0] >= tv_start]) if tv_start else None,
        "caveat": "pre tv_start the chain is the then-deferred nearest-listed contract "
                  "(settlement/thin prints) -> curve-level description only, NOT a "
                  "tradable front; front-month returns exist only in the true-volume era",
    }
    byy = defaultdict(list)
    for t, r in rets:
        byy[t[:4]].append(r)
    R["front_returns"]["by_year_nearest_listed_chain"] = {
        y: summarize([(None, x) for x in v]) for y, v in sorted(byy.items())}

    # monthly |ret| within true-volume era only (single seasonal cycle -> descriptive)
    era = [r for r in rets if r[0] >= tv_start] if tv_start else []
    bym = defaultdict(list)
    for t, r in era:
        bym[int(t[5:7])].append(abs(r))
    R["front_returns"]["true_volume_era_mean_absret_by_calendar_month_x100"] = {
        f"{m:02d}": round(st.mean(v) * 100, 3) for m, v in sorted(bym.items())}
    if era:
        ws = [abs(r) for t, r in era if int(t[5:7]) in (11, 12, 1, 2, 3)]
        ss = [abs(r) for t, r in era if int(t[5:7]) in (4, 5, 6, 7, 8, 9, 10)]
        R["front_returns"]["true_volume_era_absret_winter_vs_summer_x100"] = {
            "winter_nov_mar": round(st.mean(ws) * 100, 3),
            "summer_apr_oct": round(st.mean(ss) * 100, 3)}
        # lag-1 autocorrelation (descriptive trend vs mean-reversion fingerprint)
        v = [r for _, r in era]
        mu = st.mean(v)
        num = sum((v[i] - mu) * (v[i + 1] - mu) for i in range(len(v) - 1))
        den = sum((x - mu) ** 2 for x in v)
        R["front_returns"]["true_volume_era_lag1_autocorr"] = round(num / den, 4)
        R["front_returns"]["nearest_listed_chain_lag1_autocorr"] = round(
            (lambda vv: sum((vv[i] - st.mean(vv)) * (vv[i + 1] - st.mean(vv))
                            for i in range(len(vv) - 1)) /
            sum((x - st.mean(vv)) ** 2 for x in vv))([r for _, r in rets]), 4)

    # trailing 20d vol (strictly trailing) on nearest-listed chain, split at tv_start
    rl = [(rets[i][0], rets[i - 20:i]) for i in range(20, len(rets))]
    prof = [(t, math.sqrt(sum(x * x for _, x in w) / 20) * math.sqrt(252)) for t, w in rl]
    R["front_returns"]["trailing20d_annvol_nearest_listed_chain"] = {
        "median": round(st.median(p[1] for p in prof), 3),
        "p10": round(pct([p[1] for p in prof], .1), 3),
        "p90": round(pct([p[1] for p in prof], .9), 3),
        "max": round(max(p[1] for p in prof), 3),
        "last": round(prof[-1][1], 3),
        "last_date": prof[-1][0],
        "true_volume_era_median": round(st.median(
            [p[1] for p in prof if p[0] >= tv_start]), 3) if tv_start else None,
    }

    closes = [c for _, _, c, _, _ in front_series]
    R["front_price_levels_nearest_listed_chain"] = {
        "window": [front_series[0][0], front_series[-1][0]],
        "min": min(closes), "max": max(closes), "median": round(st.median(closes), 3),
        "first": front_series[0][2], "last_at_snapshot": front_series[-1][2],
    }
    # true-volume era levels (front)
    era_lv = [c for t, _, c, _, _ in front_series if t >= tv_start] if tv_start else []
    if era_lv:
        R["front_price_levels_true_volume_era"] = {
            "window": [tv_start, front_series[-1][0]],
            "min": min(era_lv), "max": max(era_lv), "median": round(st.median(era_lv), 3),
            "last_at_snapshot": front_series[-1][2]}

    # front volume (true era) + aggregate activity
    if tv_start:
        fv = [v for t, _, _, v, _ in front_series if t >= tv_start]
        R["front_volume_true_volume_era"] = {
            "median_daily_lots": int(st.median(fv)),
            "p10": int(pct(fv, .1)), "p90": int(pct(fv, .9)),
        }
    agg = []
    for t in all_days:
        if tv_start and t >= tv_start:
            agg.append(sum(px[c][t]["v"] for c in px if t in px[c]))
    if agg:
        R["aggregate_daily_volume_all_contracts_true_volume_era"] = {
            "median_lots": int(st.median(agg)),
            "p10": int(pct(agg, .1)), "p90": int(pct(agg, .9)),
        }

    # ---------------- 3. Roll table (matured adjacent pairs) ----------------
    # matured = contract whose life ended before snapshot end.
    rolls = []
    for cid, info in panel.items():
        if info["alive_at_snapshot"] or info["last_real_vol_date"] is None:
            continue
        nxt = [c for c in panel if panel[c]["delivery_midx"] == info["delivery_midx"] + 1]
        if not nxt:
            continue
        nc = nxt[0]
        # volume crossover within final 90 days of m's real-volume life
        end_d = date.fromisoformat(info["last_real_vol_date"])
        start_d = date.fromordinal(end_d.toordinal() - 90)
        cur, nn = px[cid], px[nc]
        common = sorted(t for t in set(cur) & set(nn)
                        if date.fromisoformat(t) >= start_d)
        cross, cross_share = None, None
        for t in common:
            a, b = cur[t]["v"], nn[t]["v"]
            if a > 0 and b > 0 and b > a:
                cross = t
                cross_share = round(a / (a + b), 3)
                break
        # roll date = first chain day holding nc after m's last bar
        roll_date = None
        lastm = info["last_bar"]
        for t, c, cl, v, hr in front_series:
            if t > lastm:
                roll_date = t if c == nc else None
                if c == nc:
                    break
        old_final = cur[lastm]["c"] if lastm in cur else None
        new_close = nn[roll_date]["c"] if roll_date and roll_date in nn else None
        # same-day calendar spread at outgoing final session (both legs quoted)
        sameday = (nn[lastm]["c"] - cur[lastm]["c"]) if (lastm in nn and lastm in cur) else None
        rolls.append({
            "from": info["localSymbol"], "to": panel[nc]["localSymbol"],
            "delivery_ym": info["delivery_ym"],
            "m_last_real_vol": info["last_real_vol_date"],
            "m_final_bar": lastm,
            "roll_date_chain": roll_date,
            "vol_crossover_date": cross,
            "front_vol_share_at_crossover": cross_share,
            "days_crossover_before_final": (end_d - date.fromisoformat(cross)).days if cross else None,
            "crossover_at_window_cap_90d": (cross is not None and
                                            (end_d - date.fromisoformat(cross)).days >= 89),
            "same_day_spread_at_final_usd_mmbtu": round(sameday, 4) if sameday is not None else None,
            "gap_new_close_minus_m_final_close_usd_mmbtu": round(new_close - old_final, 4)
            if (new_close is not None and old_final is not None) else None,
            "gap_usd_per_contract": round((new_close - old_final) * 10000, 2)
            if (new_close is not None and old_final is not None) else None,
        })
    rolls.sort(key=lambda r: r["delivery_ym"])
    R["roll_table_matured_pairs"] = rolls
    gv = [r["gap_new_close_minus_m_final_close_usd_mmbtu"] for r in rolls
          if r["gap_new_close_minus_m_final_close_usd_mmbtu"] is not None]
    cv = [r["days_crossover_before_final"] for r in rolls
          if r["days_crossover_before_final"] is not None]
    R["roll_summary"] = {
        "n_matured_pairs": len(rolls),
        "same_day_spread_def": "next close minus outgoing close on the outgoing final "
                               "session (pure calendar-spread component at roll)",
        "gap_def": "next-contract close on first chain day after outgoing final bar "
                   "minus outgoing final close (stale carry of outgoing close; "
                   "conflates calendar spread + inter-session move; descriptive only, "
                   "NOT a measured executable roll cost)",
        "same_day_spread_usd_mmbtu": None,  # filled below
        "gap_usd_mmbtu": {"median": round(st.median(gv), 4) if gv else None,
                          "min": round(min(gv), 4) if gv else None,
                          "max": round(max(gv), 4) if gv else None,
                          "share_negative": round(sum(1 for x in gv if x < 0) / len(gv), 3) if gv else None},
        "days_volume_crossover_before_outgoing_final": {
            "median": st.median(cv) if cv else None,
            "min": min(cv) if cv else None, "max": max(cv) if cv else None,
            "n_pairs_no_crossover_in_90d": sum(1 for r in rolls if r["vol_crossover_date"] is None),
            "note": "search window capped at 90 days before outgoing final; values >=89 "
                    "mean next contract already dominated at window start"},
        "declared_rule_note": "data-lane baseline rule 'hold to last session before "
                              "day-1 of expiry(delivery) month' is INFEASIBLE for NG as written: "
                              "front's final trade is the 3rd-last business day of the PRIOR month, "
                              "so the binding constraint is the contract's own last trade; "
                              "calendar rule as implemented rolls at the outgoing final bar",
    }
    sd = [r["same_day_spread_at_final_usd_mmbtu"] for r in rolls
          if r["same_day_spread_at_final_usd_mmbtu"] is not None]
    R["roll_summary"]["same_day_spread_usd_mmbtu"] = {
        "median": round(st.median(sd), 4) if sd else None,
        "min": round(min(sd), 4) if sd else None,
        "max": round(max(sd), 4) if sd else None,
        "share_negative": round(sum(1 for x in sd if x < 0) / len(sd), 3) if sd else None,
    }

    # ---------------- 4. Term structure m1 - m2 ----------------
    spreads = []
    for t in all_days:
        cand = [c for c in front_candidates(t) if t in px[c]][:2]
        if len(cand) < 2:
            continue
        a, b = px[cand[0]][t]["c"], px[cand[1]][t]["c"]
        if a > 0 and b > 0:
            spreads.append((t, a - b))
    sv = [s for _, s in spreads]

    def sp_block(rows):
        v = [s for _, s in rows]
        if not v:
            return None
        return {"n": len(v), "median_usd_mmbtu": round(st.median(v), 4),
                "p10": round(pct(v, .1), 4), "p90": round(pct(v, .9), 4),
                "share_negative_backwardation": round(sum(1 for x in v if x < 0) / len(v), 4)}
    R["term_structure_m1_minus_m2"] = {
        "window": [spreads[0][0], spreads[-1][0]],
        "nearest_listed_chain_full": sp_block(spreads),
        "deferred_era_curve_proxy": sp_block([r for r in spreads if r[0] < tv_start]) if tv_start else None,
        "true_volume_era": sp_block([r for r in spreads if r[0] >= tv_start]) if tv_start else None,
        "caveat": "pre tv_start legs are then-deferred nearest-listed contracts "
                  "(forward-strip spread), not contemporaneous front/next",
    }
    bym_sp = defaultdict(list)
    for t, s in spreads:
        if t >= (tv_start or "9999"):
            bym_sp[int(t[5:7])].append(s)
    R["term_structure_m1_minus_m2"]["true_volume_era_median_by_month"] = {
        f"{m:02d}": round(st.median(v), 4) for m, v in sorted(bym_sp.items())}

    # ---------------- 5. Intraday RTH (09:30-17:00 ET) ----------------
    h1cov, hour_vol, hour_ret, h1_days = [], defaultdict(int), defaultdict(list), set()
    wd10, wdall = defaultdict(int), defaultdict(int)
    for cid, (meta, bars) in h1.items():
        if not bars:
            continue
        h1cov.append({"localSymbol": meta["localSymbol"], "n": len(bars),
                      "first": bars[0]["t"], "last": bars[-1]["t"],
                      "v0_bars": sum(1 for b in bars if b["v"] == 0)})
        byday = defaultdict(list)
        for b in bars:
            hh = int(b["t"][11:13])
            hour_vol[hh] += b["v"]
            byday[b["t"][:10]].append((b["t"], b))
            h1_days.add(b["t"][:10])
            d = date.fromisoformat(b["t"][:10])
            wdall[d.weekday()] += b["v"]
            if hh == 10:
                wd10[d.weekday()] += b["v"]
        for d, bl in byday.items():
            bl.sort()
            for (t0, b0), (t1, b1) in zip(bl, bl[1:]):
                if b0["c"] > 0 and b1["c"] > 0:
                    hour_ret[int(t1[11:13])].append(abs(math.log(b1["c"] / b0["c"])))
    tot_v = sum(hour_vol.values())
    R["intraday_h1_rth"] = {
        "coverage_note": "H1 30D per contract ending at its final session (or snapshot "
                         "for alive); pooled coverage is the union; 2025-07-21..2026-10-01",
        "n_files_with_bars": len(h1cov),
        "n_days_pooled": len(h1_days),
        "hour_et_volume_share": {f"{h:02d}": round(hour_vol[h] / tot_v, 4) for h in sorted(hour_vol)},
        "hour_et_mean_abslogret_x100": {f"{h:02d}": round(st.mean(v) * 100, 4)
                                        for h, v in sorted(hour_ret.items())},
        "hour_bucket_def": "09=09:30-10:00 (half hour), 10..15=hour starting HH:30, "
                           "16=16:00-17:00 final hour; return attributed to later bar's hour",
        "weekday_volume_share_of_10am_bucket": {
            ["Mon", "Tue", "Wed", "Thu", "Fri"][k]: round(wd10[k] / wdall[k], 4)
            for k in sorted(wdall) if wdall[k] > 0},
        "note": "IB useRTH=True capture: 09:30-17:00 ET only; full Globex session "
                "(S1 tradingHours 18:00 prev-day to 17:00 ET) NOT captured; the "
                "10:00-11:00 ET bucket contains the EIA storage 10:30 release - "
                "time-of-day descriptive profile only, NOT an event study",
    }
    R["intraday_h1_rth"]["coverage_by_contract"] = sorted(h1cov, key=lambda x: x["first"])

    m1cov, first30, daytot, last30 = [], 0, 0, 0
    for cid, (meta, bars) in m1.items():
        if not bars:
            continue
        m1cov.append({"localSymbol": meta["localSymbol"], "n": len(bars),
                      "first": bars[0]["t"], "last": bars[-1]["t"]})
        byday = defaultdict(list)
        for b in bars:
            byday[b["t"][:10]].append(b)
        for d, bl in byday.items():
            daytot += sum(b["v"] for b in bl)
            first30 += sum(b["v"] for b in bl if b["t"][11:16] < "10:00")
            last30 += sum(b["v"] for b in bl if b["t"][11:16] >= "16:30")
    R["intraday_m1_rth"] = {
        "n_files_with_bars": len(m1cov),
        "first30min_volume_share": round(first30 / daytot, 4) if daytot else None,
        "last30min_volume_share": round(last30 / daytot, 4) if daytot else None,
        "coverage_window": [min(c["first"] for c in m1cov), max(c["last"] for c in m1cov)],
        "note": "M1 2-day files per contract near final session, RTH only; descriptive",
    }

    # ---------------- 6. BID/ASK 1Y front spread proxy ----------------
    spread_rows = []
    for t in all_days:
        for c in front_candidates(t):
            if panel[c]["delivery_midx"] - (int(t[:4]) * 12 + int(t[5:7])) > 2:
                break  # only front-true era legs (delivery within 2 months)
            if c in bid and c in ask and t in bid[c] and t in ask[c]:
                b, a = bid[c][t]["c"], ask[c][t]["c"]
                if a >= b > 0:
                    spread_rows.append((t, panel[c]["localSymbol"], a - b))
                    break
    sp = [s for _, _, s in spread_rows]
    pos = [s for s in sp if s > 0]
    # S6 cross-check: last 20 snapshot days of the current front NGX26
    x26 = [(t, s) for t, ls, s in spread_rows if ls == "NGX26"][-20:]
    x26v = [s for _, s in x26]
    R["bidask_1y_front_proxy"] = {
        "n_days": len(sp),
        "window": [spread_rows[0][0], spread_rows[-1][0]] if spread_rows else None,
        "share_zero_spread_days": round(sum(1 for s in sp if s == 0) / len(sp), 3) if sp else None,
        "median_usd_incl_zero": round(st.median(sp), 3) if sp else None,
        "median_usd_positive_only": round(st.median(pos), 3) if pos else None,
        "p90_usd": round(pct(sp, .9), 3) if sp else None,
        "max_usd": round(max(sp), 3) if sp else None,
        "cross_check_NGX26_last20d_median_usd": round(st.median(x26v), 3) if x26v else None,
        "cross_check_vs_S6_FRONT_SPREADS": "S6 (data lane): median 2 ticks=$20, p90 $30 "
                                           "(front NGX26, 20 days, close-to-close proxy)",
        "note": "close-bid vs close-ask of nearest-listed front (delivery<=2m ahead) "
                "with both quotes; daily closes, NOT synchronous -> non-executable "
                "descriptive proxy; zero-spread days = stale/marked quotes",
    }

    OUT.write_text(json.dumps(R, indent=1))
    print("wrote", OUT)
    print(json.dumps({k: R[k] for k in
                      ["universe", "chain_definition", "roll_summary",
                       "front_volume_true_volume_era", "bidask_1y_front_proxy"]}, indent=1))


if __name__ == "__main__":
    main()
